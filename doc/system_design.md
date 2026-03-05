# Top Selling Intelligence（TikTok Shop vs Shopee）— 系统设计（单文件合并版）

> 本文件是“系统需求分析 + 总结 + 设计”的合并版本。
> PDF 原文与抽取文本在：`doc/requirement/`；PDF 要求梳理见：`doc/requiment.md`。

## 1. 背景与目标

### 1.1 业务背景

- 客户：东南亚大型线下零售商（300+ 门店），线下为主，线上数据做参考信号。
- 规模：我方在架 SKU 20k–30k，可采/可扩展 200k+；平台侧商品规模可达千万级（10M+）。
- 目标用户：定价中心 + 品类团队。
- 他们要的不是“数据报表”，而是可执行输出：看板 + 预警 + 机会清单。

### 1.2 题目要求（Case Brief）

题目原始要求偏 Demo 形态（用于展示能力边界）：

1. 对比 TikTok Shop vs Shopee 在同一品类下的热销结构
2. 标准化异构数据（品牌/规格/单位/币种/口径）
3. 跨平台商品对齐（matching）并给出可解释输出
4. 形成行动闭环（覆盖/可采/不建议 + 下一步动作）

### 1.3 交付目标（企业级 MVP，可用）

在满足题目展示点的同时，本项目交付以“企业级可用 MVP”为默认目标：

- 可部署：至少具备 staging（或 prod）部署形态与回滚路径
- 可运维：日志/指标/告警齐备，能定位抓取失败、DQ 失败、审核积压、API 延迟等问题
- 可治理：schema/规则/接口版本化；产物可回放、可审计；DQ 失败不发布或明确 degraded
- 可控安全：OIDC/JWT + RBAC；review/override 全量审计；密钥不落日志

### 1.3 非目标（明确不做什么）

- 不做生产级全量抓取与索引（千万级不要求）。
- 不做“黑盒模型匹配”（必须可解释、可审核）。
- 不追求完美“我方可采”判断（允许规则/流程 stub）。

---

## 2. 需求分析（从 Case Brief 落地成可实现的系统需求）

### 2.1 固定约束

- 品类：1–2 个
- 平台：必须覆盖 Shopee + TikTok Shop
- 时间窗：7/14/30 天三选一，并在文档解释原因
- Top selling 口径：可用 proxy（rank/sold/评价/互动等），但需解释偏差与替代
- 扩展策略：必须说明候选集召回/增量更新/缓存/人审闭环

### 2.2 MVP 必做能力

1. 数据获取与标准化（Ingestion & Standardisation）

- 两平台 Top selling 列表
- 必含价格 + 至少一种销量/热度 proxy
- 标准化：品牌、规格/单位、币种、proxy 口径

2. 跨平台匹配（Cross-platform matching）

- TikTok item ↔ Shopee item 对齐
- 输出：`match_type`、`confidence`、`reasons`
- 包含阈值与 review/override（Demo 演示）

3. 行动闭环（Action loop, light）

- 机会清单：covered/not_covered/harvestable/not_recommended
- 下一步动作：补货/找货/调价/关注/忽略（规则即可）

### 2.3 Demo 展示要求映射到页面

- Overview：重叠、差异结构、趋势变化、价格带/促销结构
- Top items：筛选列表 + 展示 proxy + 展示匹配理由
- Alerts/Opportunities：爆款预警、平台差异、价格异常、机会清单
- Review：对齐结果的人审/override

---

## 3. 范围与口径（建议的 Demo 默认值）

### 3.1 品类

- 选 1 个规格较标准的品类（如洗衣液/护肤精华），必要时再加 1 个备选。

### 3.2 主时间窗

- 建议主窗口默认 14 天：更抗噪声、又不至于数据量过大；并保留切换 7/30 的参数能力。

### 3.3 Top selling proxy（统一表达）

- 必选：`rank`
- 可选补充：`sold`/`sold_range`/`review_count`/`likes`/`comments`…
- 统一落在 `sales_proxy(proxy_type, proxy_value)`：
  - 若是区间：落中位数或下界 + 在 reasons/notes 标记区间含义

---

## 4. 数据模型（schema-first）

> 目标：任何抓取方式/API/第三方数据都能映射到同一套最小表，保证后续指标、matching、预警可复用。

### 4.1 表与字段（最小闭环）

**top_items**

- `date, platform, item_id, title, category, rank, url`

**price_snapshots**

- `date, platform, item_id, list_price, promo_price?, promo_flag?, currency`

