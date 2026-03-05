# 匹配算法设计

> 版本: 2.0.0
> 最后更新: 2026-02-26
> 状态: 已接受
> 相关 ADR: [002-rule-based-matching.md](../adr/002-rule-based-matching.md)

## 概述

匹配模块识别在 Shopee Thailand 和 TikTok Shop Thailand 上架的相同或相关商品。由于同一商品在不同平台上通常有不同的标题、图片和描述，我们使用多信号打分方法来确定匹配置信度。

## 匹配类型

每个候选配对根据综合得分和信号分析被分类为四种匹配类型之一：

| 匹配类型 | 代码 | 描述 | 示例 |
|---------|------|------|-----|
| 完全相同 | `exact_same` | 同商品、同 SKU、同品牌、同规格 | NIVEA 沐浴露 500ml（Shopee）= NIVEA 沐浴露 500ml（TikTok） |
| 系列变体 | `variant_family` | 同产品线，不同规格/变体/香型 | NIVEA 沐浴露 500ml vs NIVEA 沐浴露 200ml |
| 相似 | `similar` | 同品类同品牌，但明显不同的商品 | NIVEA 沐浴露 vs NIVEA 身体乳 |
| 不匹配 | `no_match` | 相似度不足以建立任何关联 | NIVEA 沐浴露 vs 潘婷洗发水 |

### 匹配类型判定规则

综合打分后，通过检查各信号得分细化匹配类型：

```
IF composite_score >= 0.85:
    IF spec_score >= 0.90:  -> exact_same
    ELIF spec_score >= 0.50: -> variant_family
    ELSE:                    -> similar
ELIF composite_score >= 0.65:
    -> 路由到审核队列，附带建议的 match_type
ELSE:
    -> no_match
```

## 候选召回（阻隔策略）

对所有跨平台配对逐一打分是 O(n^2) 且浪费的。我们使用两阶段候选召回策略来缩减比较空间。

### 第一阶段：品牌 + 品类阻隔

仅比较满足以下条件的商品：
- 相同的标准品牌名称（品牌归一化后）
- 相同的子品类（如都是 `shampoo`）

这大幅缩减了比较空间。对每平台每子品类 200 个商品，约 20 个品牌，平均每品牌每平台约 10 个商品，每品牌产生约 100 次比较而非 40,000 次。

### 第二阶段：TF-IDF 文本相似度预过滤

在每个阻隔块内，对 `title + description_snippet` 拼接文本计算 TF-IDF 余弦相似度：

1. 分词：小写化，移除常见泰语/英语停用词，按空白和标点切分。
2. 构建块内局部 TF-IDF 矩阵。
3. 计算每个跨平台配对的余弦相似度。
4. 保留 TF-IDF 余弦相似度 >= 0.20 的配对作为完整打分的候选。

此预过滤通常淘汰 60-70% 明显无关的块内配对（如同品牌的不同产品类型）。

### 边界情况：品牌缺失

当无法提取品牌时（brand_confidence: low 或缺失）：
- 商品被放入每子品类的特殊 `unknown_brand` 阻隔块。
- 所有未知品牌商品相互比较，同时与该子品类中商品数量前 3 的品牌进行比较。
- 这增加了召回率，代价是更多比较，但未知品牌阻隔块通常较小（< 10% 的商品）。

### 第三阶段（可选）：OpenSearch BM25 召回

启用条件：在 `config/default.yaml` 的 `recall.strategies` 中添加 `opensearch`，并启动 OpenSearch 服务。

| 参数 | 默认值 | 描述 |
|-----|-------|-----|
| `host` | `localhost` | OpenSearch 主机 |
| `port` | `9200` | OpenSearch 端口 |
| `index_name` | `sea_matching_items` | 索引名称 |
| `min_score` | `2.0` | 最低 BM25 分数 |
| `top_k` | `50` | 每个查询返回的最大候选数 |

**索引映射**：
- `title`：使用 `product_analyzer`（自定义分词器，支持中英泰混合文本）
- `brand_std`：keyword 类型，精确匹配
- `category`：keyword 类型，精确过滤

**查询策略**：
- Bool 查询：`must` 中的 `multi_match`（title + brand_std）+ `filter` 中的 category 精确匹配
- 品牌字段加权 boost = 5.0
- BM25 分数归一化到 [0, 1] 范围

**优雅降级**：如果 opensearch-py 未安装或 OpenSearch 服务不可用，跳过此策略并记录警告日志。

### 第四阶段（可选）：向量召回（FAISS / Milvus）

启用条件：在 `config/default.yaml` 的 `recall.strategies` 中添加 `vector`，并安装 `sentence-transformers`。

| 参数 | 默认值 | 描述 |
|-----|-------|-----|
| `backend` | `local` | `local`（FAISS）或 `milvus` |
| `model_name` | `paraphrase-multilingual-MiniLM-L12-v2` | 编码模型 |
| `top_k` | `30` | 每个查询返回的最大候选数 |
| `min_similarity` | `0.4` | 最低余弦相似度 |
| `milvus_host` | `localhost` | Milvus 主机（仅 milvus 后端） |
| `milvus_port` | `19530` | Milvus 端口（仅 milvus 后端） |
| `collection_name` | `sea_matching_vectors` | Milvus 集合名（仅 milvus 后端） |

