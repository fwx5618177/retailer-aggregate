# MVP 范围定义

> 版本: 2.0.0
> 最后更新: 2026-02-26
> 状态: 已锁定（已更新以反映实现情况）

## 概述

MVP 交付一个面向泰国电商平台个人护理品类的竞争情报流水线。它采集畅销商品排名、标准化商品数据、跨平台匹配商品，并通过轻量级演示 UI 展示每日洞察。

## 目标品类

| 属性 | 值 |
|-----|---|
| 品类 | `personal_care`（个人护理） |
| 子品类 | 沐浴露、洗发水、护肤品（保湿霜、洁面乳、精华液） |
| 品类体系 | 平台原生品类 ID 映射到内部分类体系 |

我们有意限制在单个一级品类内，以保持标准化规则的可管理性。子品类列表可在 personal_care 内扩展，但添加新的一级品类（如 `food_beverage`）需要范围修订。

## 目标地区

| 属性 | 值 |
|-----|---|
| 国家 | 泰国（TH） |
| 货币 | 泰铢（THB） |
| 语言环境 | 显示用 `th-TH`，内部字段用 `en` |
| 时区 | `Asia/Bangkok`（UTC+7） |

所有时间戳内部以 UTC 存储。显示层转换为 `Asia/Bangkok`。

## TopN 配置

| 参数 | 默认值 | 范围 |
|-----|-------|-----|
| `top_n` | 200 | 50 - 500 |
| 范围 | 每平台、每子品类 | - |
| 排序依据 | 平台原生畅销排名 | - |

MVP 从每个平台每个子品类拉取 Top 200 商品。大约 200 × 3 子品类 × 2 平台 = 1,200 个商品列表/每日运行。

## 数据窗口

| 参数 | 默认值 | 可选值 |
|-----|-------|------|
| `window_days` | 14 | 7, 30 |

默认分析窗口为 14 天。窗口参数化，API 消费者和演示 UI 可请求 7 天（短期趋势）或 30 天（月度趋势）视图。采集流水线保留原始数据至少 90 天以支持追溯重处理。

### 窗口语义

- **14 天（默认）**：趋势检测与噪声抑制的最佳平衡。用于所有主要仪表盘视图。
- **7 天**：短期动量检测。适用于闪购影响分析。
- **30 天**：月度表现视图。适用于品牌级战略摘要。

## 销售估算的代理指标

由于实际销量无法直接从平台列表获取，我们使用代理指标：

### 主要代理：排名

| 属性 | 详情 |
|-----|------|
| 字段 | `rank`（整数） |
| 可用性 | 在 Shopee 和 TikTok Shop 畅销页面上始终可用 |
| 解读 | 排名越低 = 预估销量越高 |
| 用途 | 数据窗口内的排名变动是主要趋势信号 |

### 最佳辅助代理：评论数

| 属性 | 详情 |
|-----|------|
| 字段 | `review_count`（整数） |
| 可用性 | 约 95% 的商品列表可获取 |
| 解读 | 评论数增量越高 = 近期销售活动越活跃 |
| 用途 | 佐证排名趋势；排名相同时用作决胜指标 |

### 其他考虑的代理（MVP 中降低优先级）

| 代理 | 降低优先级的原因 |
|-----|---------------|
| `units_sold` | 跨平台显示不一致；Shopee 有时隐藏此数据 |
| `rating` | 太稳定，不适合作为趋势信号；大多数商品集中在 4.5-4.9 |
| `price_discount_pct` | 适用于促销检测但非直接销售代理 |

## 目标平台

| 平台 | 市场 | 数据源方式 |
|-----|------|----------|
| Shopee Thailand | `shopee.co.th` | 可用时使用 API，否则结构化抓取 |
| TikTok Shop Thailand | `tiktokshop.com`（TH 区域） | 结构化抓取，限速控制 |

### 平台特定说明

**Shopee**：
- 畅销排名页面结构良好且稳定。
- 商品详情页包含 `review_count`、`units_sold`（有时）、`rating`、`price`、`brand`。
- 部分数据有 API 端点但需加入联盟计划。

**TikTok Shop**：
- 排名数据可通过品类浏览获取。
- 商品详情页包含 `review_count`、`rating`、`price`。
- 无官方公开 API；结构化抓取是唯一选项。
- 页面结构比 Shopee 变化更频繁；需要更健壮的选择器。

## 更新频率

| 模式 | 频率 | 触发方式 |
|-----|------|---------|
| 生产（MVP） | 每日批处理 | 定时（cron）02:00 UTC+7 |
| 演示 | 按需 | 通过 CLI 或 UI 按钮手动触发 |

每日批处理是主要运行模式。演示时，UI 中的手动触发按钮启动完整的流水线运行。流水线是幂等的：对同一日期重新触发会覆盖该日期的先前数据。