**sales_proxy**

- `date, platform, item_id, proxy_type, proxy_value`

**match_map_platform**

- `tiktok_item_id, shopee_item_id, match_type, confidence, reasons, status`

**our_mapping**

- `platform, item_id, our_status, notes`

**alerts**

- `date, item_id(s), alert_type, severity, status, reasons`

### 4.2 标准化（必须能解释）

- 品牌：`brand_raw → brand_std`（字典/规则 + override）
- 规格：从标题解析 `size_value + size_unit`（ml/g/pcs）并做单位换算
- 币种：从站点推断或源字段读取，统一写入 `currency`

### 4.3 主键、幂等与分区（生产级容易遗漏，但非常关键）

> 题目只给了 minimal schema，但要做到“成熟高性能方案”，必须补齐：主键/去重幂等/类型/分区/血缘，否则增量更新、回放与一致性会失控。

- 时间字段建议拆分：
  - `event_date`：业务日期（窗口计算/趋势分析用）
  - `ingested_at`：入湖/入库时间（增量/回放/可观测用）
- 幂等键（写入/重跑去重）建议：
  - `top_items`：`platform + item_id + event_date + rank_source`
  - `price_snapshots`：`platform + item_id + event_date + price_source`
  - `sales_proxy`：`platform + item_id + event_date + proxy_type`
  - `match_map_platform`：`tiktok_item_id + shopee_item_id`（建议再加 `rule_version/model_version` 用于追溯）
- 类型建议：
  - 价格避免 float：用 Decimal 或“最小货币单位整数”（例如分）
  - `reasons` 建议为结构化 JSON（强证据/弱证据/字段对齐详情），便于 UI 展示与审计
- 分区建议（Iceberg/Delta/ClickHouse）：
  - 至少按 `event_date` 分区；常用筛选再加 `platform`、`category`

---

## 5. 系统架构（Demo 可落地最简形态）

### 5.1 模块划分

1. Ingestion：按平台/品类/时间窗拉取 Top items 与字段
2. Standardisation：解析/清洗/单位换算/币种处理/写入标准表
3. Matching：候选集召回 → 评分 → 阈值分流 → review/override 回写
4. Insights & Alerts：重叠、差异、趋势、价格带、异常与机会清单
5. Demo UI：Overview / Top items / Alerts&Opp / Review

### 5.2 存储建议

- Demo：SQLite 或 DuckDB + 原始抓取文件缓存（便于复现）

### 5.3 生产级架构映射（与第 12/13 节对齐，避免前后割裂）

- Ingestion：采集/抓取/第三方数据 → Kafka（事件总线）→ Object Storage（Bronze / raw）
- Standardisation：Spark/Flink → Iceberg/Delta（Silver / 标准化）
- Matching：
  - Recall：OpenSearch（BM25）+ 向量库（Milvus/pgvector）召回 TopK 候选
  - Rank：规则强约束 + 特征融合打分 → `match_map_platform`
  - Review：`needs_review` 队列 → 人工 override → 回写并沉淀规则资产
- Serving：ClickHouse 负责聚合/分桶/趋势/预警查询；Redis 负责热点缓存
- API/UI：Java/Go 服务层 + React 工作台（列表筛选/详情/审核/状态流转）

---

## 6. 跨平台 Matching 设计（可解释 + 可审阅）

### 6.1 match_type 定义

- `exact_same`：同款同规格（品牌一致 + 规格一致/极小差异 + 标题高相似）
- `variant_family`：同系列不同规格（如 30ml/50ml）
- `similar`：同类相似但无法确认同款
- `no_match`

### 6.2 候选集召回（先快再准）

- 规则召回：同品牌 + 类目相近 + 规格接近
- 文本召回：标题关键词重叠/TF-IDF 相似度（Demo 可用）
- （可选）Embedding 召回：小规模可直接余弦相似

### 6.3 置信度与 reasons

- confidence = 加权组合（品牌/规格/标题相似/类目一致/价格带一致…）
- reasons 输出要求：让业务同学能读懂为什么匹配/为什么不匹配

### 6.4 阈值与 review/override 流程（必须有）

- `confidence >= 0.85`：自动接受（auto_accepted）
- `0.65–0.85`：needs_review
- `< 0.65`：no_match

Review 页面（最小交互）：接受/拒绝/改 match_type → 回写 status，后续优先用 override。

---

## 7. 洞察与预警（满足题目展示项）

### 7.1 Overview 指标