**编码方式**：将 `title + " " + brand_std` 拼接为输入文本，使用多语言 sentence-transformers 模型编码为稠密向量。

**两种后端**：
- **local（FAISS）**：使用 `IndexFlatIP`（内积索引），适用于小规模数据（< 10,000 商品）
- **milvus**：使用 Milvus 2.4 分布式向量数据库，适用于大规模生产场景

**优雅降级**：如果 sentence-transformers/faiss/pymilvus 未安装或服务不可用，跳过此策略并记录警告日志。

### 召回策略组合

`CombinedRecall` 类负责编排所有启用的召回策略，合并去重候选对：

```yaml
# config/default.yaml 召回配置
recall:
  strategies:
    - brand_category      # 品牌+品类阻隔（默认）
    - text_similarity     # TF-IDF 文本相似度（默认）
    # - opensearch        # BM25 召回（可选，需 OpenSearch）
    # - vector            # 向量召回（可选，需 sentence-transformers）
```

每个策略独立运行，结果通过 `(tiktok_id, shopee_id)` 复合键去重合并。如果某策略初始化失败（依赖缺失或服务不可达），`CombinedRecall` 跳过该策略并继续使用其余策略。

## 打分模型

每个候选配对使用四个信号的加权组合进行打分：

### 信号权重

| 信号 | 权重 | 描述 |
|-----|------|-----|
| 品牌得分 | 0.30 | 品牌名称相似度 |
| 规格得分 | 0.25 | 商品规格（尺寸、容量、变体）相似度 |
| 标题得分 | 0.30 | 清洗后标题文本相似度 |
| 价格得分 | 0.15 | 价格接近度 |

### 综合得分公式

```
composite_score = (brand_weight × brand_score)
                + (spec_weight × spec_score)
                + (title_weight × title_score)
                + (price_weight × price_score)
```

所有单项得分归一化到 [0.0, 1.0]。

### 信号：品牌得分（权重 = 0.30）

| 条件 | 得分 |
|-----|------|
| 归一化后精确匹配 | 1.0 |
| 一方品牌是另一方的已知别名 | 1.0 |
| 一方品牌是另一方的子串 | 0.7 |
| 编辑距离 <= 2 | 0.5 |
| 不匹配 | 0.0 |

品牌归一化使用维护的别名字典（如 `{"NIVEA": ["nivea", "Nivea Men", "NIVEA MEN"]}`）加模糊匹配兜底。

### 信号：规格得分（权重 = 0.25）

比较提取的商品规格：

| 属性 | 子权重 | 打分规则 |
|-----|-------|---------|
| 容量/规格 | 0.50 | 精确匹配: 1.0；误差 10% 内: 0.7；误差 25% 内: 0.3；否则: 0.0 |
| 单位 | 0.20 | 相同单位: 1.0；可转换（ml↔L）: 0.8；否则: 0.0 |
| 变体（香型/类型） | 0.30 | 精确匹配: 1.0；模糊匹配（Jaccard >= 0.5）: 0.5；否则: 0.0 |

当某规格属性在一方或双方缺失时，该子权重按比例重分配到其余属性。

### 信号：标题得分（权重 = 0.30）

1. 清洗标题：移除平台特有噪声（表情符号、促销文字如 "SALE"、"HOT"、重复关键词）。
2. 分词：切分为词 token，小写化。
3. 计算 token 集合的 Jaccard 相似度。
4. 计算字符级三元组相似度作为辅助检查。
5. 最终 title_score = 0.7 × jaccard + 0.3 × trigram_similarity。

### 信号：价格得分（权重 = 0.15）

```
price_ratio = min(price_a, price_b) / max(price_a, price_b)

IF price_ratio >= 0.95: price_score = 1.0
ELIF price_ratio >= 0.85: price_score = 0.7
ELIF price_ratio >= 0.70: price_score = 0.4
ELIF price_ratio >= 0.50: price_score = 0.2
ELSE: price_score = 0.0
```

价格得分权重最低，因为同一商品在不同平台上可能因促销、卖家类型（官方店 vs 经销商）和捆绑销售导致价格显著不同。

## 阈值

| 阈值 | 范围 | 动作 |
|-----|------|-----|
| 自动接受 | composite_score >= 0.85 | 自动接受匹配。写入 `match_map_platform`，`status=auto_accepted`。 |
| 需要审核 | 0.65 <= composite_score < 0.85 | 写入 `match_map_platform`，`status=needs_review`，供人工决策。 |
| 自动拒绝 | composite_score < 0.65 | 分类为 `no_match`，不写入 `match_map_platform`。 |

### 阈值调优

阈值存储在版本化配置文件（`matching-engine/config/default.yaml`）中，无需代码变更即可调整。任何阈值变更都会递增 `rule_version`。

