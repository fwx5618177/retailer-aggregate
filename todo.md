# 多仓库实施 TODO（企业级 MVP：可用 / 可部署 / 可运维）

## 企业级 MVP（必须满足的最低验收标准）

- [x] 有明确的"上线形态"：至少 1 个可长期运行的环境（staging 或 prod）+ 回滚策略
- [x] 统一鉴权与授权：OIDC/JWT + RBAC（viewer/reviewer/admin），前后端一致
- [x] 审计可追溯：所有 review/override 写操作有 who/when/old/new/reason，并可检索
- [x] 可观测：结构化日志 + 指标（任务成功率、DQ、API P95、审核积压）+ 告警阈值
- [x] 安全基线：密钥不入库不入日志；最小权限；依赖漏洞扫描（SCA）与基础镜像管理
- [x] 数据质量门禁：DQ 失败不发布（或标记 degraded 且 UI 明示），并可回放重算
- [x] 版本化：schema_version / rule_version / api_version 与兼容规则落地
- [x] 发布与变更可控：至少 1 条 CI 流水线（lint/test/build）+ 1 条 CD/发布流程（手动 gate 也可）
- [x] 备份与恢复：关键存储（ClickHouse/Postgres/对象存储）有备份与演练记录（最小化即可）
- [x] 合规边界可审计：数据来源、频控、robots/ToS 策略文档化并在配置中可追溯

## Repo: docs-spec（需求/口径/契约，文档仓库）

- [x] 明确 MVP 范围：品类（1–2）、站点/国家（1 个优先）、TopN（100/200/500/1000）、主时间窗（7/14/30 选 1 个）
- [x] 明确 Top selling proxy：至少 1 个（rank 必选）+ 可选 proxy（sold/reviews/likes 等）并写出偏差与替代方案
- [x] 明确合规边界：数据来源优先级（官方 API/合规第三方/自研抓取），以及 ToS/robots/频控约束与降级策略
- [x] 固化统一 schema（schema-first）：top_items、price_snapshots（含 currency）、sales_proxy、match_map_platform、our_mapping、alerts
- [x] 固化幂等键与追溯字段：event_date、ingested_at、source_url/source_type、rule_version/model_version、batch_id/run_id
- [x] 固化 matching 口径：match_type 定义、阈值（auto/needs_review/no_match）、reasons 的 JSON 结构
- [x] 固化 DQ 门禁：TopN 覆盖率、关键字段缺失率、rank 唯一性、币种一致性、价格范围、分布漂移阈值
- [x] 固化 API 契约（OpenAPI）：/overview、/top-items、/items/{id}、/alerts、/review-queue、/review decision、/our-mapping
- [x] 固化权限模型（RBAC）：viewer/reviewer/admin + 审计字段
- [x] 固化 Runbook：429/403、字段缺失突增、alerts 异常、review 积压的处置与回放/回滚流程
- [x] 固化交付物：README 目录索引、可复现环境说明（dev/staging）、stub 数据声明、AI 工具使用说明
- [x] 约定跨仓库版本策略：schema_version/rule_version/api_version 的命名与兼容规则
- [x] 约定数据集交换协议：serving 数据输出的目录结构与命名（例如 data/serving/{event_date}/{run_id}/...）
- [x] 固化"企业级 MVP 验收用例"：端到端验收脚本 + SLO/DQ/告警阈值清单 + 权限用例

## Repo: data-pipeline（数据采集与标准化，Python）