- Top N overlap：按 `exact_same`、`variant_family` 分层统计
- 平台差异结构：TikTok 强 vs Shopee 弱（反向同理）
- 趋势变化：rank jump / proxy spike
- 价格带与促销结构：价格分桶占比 + 促销占比

### 7.2 Alerts（轻量规则即可）

- `rank_jump`：名次提升超过阈值
- `proxy_spike`：proxy 增幅超过阈值
- `platform_gap`：A 平台强但 B 平台弱/无匹配
- `price_anomaly`：同类候选中价格偏离中位数/分位数

---

## 8. 行动闭环（机会清单）

- `covered`：我方已覆盖（同款/同系列）→ 建议关注定价/库存/陈列
- `harvestable`：我方未覆盖但可采 → 建议找货/上新评估
- `not_covered`：未覆盖且待调研 → 进入待办
- `not_recommended`：不建议跟 → 给出原因（可先 stub）

---

## 9. 扩展到千万级的思路（题目要求必须写清）

### 9.1 候选集策略

- 不做全量：只抓“热销候选集”（榜单/Top 列表/关键词 Top 结果）
- matching 只在候选集内做对齐，避免组合爆炸

### 9.2 增量更新

- 每日增量：新增 top item、价格变化、proxy 更新
- 只对变化项重算 matching 与 alerts

### 9.3 缓存

- raw 抓取缓存（平台/品类/日期）
- 标准化解析缓存（title→规格/品牌）
- matching 结果缓存（item_id→mapping，override 优先）

### 9.4 人审闭环

- 低置信度交给审核
- 审核结果沉淀为字典/规则/映射表，持续提升准确率

---

## 10. 风险与验证

- 反爬/字段不稳定：重试 + 降级 + stub 数据
- proxy 偏差：需要在文档说明限制与替代方案
- matching 误判：必须 reasons + review，抽样评估准确率

### 10.1 合规、数据治理与安全（生产级不可遗漏）

- 合规获取：数据采集需遵守平台 ToS/robots/法律法规；优先官方 API 或合规第三方数据。
- 数据治理：
  - 保留 lineage：标准化/匹配结果可回溯到 raw 与规则版本
  - Schema 演进：字段新增/变更版本化，保证下游稳定
- 安全：密钥与令牌用 KMS/Vault 管理；最小权限；若出现敏感字段需脱敏与访问审计

---

## 11. 交付物清单（对齐题目）

- 设计文档：本文件 + `doc/requiment.md`（需求梳理）
- 可运行系统（企业级 MVP）：数据管道 + matching + API + React 工作台 + review/override 闭环
- （可选）Demo 形态：Streamlit/Gradio（用于内部快速展示/回归，不作为主交付）
- Repo + README：运行方式（dev/staging）、数据获取与合规边界、stub/回放、验证与验收脚本

---

## 12. 技术选型（Tech Stack，成熟高性能方案）

> 说明：题目要求是 Demo，但你提出“要用最成熟的业界高性能方案实现”。因此这里给出 **生产级参考架构（推荐）**，同时保留 **Demo 级降级实现**，两者 schema 与流程一致，便于从 Demo 平滑演进。

### 12.1 生产级参考架构（推荐：成熟、可扩展、可观测）

**计算与编排**

- Kubernetes：统一部署与弹性伸缩
- Airflow（批处理编排）+（可选）Argo Workflows：定时/依赖/重试
- （可选）Flink：需要近实时预警时用流式计算

**数据采集与传输**

- Kafka：采集事件/抓取结果的主干消息总线（高吞吐、解耦）
- Connect/自研 Producer：把抓取结果、价格快照、proxy 事件写入 Kafka

**数据湖（长期沉淀 + 可回放 + 成本可控）**

- Object Storage：S3 / GCS / ADLS（raw 与标准化数据分层存储）
- 表格式：Apache Iceberg（或 Delta Lake）：支持 ACID、分区、时间旅行、增量读取

**离线处理与特征计算**

- Spark：标准化清洗、批量 matching、聚合指标与离线回填
- dbt：指标与数据模型的可维护化（可选但成熟）

**在线/交互分析（OLAP Serving）**

- ClickHouse：高性能聚合、分桶、榜单、趋势对比（最契合“看板 + 预警 + 机会清单”）
- Redis：热点缓存（Top items、过滤条件、字典/别名、最近查询）

**检索与向量匹配（Matching 的成熟解法）**

