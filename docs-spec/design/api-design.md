# API 设计

> 版本: 2.0.0
> 最后更新: 2026-02-26
> 状态: 已接受

## 概述

API 层向 Web 前端和 Streamlit 演示应用暴露流水线数据。基于 **Spring Boot 3.4.2**（Java 21）构建，提供 9 个 RESTful 端点，支持偏移量分页、幂等写入和审计日志。OpenAPI 3.1.0 契约维护在 `shared-contracts/openapi/api-v1.yaml`。

## 基础 URL

```
开发环境: http://localhost:8080/api/v1
生产环境: https://api.sea-retailer.com/api/v1
```

## 认证

| 环境 | 方式 | 说明 |
|-----|------|-----|
| 本地（MVP） | 无 | 不强制认证；使用 `local` Spring 配置 |
| 生产环境 | JWT Bearer | 通过 `Authorization: Bearer <token>` 请求头进行 OIDC/JWT 认证 |

**OIDC 配置**：

| 参数 | 值 |
|-----|---|
| 提供者 | Keycloak 26.0 |
| Realm | `sea-retailer` |
| 端口 | 8180（本地） |
| Issuer URI | `http://localhost:8180/realms/sea-retailer` |
| 角色字段 | JWT `realm_access.roles` |

**RBAC 角色**（通过 `SecurityConfig` 强制执行）：