## 实现说明（技术栈变更）

实现过程中做出了以下与原始设计不同的技术决策：

| 原始设计 | 实际实现 | 理由 |
|---------|---------|-----|
| API: FastAPI（Python） | Spring Boot 3.4.2（Java 21） | 类型安全 REST，更丰富的审计/安全生态 |
| 演示 UI: Next.js | React 19 + Vite 6 + TypeScript 5.7 + Tailwind CSS 4 | 更快的开发迭代，无需 SSR 开销的简单 SPA |
| 图表: 仅 Recharts | Recharts（Web）+ Plotly（Streamlit） | 新增 Streamlit 演示作为额外 UI |
| 表: raw_listings、standardized_products 等 | top_items、price_snapshots、sales_proxy 等 | 针对 MVP 数据量简化的 Schema |

## 超出原始范围的已实现功能

以下能力原列为非目标，但已在 MVP 中实现：

1. **告警** — 流水线运行期间自动检测四种告警类型：`rank_jump`、`proxy_spike`、`platform_gap`、`price_anomaly`。可通过 API（`GET /api/v1/alerts`）和两个前端 UI 查看。实现原因是基于拉取的异常检测对竞争情报用例至关重要。

2. **内部 SKU 映射（our_mapping）** — 用于追踪哪些电商平台商品对应运营方自有产品目录的 CRUD API。支持状态：`covered`、`not_covered`、`harvestable`、`not_recommended`。

3. **数据质量状态传播** — DQ 门控结果通过 API 元数据传播到前端降级横幅，提供数据新鲜度问题的可见性。

4. **OIDC/JWT 认证 + RBAC** — 完整的 Keycloak OIDC 集成，Spring Security JWT 验证和三级角色控制（VIEWER/REVIEWER/ADMIN），前端 OIDC Authorization Code + PKCE 登录流程。本地开发模式可跳过。

5. **API 限流** — `RateLimitFilter` 实现固定窗口限流（100 请求/分钟/IP），防止滥用。

6. **可观测性** — 前端 `ErrorBoundary` + Sentry Envelope API 零依赖错误上报 + 业务事件追踪（review_decision、our_mapping_update、page_view、alert_viewed）。

7. **标准化缓存** — `StandardisationCache` 缓存已处理标题的结果（品牌归一 + 规格提取），JSON 文件持久化，LRU 淘汰（最大 10,000 条目）。

8. **高级召回策略** — OpenSearch BM25 全文检索召回 + sentence-transformers 向量召回（FAISS/Milvus），作为可选策略扩展默认的品牌阻隔 + TF-IDF 召回。

9. **安全基线** — `.gitignore` + detect-secrets pre-commit hooks + CI SCA 扫描（pip-audit、OWASP Dependency-Check、npm audit）。

10. **OpenAPI 破坏性变更检测** — oasdiff CI 工作流 + 本地检查脚本，防止意外 API 契约破坏。

11. **备份恢复与密钥管理** — 完整的备份恢复策略文档、数据生命周期管理（Raw/Silver/Gold 三层）、Sealed Secrets 密钥管理方案。

## 非目标（明确排除在 MVP 范围之外）

以下能力仍有意排除在 MVP 之外：

1. **全文搜索** — 不支持跨商品列表的自由文本搜索。筛选仅限品类、平台、品牌和排名范围。

2. **实时数据** — 无流式或近实时更新。所有数据均每日批处理。演示的手动触发仍是完整批处理运行，非实时获取。

3. **社交媒体集成** — 不从 Instagram、Facebook、LINE、Twitter/X 或任何社交平台采集数据。商品情报仅来源于电商平台列表数据。

4. **多国支持** — 仅泰国。无多国路由、货币转换或超出 TH 的区域化标准化基础设施。

5. **用户认证（生产模式强制执行）** — 已实现完整的 OIDC/JWT 认证 + RBAC（Keycloak + Spring Security + React OIDC/PKCE）。本地开发模式（`VITE_AUTH_DISABLED=true` + Spring `local` profile）跳过认证以方便调试。生产环境强制执行三级角色（VIEWER/REVIEWER/ADMIN）。

6. **导出/报告** — 无 CSV/PDF 导出功能。数据仅通过 API 消费并在演示 UI 中展示。

7. **历史回填** — MVP 从启动日期开始收集数据。不尝试抓取或重建项目启动前的历史数据。

## MVP 成功标准

| 标准 | 目标 |
|-----|-----|
| 每日流水线无需人工干预即可完成 | >= 99% 的天数 |
| TopN 覆盖率（成功采集的商品 / 预期数量） | >= 95% |
| 跨平台匹配率（Shopee + TikTok 匹配的商品） | >= 60% |
| 演示 UI 加载洞察页面 | < 3 秒 |
| 数据新鲜度（从计划运行到服务数据可用的时间） | < 2 小时 |