- OpenSearch/Elasticsearch：标题/关键词倒排检索（候选集召回）
- Milvus（或 pgvector/Weaviate）：向量检索（召回相似商品标题/描述）
- 说明：生产上通常是“倒排召回 + 向量召回 + 规则强约束 + 打分融合”，兼顾解释与覆盖。

**服务层与 UI**

- API：Java（Spring Boot）或 Go（Gin/Fiber）
  - 原因：成熟、性能强、工程化与可观测体系完善
  - JDK（开发机/构建默认）：Temurin 25.0.2（`25.0.2-tem`，SDKMAN 管理）
- 前端：React + Ant Design（或 Next.js）
  - 原因：列表筛选、表格、详情、审核工作流更易做成可用工具

**质量、可观测与安全**

- 数据质量：Great Expectations（或 Soda）
- 可观测：OpenTelemetry + Prometheus + Grafana + Loki
- 密钥：Vault / 云 KMS
- CI/CD：GitHub Actions + Helm + ArgoCD（可选）

### 12.2 Demo 级降级实现（在 1–2 天内可交付）

> Demo 仍建议保持与生产级一致的分层与 schema，只是把组件替换为轻量单机版本。

- 语言：Python
- UI：Streamlit
- 存储：DuckDB（单文件）
- 抓取：requests/httpx + BS4（必要时 Playwright）
- matching：规则 + RapidFuzz/TF-IDF（可选 embedding）

---

## 13. 关键实现细节（按生产级高性能方案描述）

### 13.1 数据分层与表设计（Lakehouse）

- Raw 层（Bronze）：保存原始抓取/第三方数据，便于回放与审计
- 标准化层（Silver）：统一 brand/size/unit/currency/proxy 口径
- 服务层（Gold）：面向看板/预警/机会清单的聚合宽表与物化视图

推荐落地：Iceberg 表 + 分区（`platform`、`category`、`date`），并保留 `ingested_at` 支持增量。

### 13.2 采集与更新策略（高吞吐 + 可恢复）

- 抓取/采集任务写入 Kafka（或直接落 raw 存储，再异步入湖）
- 失败重试与幂等：以 `platform + item_id + date` 作为幂等键
- 增量更新：
  - 只处理“新增/变更”的 item（rank/price/proxy 变动）
  - ClickHouse 侧做物化视图或定期聚合，避免每次全量重算

### 13.3 Standardisation（规则资产化）

- 品牌别名表、停用词表、规格解析规则：做成版本化配置（可在 UI 或 Git 管理）
- 关键是可追溯：每条标准化结果要能回溯到 raw 与规则版本（便于解释与纠错）

### 13.4 Matching 的工业化流水线（召回 → 融合 → 审核闭环）

**候选集召回（Recall）**

- 倒排召回：OpenSearch 按 `brand_std + 关键 token` 召回 TopK
- 向量召回：Milvus 按标题向量召回 TopK

**强约束过滤（Hard filters）**

- 规格/单位容忍区间过滤（例如 500ml ±10%）
- 类目/属性一致性过滤

**融合打分（Ranking / Scoring）**

- 组合特征：品牌一致、规格接近、标题相似（BM25/向量相似）、价格带一致
- 输出 `confidence` 与结构化 `reasons`（强证据优先）

**审核闭环（Human-in-the-loop）**

- `needs_review` 进入审核队列（可用工作台 UI）
- override 写回：
  - 覆盖后续同 item 对的自动结果
  - 同时沉淀品牌别名/规格解析修正规则

### 13.5 指标与预警的高性能实现

- 指标计算尽量下推到 ClickHouse：
  - overlap、价格带分布、趋势变化（窗口对比）
  - 预警规则（rank jump/proxy spike/platform gap/price anomaly）
- 预警落库后由服务层提供：
  - 列表查询（分页、筛选）
  - 状态流转（open/ack/closed）

### 13.6 规模化关键点（回答“千万级怎么扩”）

- 不做全量抓取：只抓热销候选集 + 关键词候选集
- 分层缓存：Redis 缓热点；ClickHouse 做交互分析；Iceberg 存历史全量
- 增量与回填：日常走增量，规则变更/模型升级时触发回填任务（Spark）
- 可观测与质量：把字段缺失率、抓取成功率、匹配通过率、人工覆盖率做成监控指标

### 13.7 Demo 如何“对齐生产架构”（避免写成两套）

- Demo 用 DuckDB/本地文件替代 Iceberg + ClickHouse，但表结构与字段保持一致
- Demo matching 先做倒排/规则/相似度，向量检索作为可选项写入路线图
- Demo UI 用 Streamlit，生产 UI 用 React 工作台；接口契约（API schema）保持一致