推荐调优流程：
1. 从每个阈值区间随机抽取 100 个配对。
2. 由人工标注正确/错误。
3. 计算每个阈值的精确率/召回率。
4. 调整阈值以保持自动接受的精确率 >= 95%。

## 理由结构

每个打分配对都包含一个 `reasons` 对象，解释得分明细。这对可审计性和审核工作流至关重要。

```json
{
  "composite_score": 0.78,
  "match_type_suggestion": "variant_family",
  "signals": {
    "brand": {
      "score": 1.0,
      "weight": 0.30,
      "weighted_contribution": 0.30,
      "detail": "归一化后精确匹配: NIVEA = NIVEA"
    },
    "spec": {
      "score": 0.30,
      "weight": 0.25,
      "weighted_contribution": 0.075,
      "detail": "容量不匹配: 500ml vs 200ml (比率: 0.40)。变体匹配: 'Extra White' = 'Extra White'。"
    },
    "title": {
      "score": 0.72,
      "weight": 0.30,
      "weighted_contribution": 0.216,
      "detail": "Jaccard: 0.65, Trigram: 0.88。清洗后标题: 'nivea extra white body wash 500ml' vs 'nivea extra white body wash 200ml'。"
    },
    "price": {
      "score": 0.70,
      "weight": 0.15,
      "weighted_contribution": 0.105,
      "detail": "价格比率: 0.87 (159 THB vs 183 THB)。"
    }
  },
  "blocking_info": {
    "block_key": "NIVEA__body_wash",
    "tfidf_prescore": 0.72
  }
}
```

## 输出表：`match_map_platform`

所有已接受和待审核的配对写入 DuckDB 的 `match_map_platform` 表。关键字段：

| 字段 | 描述 |
|-----|-----|
| `tiktok_item_id` | TikTok 商品 ID（主键第 1 部分） |
| `shopee_item_id` | Shopee 商品 ID（主键第 2 部分） |
| `match_type` | `exact_same`、`variant_family`、`similar`、`no_match` |
| `confidence` | 综合得分 [0.0, 1.0] |
| `status` | `auto_accepted`、`needs_review`、`overridden` |
| `reasons` | JSON 字符串，包含证据明细 |
| `rule_version` | 匹配配置版本 |
| `run_id` | 流水线运行标识 |

完整 DDL 见 [data-model.md](data-model.md#表-4match_map_platform)。

## 覆盖合并

匹配引擎支持通过 JSON 文件注入人工覆盖。每次匹配运行时：

1. 加载覆盖文件（如存在），包含人工匹配决策。
2. 构建以 `tiktok_id::shopee_id` 复合键为索引的查找表。
3. 对每个匹配对，检查是否存在覆盖：
   - 如果存在：从覆盖中更新 `match_type`，设置 `status = "overridden"`，追加证据注释：`"Human override applied: {comment}"`。
   - 如果不存在：保留算法结果。
4. 返回合并后的匹配候选列表。

覆盖文件通过审核工作流（API `POST /review/{tiktokItemId}/{shopeeItemId}/decision`）管理。

## 审核工作流

### 审核队列

置信度在审核区间（0.65–0.85）的配对写入 `match_map_platform`，`status=needs_review`。它们通过以下方式出现在审核队列中：

- **API**：`GET /api/v1/review-queue`（分页列表）
- **Web 前端**：审核页面，支持并排比较
- **Streamlit**：审核页面，支持 accept/reject/change_type 表单

### 审核操作

| 操作 | API 决策值 | 效果 |
|-----|----------|-----|
| **接受** | `accept` | 更新 `match_map_platform` 中的 `status` 为 `auto_accepted`。记录审计日志。 |
| **拒绝** | `reject` | 更新 `match_map_platform` 中的 `status` 为 `no_match`。记录审计日志。 |
| **变更类型** | `change_type` | 更新 `match_type` 为审核者选择，设置 `status=overridden`。需要 `new_match_type` 字段。 |

### 审核 API

```
POST /api/v1/review/{tiktokItemId}/{shopeeItemId}/decision
Headers: Idempotency-Key: <uuid>
Body: { "decision": "accept", "new_match_type": "variant_family", "comment": "..." }
```

所有决策通过 API 后端的 `AuditService` 记录：谁、何时、旧值、新值、备注。

## 评估报告

每次匹配运行后，引擎在 `reports/report_{run_id}.md` 生成 Markdown 评估报告。报告包含：

1. **运行元数据**：运行 ID、时间戳、配置版本。
2. **分布统计**：
   - 匹配类型分布（exact_same / variant_family / similar / no_match）—— 计数和百分比。
   - 状态分布（auto_accepted / needs_review）—— 计数和百分比。
3. **平均置信度**：所有打分候选的综合得分均值。
4. **样本配对**：随机抽取（默认 50 对）用于人工质量检查，展示：
   - TikTok 和 Shopee 商品 ID 和标题
   - 置信度分数和匹配类型
   - 证据摘要（强证据/弱证据）

报告支持无需数据库查询即可快速评估质量，服务于阈值调优工作流。
