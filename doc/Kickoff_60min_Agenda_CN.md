# 60 分钟 Kickoff 讨论拆解（可直接照此主持）

> 会议目标：在 60 分钟内把 Demo 的“范围、口径、数据、matching、展示与行动闭环”全部定下来，并形成可执行的 take-home 计划。

## 0–5 分钟：对齐目标与成功标准

- 复述题目：TikTok Shop vs Shopee Top Selling Intelligence Demo。
- 明确评估点：端到端交付、范围取舍、沟通清晰；不要求生产系统。
- 会议输出物：
  - 选定品类（1–2 个）
  - 选定时间窗（7/14/30）与理由
  - 选定 top selling proxy（至少 1 个）与偏差说明
  - Demo 页面清单（Overview / Top items / Alerts&Opportunities / Review）
  - matching 阈值与 review/override 流程
  - 数据获取路线（含失败与 stub）

## 5–15 分钟：范围取舍（品类、国家站点、Top N）

要决策的点：

- 品类：选 1 个优先（备选 1 个）。
- 站点/国家：若涉及多币种，Demo 是否先固定 1 个站点。
- Top N：Demo 用 Top 100/200/500（根据抓取可行性与展示密度）。

产出：范围声明（写进设计文档开头）：

- “本次 Demo 覆盖：平台=Shopee+TikTok；品类=…；站点=…；时间窗=…；TopN=…；更新频率=每日/手动。”

## 15–25 分钟：口径与数据（proxy、字段、更新频率、失败处理）

要决策的点：

- proxy：rank +（sold/review/likes 任选其一或多 proxy）。
- 价格字段：list_price、promo_price、promo_flag（能拿到则做）。
- 标准化字段：brand、规格（size_value+unit）、币种。
- 更新频率：Demo 选每日/手动触发。
- 合规与数据边界：是否仅使用官方 API/合规第三方数据；如需自研抓取，明确 ToS/robots/频控约束。
- 失败处理：反爬/字段缺失时的降级策略（例如只保留 rank+price；或使用静态样例数据）。
- 性能与稳定性：限速策略、raw 缓存与复现方式（保证“可重复跑通”）。

产出：字段字典（写进文档）：

- 每个平台：能拿到哪些字段、缺失哪些、如何映射到统一 schema。

## 25–45 分钟：Matching 方案（召回、打分、解释、审核闭环）

要决策的点：

- match_type 定义：exact_same / variant_family / similar / no_match。
- 候选集召回：
  - 规则召回（同品牌+规格近似）
  - 文本召回（标题相似度）
- confidence 计算：哪些特征、怎么解释 reasons。
- 阈值：
  - 自动接受阈值（如 0.85）
  - 需要审核区间（如 0.65–0.85）
- review/override：
  - Demo 中如何让用户确认/驳回
  - override 如何回写并在后续优先使用
- 可追溯性（轻量即可）：reasons 结构化、规则版本/数据批次标记，便于解释与回放。

产出：matching 流程图（文档 1 页即可）：

- 候选集 → 评分 → 阈值分流 → 人审 → 回写。

## 45–55 分钟：Demo 信息架构（必须展示哪些页面/指标）

要决策的点：

- Overview：
  - Top N overlap（exact/family）
  - 价格带分布对比
  - 平台差异概览
  - 趋势变化（rank jump / proxy spike）
- Top items 列表：筛选（品牌/规格/价格带）+ 详情（匹配理由）。
- Alerts / Opportunities：规则列表 + 建议动作。
- Review：needs_review 的确认页。

产出：页面与组件清单（写进文档“Demo 信息架构”章节）。

## 55–60 分钟：行动闭环与 take-home 计划

- Action loop：我方覆盖/可采/不建议 的定义与来源（规则/人工标注/简单表）。
- Optional（可选一项）：
  - 社媒/趋势信号，或
  - 我方 500–2,000 SKU 的精细对齐。
- take-home 排期（1–2 天）：
  - Day 1：数据获取与标准化 + 基础页面
  - Day 2：matching + review + alerts/opportunities + 文档/README
- 如果面试官追问“如何扩到千万级/高性能”：用 1 分钟讲清候选集策略、增量更新、缓存、以及可观测/SLO 的最小集合。

产出：待办清单（谁/做什么/截止）。