---

## 14. 小规模可上线使用（成熟高性能、但控制复杂度）

> 目标：在不追求“千万级全量抓取”的前提下，把系统做成可以 **小规模真实使用** 的形态：可观测、可回放、可运维、可扩展。

### 14.1 规模与容量假设（可在 kickoff 明确）

- 品类：1–5 个（逐步扩展）
- 候选集：每天每平台每品类 Top 200–2,000（而不是全量）
- 增量写入：以 `event_date + platform + item_id + proxy_type` 幂等键去重
- 保留周期：raw 30–90 天；标准化与聚合 6–12 个月（按成本调整）

### 14.2 SLO（上线后可用的最低标准）

- 数据新鲜度：每日批处理模式下，T+2h 内产出当日聚合与 alerts（或按业务要求设 T+4h）
- 查询延迟：Overview/列表类接口 P95 < 1s；详情与审核类 P95 < 2s
- 稳定性：核心链路（采集→标准化→服务）日成功率 ≥ 99%（先从 95% 起步也可以，但要监控）
- 质量指标：字段缺失率、匹配自动接受率、needs_review 占比、人工审核吞吐与积压量

### 14.3 最小可用部署拓扑（Small-prod）

在“成熟组件”与“运维成本”之间取平衡，小规模落地建议如下（二选一即可）：

- 方案 A（更成熟、更解耦）：Kafka + Lakehouse（Iceberg/Delta）+ Spark + ClickHouse + OpenSearch（matching recall）+ Redis + API/UI
- 方案 B（更轻、更易运维，但仍高性能）：Object Storage + Spark（或仅批处理）+ ClickHouse（主存储/聚合/Serving）+ OpenSearch（可选）+ Redis + API/UI

说明：

- Matching 在小规模可先不引入向量库：先用 OpenSearch 召回 + 规则/相似度打分；向量库作为后续增强。
- 如果团队暂时不维护 K8s：可以先用虚机/容器编排跑 Airflow/Spark 作业与服务层，但需要把监控/日志/告警补齐。

### 14.4 运维与可观测（必须能定位问题）

- 日志：采集任务、标准化任务、matching 任务、API 服务统一结构化日志（带 `run_id/batch_id/platform/category/event_date`）
- 指标（Prometheus/Otel）：
  - 采集成功率、HTTP 失败率、字段缺失率、解析失败率
  - 增量写入条数、去重命中数（幂等效果）
  - matching 通过率、needs_review 进入量、审核积压量
  - API P95 延迟、错误率
- 告警：
  - 任务失败/延迟超阈值
  - 字段缺失率突增（疑似页面结构变更/反爬）
  - alerts 产出量异常（突然为 0 或暴增）

### 14.5 回放、审计与治理（生产落地常见卡点）

- 回放能力：raw 层保留原始响应（或第三方原始记录），支持“规则/版本变更后重跑”
- 审计字段：
  - 标准化：`rule_version`、`ingested_at`、`source_url/source_type`
  - matching：`rule_version/model_version`、结构化 `reasons`
  - review/override：操作人、时间、旧值/新值（最小审计）
- Schema 演进：字段新增/重命名要版本化，并在下游查询层做兼容

### 14.6 安全与权限（小规模也要做对）

- 密钥管理：抓取 token/第三方 key 用 KMS/Vault；不落日志
- 访问控制：审核/override 权限与只读权限分离；所有 override 可追溯
- 合规：明确 ToS/robots/数据来源边界；优先官方/合规第三方数据源

### 14.7 数据质量（DQ）与发布门禁（让系统“可用且可信”）

- DQ 检查（至少做这几类）：
  - 完整性：TopN 是否达到预期比例（例如 >= 95%）；关键字段缺失率阈值
  - 合理性：价格范围、币种一致性、rank 唯一性（同 platform+event_date 内）
  - 稳定性：与前一日相比的分布漂移（异常突变报警）
- 发布门禁（最小闭环）：
  - 当 DQ 失败时：不更新 Gold 聚合与看板（或标记数据为 degraded），并发告警
  - matching 规则/版本变更：必须可回放、可回滚（保留旧版本产物一段时间）

### 14.8 备份、保留与恢复（DR）

- 数据保留：raw/standardised/serving 分层设置生命周期（成本可控）
- 备份：
  - ClickHouse：每日备份到对象存储（或使用托管备份）
  - 配置与规则资产：品牌别名/规格规则/override 映射版本化（Git 或专表 + 审计）