- [x] 初始化项目脚手架：Python 版本、依赖管理、代码格式化与 lint（可先轻量）
- [x] 固化依赖与可复现：requirements.txt/uv/poetry（三选一）+ 锁定版本
- [x] 增加最小单元测试骨架：解析/单位换算/字段映射的测试用例
- [x] 约定配置方式：config/default.yaml（platform/category/site/window/topN、频控、阈值、路径、stub 开关）
- [x] 约定日志格式：JSON 日志 + 关键字段（run_id/batch_id/platform/category/site/event_date）
- [x] 实现存储抽象（必须）：local（DuckDB 单文件）+ prod（对象存储 raw + ClickHouse/Parquet serving）
- [x] 实现 raw 缓存：按 platform/category/site/event_date 落盘保存原始响应（支持回放）
- [x] 实现 ingestion：Shopee Top items 拉取（url/title/rank/price + 至少 1 个 proxy）
- [x] 实现 ingestion：TikTok Shop Top items 拉取（url/title/rank/price + 至少 1 个 proxy）
- [x] 实现平台适配层：平台原始字段 → 统一 schema（允许缺字段）
- [x] 实现频控与重试：速率限制、并发上限、退避、错误分类（429/403/解析失败/超时）
- [x] 实现 stub 数据源：抓取失败可回落到 data/raw_stub/（并打标）
- [x] 写入 top_items：按幂等键 upsert/merge（重跑不重复）
- [x] 写入 price_snapshots：价格类型统一（Decimal 或最小货币单位整数），补齐 currency
- [x] 写入 sales_proxy：支持多 proxy_type，并记录 proxy_value 的解释（区间/累计等）
- [x] 实现品牌标准化：brand_raw → brand_std（字典 + 清洗规则 + override 入口）
- [x] 实现规格解析：size_value + size_unit（ml/g/pcs）+ 单位换算
- [x] （可选）识别套装/多件装：pack_count 或标注到 notes/reasons
- [x] 产出标准化宽表或视图：供 matching/看板直接消费
- [x] 实现标准化缓存：title→规格/品牌解析结果缓存（提升增量稳定性）
- [x] 实现 DQ 检查（MVP）：TopN 覆盖率、字段缺失率、rank 唯一性、币种一致性、价格范围
- [x] 实现 DQ 门禁（MVP）：DQ 失败则不更新 serving 产物，并输出 degraded 标记
- [x] 实现批量运行入口（CLI）：run_id/batch_id 注入，支持一键跑通（ingest→standardise→export）
- [x] 输出 serving 数据集（MVP）：导出 Parquet/ClickHouse 可读产物给 API 读取（约定路径与版本）
- [x] 输出元数据清单（MVP）：每次 run 产出 manifest.json（口径参数、行数、缺失率、时间范围、版本号）
- [x] 产出任务指标（企业级必须）：抓取成功率/重试次数/DQ 结果/入库条数（Prometheus 或日志指标化）

## Repo: matching-engine（模型/召回/打分，Python，专注可解释）

- [x] 初始化项目脚手架：依赖、测试骨架、配置（阈值/K/规则版本）
- [x] 固化输入/输出契约：读取标准化数据（DuckDB/Parquet）+ 输出 match_map_platform（带 manifest）
- [x] 定义 match_type 枚举与状态机：auto_accepted/needs_review/no_match/overridden
- [x] 实现候选集召回（MVP）：规则召回（同品牌/规格近似/类目近似）+ 文本相似度召回（TF-IDF/RapidFuzz）
- [x] 实现候选集 TopK 限制：K 可配置，避免组合爆炸
- [x] 实现强约束过滤：规格容忍区间（如 ±10%）、币种/站点一致性
- [x] 实现融合打分：品牌一致、规格接近、标题相似、价格带一致（可选）→ confidence
- [x] 输出结构化 reasons（JSON）：强证据/弱证据/字段对齐详情/缺失字段说明
- [x] 实现阈值分流：>=0.85 自动接受；0.65–0.85 进审核；<0.65 拒绝（阈值可配置）
- [x] 生成 match_map_platform 产物：包含 rule_version、ingested_at、batch_id
- [x] 支持 override 合并：读取已有 override 映射，合并到最终产物并标记 overridden
- [x] 实现最小评估脚本：抽样 30–50 对，统计准确率与典型错误案例（输出到 reports/）
- [x] 输出可回放产物（企业级必须）：保留输入 manifest + 输出 manifest + rule_version/model_version，支持按 run_id 重跑
- [x] （业界成熟升级）引入倒排召回：OpenSearch/Elasticsearch（brand_std + token）召回 TopK
- [x] （业界成熟升级）引入向量召回：Milvus/pgvector（只在需要且具备运维能力时启用）

## Repo: api-backend（API 后端，Java Spring Boot 或 Go；JDK=Temurin 25.0.2）

- [x] 初始化服务骨架：路由、配置管理、日志规范、健康检查（/healthz）
- [x] 固化构建工具链：Java=Temurin 25.0.2；构建用 Maven/Gradle（二选一）并锁定版本
- [x] 增加基本测试：API 合同测试（最少对 /overview、/top-items 返回 schema 做断言）
- [x] 固化 OpenAPI：把 docs-spec 的契约落成 swagger/openapi.yaml 并自动生成文档
- [x] 接入存储（企业级 MVP）：读 ClickHouse（或 Parquet+查询层）+ 写 Postgres（override/审计/配置）
- [x] 实现只读接口（MVP）：GET /overview、GET /top-items、GET /alerts、GET /review-queue、GET /items/{platform}/{item_id}
- [x] 实现写接口（MVP）：POST /review/.../decision、POST /our-mapping/...（写入审计与 override）
- [x] 实现幂等写入：支持 Idempotency-Key 或 decision_id，保证重复提交不产生重复副作用
- [x] 实现 OIDC/JWT 鉴权（企业级 MVP 必须）：对接 IdP（本地可用 Keycloak），并落地 RBAC
- [x] 输出审计日志：who/when/old/new/comment/rule_version/batch_id
- [x] 实现分页与筛选规范：limit/offset + 关键口径参数可追溯
- [x] 增加 CORS/反向代理配置（MVP）：支持前端开发与本地联调
- [x] 可观测（企业级必须）：request_id/trace_id 注入，Prometheus metrics，错误码规范与告警指标
- [x] 安全（企业级必须）：限流（按用户/接口），输入校验（schema 校验），基础 SAST/SCA 门禁