| 角色 | GET /api/v1/** | POST /review/** | POST /our-mapping/** | 其他操作 |
|-----|---------------|----------------|---------------------|---------|
| `VIEWER` | 允许 | 拒绝 | 拒绝 | 拒绝 |
| `REVIEWER` | 允许 | 允许 | 允许 | 拒绝 |
| `ADMIN` | 允许 | 允许 | 允许 | 允许 |

**Keycloak 角色转换**：`SecurityConfig.KeycloakRoleConverter` 从 JWT 的 `realm_access.roles` 数组中提取角色，映射为 Spring Security 的 `ROLE_VIEWER`、`ROLE_REVIEWER`、`ROLE_ADMIN` 格式。

## 分页契约

所有列表端点使用**偏移量分页**：

| 参数 | 类型 | 默认值 | 描述 |
|-----|------|-------|-----|
| `limit` | integer | 20 | 页大小（最大 100） |
| `offset` | integer | 0 | 跳过的条目数 |

### 响应信封（`PagedResponse<T>`）

```json
{
  "items": [...],
  "total": 400,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

## 通用请求头

### 请求头

| Header | 是否必需 | 描述 |
|--------|---------|-----|
| `X-Request-Id` | 否 | 客户端生成的关联 ID。若缺失，服务端自动生成。 |
| `Idempotency-Key` | POST 请求必需 | 唯一键，防止重复写操作。 |
| `Authorization` | 仅生产环境 | `Bearer <JWT>` 令牌 |

### 响应头

| Header | 描述 |
|--------|-----|
| `X-Request-Id` | 回显请求关联 ID |
| `X-RateLimit-Limit` | 当前窗口的最大请求数（100） |
| `X-RateLimit-Remaining` | 当前窗口剩余的请求数 |
| `Retry-After` | 超限时，等待重试的秒数（仅在 429 时返回） |

## 端点列表

### 1. GET `/healthz`

健康检查端点。不在 `/api/v1` 前缀下。

**Controller**：`HealthController`

**响应**：`200 OK`
```json
{ "status": "UP" }
```

---

### 2. GET `/api/v1/overview`

返回聚合仪表盘 KPI：商品计数、重叠统计、价格区间分布、Top 品牌、告警摘要和元数据。

**Controller**：`OverviewController`

**查询参数**：

| 参数 | 类型 | 默认值 | 描述 |
|-----|------|-------|-----|
| `category` | string | `personal_care` | 商品品类 |
| `event_date` | date | 最新日期 | ISO 8601 日期 |
| `window` | string | `14d` | `7d`、`14d` 或 `30d` |

**响应**：`OverviewResponse`
```json
{
  "event_date": "2026-02-25",
  "window": "14d",
  "top_n": 200,
  "category": "personal_care",
  "platforms": ["tiktok", "shopee"],
  "total_items": { "tiktok": 200, "shopee": 200 },
  "overlap": {
    "exact_same": 45,
    "variant_family": 38,
    "similar": 12,
    "total_matched": 95
  },
  "match_rate": 47.5,
  "needs_review_count": 27,
  "price_band_distribution": [
    { "band": "<100", "tiktok_count": 50, "shopee_count": 45 }
  ],
  "top_brands": [
    { "brand": "NIVEA", "tiktok_count": 15, "shopee_count": 12 }
  ],
  "alerts_summary": {
    "total": 22,
    "by_severity": { "high": 5, "medium": 17 },
    "by_type": { "rank_jump": 8, "proxy_spike": 4, "price_anomaly": 6, "platform_gap": 4 }
  },
  "metadata": {
    "schema_version": "1.0.0",
    "rule_version": "1.0.0",
    "batch_id": "batch_20260225_020000",
    "dq_status": "passed"
  }
}
```

---

### 3. GET `/api/v1/top-items`

返回分页的畅销商品列表，支持多种筛选条件。

**Controller**：`TopItemsController`

**查询参数**：

| 参数 | 类型 | 默认值 | 描述 |
|-----|------|-------|-----|
| `platform` | string | 全部 | `tiktok` 或 `shopee` |
| `category` | string | `personal_care` | 商品品类 |
| `event_date` | date | 最新日期 | ISO 8601 日期 |
| `window` | string | `14d` | 分析窗口 |
| `brand` | string | 全部 | 按 `brand_std` 筛选 |
| `price_min` | integer | — | 最低价格（satang） |
| `price_max` | integer | — | 最高价格（satang） |
| `sort` | string | `rank` | `rank`、`price_asc`、`price_desc`、`title` |
| `match_status` | string | — | `auto_accepted`、`needs_review`、`no_match`、`overridden` |
| `limit` | integer | 20 | 页大小 |
| `offset` | integer | 0 | 跳过数 |

**响应**：`PagedResponse<TopItem>`

**默认排序**：`rank ASC`

---

### 4. GET `/api/v1/items/{platform}/{itemId}`

返回单个商品的详细信息，包括价格历史、销售代理历史和跨平台匹配。

**Controller**：`ItemDetailController`

**路径参数**：

| 参数 | 类型 | 描述 |
|-----|------|-----|
| `platform` | string | `tiktok` 或 `shopee` |
| `itemId` | string | 平台原生商品 ID |

**响应**：`TopItemDetail`
```json
{
  "event_date": "2026-02-25",
  "platform": "tiktok",
  "item_id": "tt_001",
  "title": "NIVEA Body Wash 500ml",
  "rank": 1,
  "price_history": [
    { "event_date": "2026-02-24", "list_price": 29900, "promo_price": 24900 }
  ],
  "proxy_history": [
    { "event_date": "2026-02-25", "proxy_type": "review_count", "proxy_value": "1250" }
  ],
  "matches": [
    {
      "tiktok_item_id": "tt_001",
      "shopee_item_id": "sh_042",
      "match_type": "exact_same",
      "confidence": 0.92,
      "status": "auto_accepted",
      "reasons": { "strong_evidence": ["Brand exact match"], "weak_evidence": [] }
    }
  ]
}
```

**错误**：商品未找到时返回 `404`。

---

### 5. GET `/api/v1/alerts`

返回分页的告警和机会列表。

**Controller**：`AlertsController`

**查询参数**：

| 参数 | 类型 | 默认值 | 描述 |
|-----|------|-------|-----|
| `category` | string | `personal_care` | 商品品类 |
| `event_date` | date | 最新日期 | ISO 8601 日期 |
| `alert_type` | string | — | `rank_jump`、`proxy_spike`、`platform_gap`、`price_anomaly` |
| `severity` | string | — | `critical`、`high`、`medium`、`low` |
| `status` | string | — | `open`、`acknowledged`、`resolved`、`dismissed` |
| `limit` | integer | 20 | 页大小 |
| `offset` | integer | 0 | 跳过数 |

**响应**：`PagedResponse<Alert>`

---

### 6. GET `/api/v1/review-queue`

返回分页的待人工审核匹配对列表。

**Controller**：`ReviewQueueController`

**查询参数**：

| 参数 | 类型 | 默认值 | 描述 |
|-----|------|-------|-----|
| `category` | string | `personal_care` | 商品品类 |
| `sort` | string | `confidence_desc` | `confidence_asc`、`confidence_desc`、`date_desc` |
| `limit` | integer | 20 | 页大小 |
| `offset` | integer | 0 | 跳过数 |

**响应**：`PagedResponse<ReviewQueueItem>`

每个 `ReviewQueueItem` 包含 TikTok 和 Shopee 两侧的商品详情、匹配类型、置信度分数和理由。

---

### 7. POST `/api/v1/review/{tiktokItemId}/{shopeeItemId}/decision`

为匹配对提交审核决策。

**Controller**：`ReviewDecisionController`

**请求头**：`Idempotency-Key` 必需。

**路径参数**：

| 参数 | 类型 | 描述 |
|-----|------|-----|
| `tiktokItemId` | string | TikTok 商品 ID |
| `shopeeItemId` | string | Shopee 商品 ID |

**请求体**（`ReviewDecisionRequest`）：
```json
{
  "decision": "accept",
  "new_match_type": "variant_family",
  "comment": "同一产品线，不同规格"
}
```

| 字段 | 类型 | 是否必需 | 描述 |
|-----|------|---------|-----|
| `decision` | string | 是 | `accept`、`reject` 或 `change_type` |
| `new_match_type` | string | `change_type` 时必需 | `exact_same`、`variant_family`、`similar`、`no_match` |
| `comment` | string | 否 | 自由文本说明 |

**响应**：`200 OK`
```json
{
  "decision_id": "dec_uuid",
  "status": "recorded",
  "message": "Decision recorded successfully"
}
```

**副作用**：
- 更新 DuckDB 中的 `match_map_platform.status`。
- 通过 AuditService 创建审计日志条目（谁/何时/旧值/新值/备注）。

**错误**：重复 `Idempotency-Key` 返回 `409 Conflict`。

---

### 8. GET `/api/v1/our-mapping/{platform}/{itemId}`

获取商品的内部映射信息。

**Controller**：`OurMappingController`

**路径参数**：

| 参数 | 类型 | 描述 |
|-----|------|-----|
| `platform` | string | `tiktok` 或 `shopee` |
| `itemId` | string | 平台原生商品 ID |

**响应**：`OurMapping` 对象，未找到时返回 `404`。

---

### 9. POST `/api/v1/our-mapping/{platform}/{itemId}`

创建或更新商品的内部映射。

**Controller**：`OurMappingController`

**请求体**（`OurMappingRequest`）：
```json
{
  "our_status": "harvestable",
  "our_sku_id": "SKU-12345",
  "notes": "利润空间较好"
}
```

| 字段 | 类型 | 是否必需 | 描述 |
|-----|------|---------|-----|
| `our_status` | string | 是 | `covered`、`not_covered`、`harvestable`、`not_recommended` |
| `our_sku_id` | string | 否 | 内部 SKU 引用 |
| `notes` | string | 否 | 自由文本备注 |

**响应**：`200 OK`
```json
{
  "status": "updated",
  "message": "Mapping updated successfully"
}
```

**副作用**：通过 AuditService 创建审计日志条目。

## 错误响应

所有错误遵循统一格式：

```json
{
  "error": "not_found",
  "message": "Item with ID 'xyz' not found on platform 'shopee'.",
  "request_id": "req_abc123",
  "timestamp": "2026-02-25T10:30:00Z"
}
```

### 标准错误码

| HTTP 状态码 | 错误码 | 描述 |
|-----------|-------|-----|
| 400 | `bad_request` | 参数或请求体无效 |
| 404 | `not_found` | 资源未找到 |
| 409 | `conflict` | 幂等键冲突（不同请求体） |
| 422 | `validation_error` | 请求体 Schema 校验失败 |
| 429 | `rate_limited` | 超过限流阈值（100 请求/分钟/IP）。检查 `Retry-After` 头 |
| 500 | `internal_error` | 服务器错误 |

## 审计追踪

所有写操作（审核决策、our-mapping 更新）由 `AuditService` 记录：

| 字段 | 描述 |
|-----|-----|
| `timestamp` | UTC 时间戳 |
| `action` | 如 `review_decision`、`our_mapping_update` |
| `resource_type` | 如 `match_map_platform`、`our_mapping` |
| `resource_id` | 受影响资源的 ID |
| `old_value` | 先前状态（JSON） |
| `new_value` | 新状态（JSON） |
| `comment` | 用户提供的理由 |
| `user` | 用户标识（生产环境从 JWT 获取，本地为 "anonymous"） |

审计日志为追加写入且不可变。MVP 中审计条目记录到应用日志，生产环境将持久化到专用审计表。

## 限流

API 后端通过 `RateLimitFilter` 对所有非豁免端点实施固定窗口限流。

| 参数 | 值 |
|-----|---|
| 算法 | 固定窗口（每 60 秒重置） |
| 限制 | 100 请求/分钟/客户端 IP |
| IP 提取 | 优先 `X-Forwarded-For` 头，兜底 `request.getRemoteAddr()` |
| 超限响应 | `429 Too Many Requests` + `Retry-After` 头 |

**豁免路径**（不计入限流）：
- `/healthz`
- `/actuator/**`
- `/swagger-ui/**`
- `/api-docs/**`、`/v3/api-docs/**`
- `/h2-console/**`

**存储**：使用 `ConcurrentHashMap<String, AtomicInteger>` 实现线程安全的内存计数。每分钟重置。生产环境可替换为 Redis 实现分布式限流。

## CORS 配置

| 环境 | 允许的来源 |
|-----|----------|
| 本地 | `http://localhost:3000`、`http://localhost:3001` |
| 生产 | 通过环境变量配置 |

## OpenAPI 规范

完整 API 契约维护在 `shared-contracts/openapi/api-v1.yaml`（OpenAPI 3.1.0，711 行）。TypeScript 类型从此规范生成到 `web-frontend/src/api/types.ts`。
