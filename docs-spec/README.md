# SEA Retailer Intelligence Platform — 文档规范

> 东南亚零售商情报平台的中央文档中心。
> 本项目追踪东南亚电商平台的商品排名，标准化商品数据，跨平台匹配商品列表，并输出竞争情报洞察。

## 文档索引

### 范围

| 文档 | 描述 |
|-----|------|
| [scope/mvp-scope.md](scope/mvp-scope.md) | MVP 范围定义：目标品类、地区、平台、数据窗口、代理指标，以及明确的非目标。 |

### 设计

| 文档 | 描述 |
|-----|------|
| [design/system-design.md](design/system-design.md) | 端到端系统架构，覆盖 6 大模块（采集、标准化、匹配、告警检测、API 服务、展示层），Mermaid 架构图，存储表，技术栈（Spring Boot + React + DuckDB）。 |
| [design/matching-design.md](design/matching-design.md) | 跨平台商品匹配算法：匹配类型、TF-IDF 召回、加权打分模型、阈值、覆盖合并、评估报告、人工审核工作流。 |
| [design/data-model.md](design/data-model.md) | 数据模型，6 张 DuckDB 表：top_items、price_snapshots、sales_proxy、match_map_platform、our_mapping、alerts。包含完整 DDL、幂等键和跨表关系。 |
| [design/api-design.md](design/api-design.md) | Spring Boot REST API，9 个端点，偏移量分页，Idempotency-Key 幂等保证，审计日志，CORS 配置。 |

### 运维手册

| 文档 | 描述 |
|-----|------|
| [runbooks/429-403-handling.md](runbooks/429-403-handling.md) | HTTP 429（限速）和 403（封禁）抓取失败的事件响应：降速、代理轮换、存根回退、降级标记。 |
| [runbooks/field-missing-spike.md](runbooks/field-missing-spike.md) | 处理字段缺失率飙升：原始数据回放、规则修复、流水线重运行。 |
| [runbooks/alerts-anomaly.md](runbooks/alerts-anomaly.md) | 告警输出异常调查：输入验证、配置回滚、受控重运行。 |
| [runbooks/review-backlog.md](runbooks/review-backlog.md) | 管理审核队列积压：临时阈值调整、审核员扩容、优先级分诊。 |
| [runbooks/replay-rollback.md](runbooks/replay-rollback.md) | 数据回放和回滚流程：以相同 run_id 重运行、版本化配置管理、服务数据恢复。 |

### 合规

| 文档 | 描述 |
|-----|------|
| [compliance/data-sources.md](compliance/data-sources.md) | 数据源优先级层次、服务条款约束、robots.txt 合规、限速策略、回退策略。 |

### 验收

| 文档 | 描述 |
|-----|------|
| [acceptance/e2e-test-cases.md](acceptance/e2e-test-cases.md) | 端到端测试用例：覆盖流水线输出、匹配正确性、API 服务、审核工作流、审计追踪验证。 |
| [acceptance/slo-thresholds.md](acceptance/slo-thresholds.md) | 服务级别目标：数据新鲜度、API 延迟、每日成功率、字段完整性目标。 |
| [acceptance/dq-thresholds.md](acceptance/dq-thresholds.md) | 数据质量门控：TopN 覆盖率、字段缺失率、排名唯一性、货币一致性、价格范围验证。 |

### 版本管理

| 文档 | 描述 |
|-----|------|
| [versioning/version-strategy.md](versioning/version-strategy.md) | Schema、规则和 API 的版本管理策略：语义化版本约定、兼容性规则、变更日志流程。 |

### 架构决策记录（ADR）

| 文档 | 描述 |
|-----|------|
| [adr/001-duckdb-local-clickhouse-prod.md](adr/001-duckdb-local-clickhouse-prod.md) | ADR-001：本地开发用 DuckDB，生产服务用 ClickHouse。理由涵盖零配置本地工作流和 Parquet 互操作。 |
| [adr/002-rule-based-matching.md](adr/002-rule-based-matching.md) | ADR-002：选择基于规则的匹配而非 ML 方法。理由涵盖可解释性、可审计性和冷启动可行性。 |

## 约定

- 所有日期使用 ISO 8601 格式（`YYYY-MM-DD`）。
- 货币金额以最小单位存储（泰铢用 satang），除非另有说明。
- 字段名全部使用 `snake_case`。
- ADR 遵循 `NNN-short-title.md` 格式，一旦接受即不可变。被取代的 ADR 标记但不删除。
- 运维手册按事件类型排序，而非严重级别。每份手册自成一体。

## 状态

| 阶段 | 状态 | 最后更新 |
|-----|------|---------|
| MVP 范围锁定 | 完成（v2.0 — 已补充实现说明） | 2026-02-26 |
| 系统设计 | 完成（v2.1 — 补充认证/限流/缓存/可观测性/召回策略） | 2026-02-26 |
| 数据模型 | 完成（v2.0 — 来自代码的实际 DDL） | 2026-02-26 |
| API 设计 | 完成（v2.1 — 补充限流/认证/429 错误码） | 2026-02-26 |
| 匹配设计 | 完成（v2.1 — 补充 OpenSearch/向量召回策略） | 2026-02-26 |
| 运维手册 | 完成 | 2026-02-25 |
| 验收标准 | 完成 | 2026-02-25 |
| ADR | 2 个已接受 | 2026-02-25 |
| **实现** | **完成 100%（148/148 项）** | **2026-02-26** |
