# FDE Case Brief（Top Selling Intelligence）— PDF 要求梳理

> 来源：`doc/requirement/SEA_Retailer_TopSelling_Intelligence_FDE_Case_Brief.pdf`（已抽取文本：`doc/requirement/pdf_extracted_text.txt`）。
> 目的：把题目“要我做什么、必须满足什么、交付什么、展示什么”结构化成可执行清单。

## 1. 题目概览（时间与评估方式）

- Kickoff discussion：60 分钟
- Take-home：1–2 天
- Return：60–90 分钟 review + live demo
- 评估重点：
  - 端到端交付能力（end-to-end delivery）
  - 判断力（scope / trade-offs）
  - 沟通清晰度
- 不期待生产级系统（We do not expect a production system）。

## 2. 业务背景（Business context）

- 客户：某东南亚大型线下零售商（300+ 门店），销售主要在线下，线上数据作为参考信号。
- 规模：
  - 自有在架 SKU：20k–30k
  - 可采/可扩展 SKU：200k+
  - 平台侧商品规模：可达千万级（10M+）
- 目标用户：定价中心与品类团队
- 目标输出：可执行的“看板 + 预警 + 机会清单”
- 允许方式：可用爬虫、第三方数据、公开信息、AI 工具/搜索等（真实工作方式）。
- 合规前提：采集与使用需遵守平台 ToS/robots 与当地法律法规；可行时优先官方 API 或合规第三方数据源。

## 3. 目标（Objective）

做一个可运行的 Top Selling Intelligence demo：

- 对比 TikTok Shop 与 Shopee 在同一品类下的热销结构
- 输出可执行洞察
- 服务定价中心与选品决策

## 4. 固定约束（Fixed constraints，必须满足）

为保证可比性，需要满足：

- 品类：1–2 个品类
- 平台：必须覆盖 Shopee + TikTok Shop
- 时间窗：在 7/14/30 天中选择 1 个作为主窗口，并在文档解释选择原因
- Top selling 口径：允许使用 proxy（如 rank、sold count/区间、评价数、互动量等），但必须说明：
  - 你用的 proxy 具体是什么
  - 这个 proxy 的偏差/噪声
  - 可替代方案（如果字段拿不到/不稳定怎么办）
- 平台千万级规模：不要求全量实现；但文档必须说明上线扩展策略：
  - 候选集召回
  - 增量更新
  - 缓存
  - 人审闭环

## 5. 必交付（Required deliverables / MVP）

### 5.1 Ingestion & standardisation

- 拉取两平台 Top selling 列表
- 列表中必须包含：价格 + 至少一种销量/热度 proxy
- 完成标准化：
  - brand
  - 规格
  - 单位
  - 币种
  - 口径（proxy 的统一表达）

### 5.2 Cross-platform matching

- TikTok item ↔ Shopee item 对齐（同款/同类）
- 必须输出：
  - `match_type`
  - `confidence`
  - `reasons`
- 必须包含：阈值策略 + review/override 流程（demo 演示即可）

### 5.3 Action loop（light）

- 对热销结果输出“机会清单”与下一步动作
- 重点是规则/流程闭环，不要求完美
- 必须覆盖：
  - 我方是否覆盖（covered）
  - 是否可采（harvestable）

## 6. Demo 展示要求（what to show）

### 6.1 Overview

- Top N overlap
- 差异结构
- 趋势变化
- 价格带/促销结构对比

### 6.2 Top items

- 可筛选列表（品牌/规格/价格带）
- 展示字段：平台、rank、price、销量/热度 proxy
- 展示 matching：结果 + 理由

### 6.3 Alerts / opportunities

- 爆款预警：rank jump / proxy 突增
- 平台差异：TikTok 强 vs Shopee 弱等
- 价格异常：同类价格带偏离
- 机会清单：我方覆盖/可采/不建议 + 理由

## 7. 可选项（Optional，任选 1 个；跳过不扣分）

- 接入社交媒体/趋势信号：解释爆款成因或调整预警优先级
- 更精细的我方映射：把我方核心 SKU 子集（500–2,000）与平台 item 更严格对齐，输出更可用建议

## 8. Submission package（最终提交物，3 件）

1. 设计文档（3–5 页，替代 slides）：

- 范围取舍
- 数据口径
- 系统架构
- matching 方法
- demo 信息架构
- 上线扩展方案
- 风险与下一步

2. 可运行 demo：Streamlit / Gradio / 简单前端均可

3. Repo + README：

- 如何运行
- 数据如何获取
- 哪些是 stub
- 使用的 AI 工具
- 关键验证方法（简要）

## 9. Minimal schema（schema-first）

> 题目给了最小表结构示例，建议把整个系统按 schema-first 落地。

- `top_items`：`date, platform, item_id, title, category, rank, url`
- `price_snapshots`：`date, platform, item_id, list_price, promo_price(optional), promo_flag(optional)`（实现上建议补充 `currency` 以满足“币种标准化”的要求）
- `sales_proxy`：`date, platform, item_id, proxy_type, proxy_value`
- `match_map_platform`：`tiktok_item_id, shopee_item_id, match_type, confidence, reasons`
- `our_mapping`：`item_id, our_status(covered/not_covered/harvestable), notes`
- `alerts`：`date, item_id(s), alert_type, severity, status`

## 10. 60 分钟 Kickoff 讨论议程（题目给定）

- 0–10 min：问题复述与范围取舍（品类、时间窗、proxy 选择）
- 10–25 min：数据获取方案（字段口径、更新频率、失败处理）
- 25–45 min：matching 方案（候选集召回、置信度、解释、review/override）
- 45–60 min：demo 信息架构与输出动作（预警、机会清单、下一步）