## Repo: web-frontend（前端工作台，React）

- [x] 初始化项目骨架：路由、API client、表格组件、筛选状态管理
- [x] 固化接口 client：基于 OpenAPI 生成（或手写但需与契约对齐）
- [x] 实现 Overview 页（MVP）：核心 KPI、重叠、价格带、趋势
- [x] 实现 Top items 页（MVP）：筛选表格 + 详情抽屉（reasons 展示）
- [x] 实现 Alerts/Opportunities 页（MVP）：预警列表、严重度、建议动作
- [x] 实现 Review 页（MVP）：needs_review 队列、接受/拒绝/改类型、提交 override
- [x] 显示口径可追溯信息：event_date/window/topN/proxy/site/rule_version
- [x] 处理异常与降级：API 不可用/数据 degraded 时给出明确提示
- [x] 接入企业级登录（必须）：OIDC 登录、Token 刷新、基于角色的路由与按钮权限
- [x] 可观测（建议）：前端错误上报（Sentry 或等价），关键交互埋点（review throughput）

## Repo: app-mvp（可选：内部演示/本地调试用，不计入企业级 MVP 主交付）

- [x] 选择 MVP App 形态：Streamlit（推荐）或 Gradio（二选一）
- [x] 设计 MVP 路由与页面：Overview / Top items / Alerts&Opportunities / Review（与 docs 对齐）
- [x] 实现 App 的"数据入口"开关：使用真实抓取 or 使用 stub（并在页面顶部展示当前模式）
- [x] 实现 App 的"口径展示"：event_date/window/topN/proxy/site/rule_version/run_id
- [x] 实现 App 的"运行按钮"：触发一次 pipeline + matching（本地子进程或调用 infra-local 脚本）
- [x] 实现 App 的"Review 写回"：调用 api-backend 写接口（decision + 幂等 key）
- [x] 实现 App 的"降级提示"：抓取失败/字段缺失时给出原因与下一步建议
- [x] 提供 demo 演示剧本：1–2 个关键故事（机会清单/价格异常/平台差异）对应的点击路径

## Repo: shared-contracts（跨仓库共享的契约与类型）

- [x] 维护 schema 定义：表字段、枚举（match_type/status/our_status/alert_type）与 reasons JSON schema
- [x] 维护 OpenAPI（单一真源）：api_version 管理与变更记录
- [x] 为 Python/TS/Java 生成类型（可选但推荐）：避免前后端字段漂移
- [x] 兼容性门禁（企业级必须）：破坏性变更检测（CI 校验），以及契约测试样例数据集

## Repo: infra-local（开发环境：本地联调与可复现）

- [x] 定义本地启动顺序：data-pipeline 产出 serving → matching-engine 产出 match_map → api-backend 启动 → web-frontend 启动
- [x] 提供一键命令（Makefile 或脚本）：make mvp（或等价）
- [x] 提供 docker-compose（企业级联调）：起 api-backend、web-frontend、clickhouse、postgres（可选加 redis/opensearch）
- [x] 提供示例配置与样例数据：保证无外网/反爬情况下也能跑通全链路
- [x] 端到端验收脚本：跑一次 pipeline+matching，然后用 API 拉取 overview/top-items/alerts/review-queue
- [x] 提供开发者入口：make mvp-stub（纯 stub）与 make mvp-live（尽力抓取，失败降级）

## Repo: infra-small-prod（小规模可用的部署与运维，后续演进）

- [x] 选 Small-prod 方案：A（Kafka+Lakehouse+Spark+CH+OS+Redis）或 B（ObjStorage+批处理+CH+可选 OS+Redis）
- [x] 定义 SLO 与告警：数据新鲜度、API P95、任务成功率、字段缺失率、needs_review 占比、审核积压量
- [x] 规划备份与保留：raw/silver/gold 生命周期 + ClickHouse 备份到对象存储
- [x] 规划回放与回滚：rule_version/versioned config + 产物对比与恢复步骤
- [x] 落地 IaC（企业级 MVP 必须）：Terraform/Bicep/Helm（三选一）+ 可复现的环境参数
- [x] 落地 CI/CD（企业级 MVP 必须）：build/test/scan + 部署到 staging（手动 gate 也可）
- [x] 落地可观测（企业级 MVP 必须）：日志采集、指标、告警（至少覆盖任务失败、DQ 失败、API P95、审核积压）
- [x] 落地密钥管理（企业级 MVP 必须）：KMS/Secrets Manager/Sealed Secrets（任选其一）
- [x] 最终验收：现场演示端到端（stub 或真实数据→标准化→matching→review→alerts/opportunities）并能解释 proxy 偏差与扩展策略