- 恢复目标（可在 kickoff 对齐）：RPO=24h（先从日更），RTO=4h（核心看板恢复）

### 14.9 成本、频控与缓存（小规模也要“成熟”）

- 频控：对每个平台/站点设置速率限制与并发上限；失败退避；封禁熔断
- 缓存：raw 响应缓存 + 标准化结果缓存 + Serving 热点缓存（Redis）
- 成本护栏：
  - 只抓候选集（Top 列表/关键词 Top），避免全量爆炸
  - 向量库/流处理属于后期增强：仅在有明确收益与运维能力时引入

### 14.10 上线检查清单（小规模可用的“成熟感”来源）

- 口径：站点/币种/时间窗/TopN/proxy 定义固化在配置并可追溯
- 幂等与回放：关键表幂等键生效；支持按 `batch_id/run_id` 回放重算
- 观测与告警：任务成功率、字段缺失率、API P95、审核积压量全都可见且有告警阈值
- 权限与审计：override 可追溯；密钥不落日志；访问最小权限

### 14.11 API 契约（建议用 OpenAPI 固化，保证“可直接实现”）

> 原则：读请求面向看板与审核；写请求只用于审核/override/状态流转，并要求幂等与审计。

**鉴权与角色（RBAC）**

- Auth：优先 OIDC/JWT（小规模可先用 Basic/Auth Proxy，但要有替换路径）
- 角色：
  - `viewer`：只读看板/列表
  - `reviewer`：可处理 review 队列、提交 override
  - `admin`：可管理规则版本/阈值配置（或仅允许通过配置仓库发布）

**核心读接口（示例）**

- `GET /api/v1/overview?platforms=...&category=...&event_date=...&window=14d`
  - 返回：overlap、price_band、trend、核心 KPI
- `GET /api/v1/top-items?platform=...&category=...&event_date=...&limit=...&offset=...&sort=rank`
  - 返回：标准化字段 + proxy + 价格 + 匹配摘要（match_type/confidence）
- `GET /api/v1/items/{platform}/{item_id}`
  - 返回：raw/standardised 摘要、历史快照、匹配候选与 reasons
- `GET /api/v1/alerts?category=...&event_date=...&severity=...&status=open&limit=...&offset=...`
  - 返回：alerts 列表（带 reasons/action）
- `GET /api/v1/review-queue?status=needs_review&limit=...&offset=...`
  - 返回：待审核匹配对 + reasons + 候选对比信息

**核心写接口（示例，需幂等）**

- `POST /api/v1/review/{tiktok_item_id}/{shopee_item_id}/decision`
  - body：`decision=accept|reject|change_type`，`match_type`，`comment`，`rule_version`（可选）
  - 要求：
    - 幂等：支持 `Idempotency-Key` header 或 `decision_id`
    - 审计：记录操作人、时间、旧值/新值、理由
- `POST /api/v1/our-mapping/{platform}/{item_id}`
  - body：`our_status`（covered/harvestable/not_covered/not_recommended），`notes`

**分页/筛选规范（建议统一）**

- 列表统一使用 `limit/offset`（或 cursor）
- 请求必须可复现：把 `event_date/window/category/site` 等关键口径作为必填或默认可追溯参数

### 14.12 Runbook（运行手册：常见故障处置与回放/回滚）

**常见告警与处置**

- 采集失败率升高 / 429/403 增多：
  - 先降速/降并发 → 启用缓存/切换数据源 → 标记当日数据为 degraded
- 字段缺失率突增（页面结构变更/数据源变更）：
  - 回放 raw 抽样对比 → 修复解析规则 → 触发重跑（带新 `rule_version`）
- alerts 产出为 0 或暴增：
  - 检查上游输入量与阈值配置 → 回滚到上一版本阈值/规则 → 重跑当日聚合
- review 队列积压：
  - 临时提升自动接受阈值/减少候选集 TopK → 增加 reviewer 配额 → 只审高价值子集

**回放与回滚原则**

- 回放：任意产物必须能按 `batch_id/run_id + rule_version` 复现
- 回滚：规则/阈值变更必须可回滚到上一版本，并保留一段时间的历史产物用于对比与解释

---

## 15. 相关文档

- PDF 要求梳理：`doc/requiment.md`
- 系统难点与应对：`doc/difficulties.md`
- Kickoff 议程：`doc/Kickoff_60min_Agenda_CN.md`
- 追问问题：`doc/Followup_Questions_15_CN.md`
