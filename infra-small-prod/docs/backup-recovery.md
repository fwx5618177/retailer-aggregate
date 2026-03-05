# 备份与恢复策略

> SEA Retailer Top Selling Intelligence Platform
> 最后更新: 2026-02-26

---

## 目录

1. [备份策略概述](#1-备份策略概述)
2. [PostgreSQL 备份](#2-postgresql-备份)
3. [ClickHouse 备份](#3-clickhouse-备份)
4. [DuckDB 本地开发备份](#4-duckdb-本地开发备份)
5. [原始数据保留策略](#5-原始数据保留策略)
6. [灾难恢复流程](#6-灾难恢复流程)
7. [备份验证演练](#7-备份验证演练)

---

## 1. 备份策略概述

本文档定义了 SEA Retailer 平台所有持久化数据存储的备份与恢复策略。核心原则:

- **最小 RPO (恢复点目标)**: 24 小时 — 每日全量备份
- **最大 RTO (恢复时间目标)**: 4 小时 — 从发现故障到服务恢复
- **存储位置**: 所有备份上传至 AWS S3 (桶: `s3://sea-retailer-backups/`)
- **加密**: 所有备份文件使用 AES-256 服务端加密 (SSE-S3)
- **通知**: 备份成功/失败通过 Slack `#ops-alerts` 频道通知

### 备份对象总览

| 数据存储 | 备份方式 | 频率 | 保留期 | 存储位置 |
|----------|---------|------|--------|---------|
| PostgreSQL | `pg_dump` 全量逻辑备份 | 每日 02:00 UTC | 30 天 | S3 |
| ClickHouse | 表级 Parquet 导出 | 每日 03:00 UTC | 30 天 | S3 |
| DuckDB (本地) | 文件级复制 | 手动 | 按需 | 本地磁盘 |
| 原始抓取数据 | S3 生命周期策略 | 持续 | 分层保留 | S3 |

---

## 2. PostgreSQL 备份

### 2.1 备份方式

使用 `pg_dump` 执行每日全量逻辑备份, 以自定义格式 (`-Fc`) 导出, 支持并行恢复。

### 2.2 备份脚本

备份由 Kubernetes CronJob 调度执行 (参见 `helm/sea-retailer/templates/cronjob-backup-pg.yaml`):

```bash
#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="pg_backup_${TIMESTAMP}.dump"

# 执行全量逻辑备份
pg_dump \
  -h "${POSTGRES_HOST}" \
  -U "${POSTGRES_USER}" \
  -d sea_retailer \
  -Fc \
  --no-owner \
  --no-privileges \
  -f "/tmp/${BACKUP_FILE}"

# 上传至 S3
aws s3 cp "/tmp/${BACKUP_FILE}" \
  "s3://sea-retailer-backups/postgres/${BACKUP_FILE}" \
  --sse AES256

# 清理本地临时文件
rm -f "/tmp/${BACKUP_FILE}"

echo "[$(date)] PostgreSQL 备份完成: ${BACKUP_FILE}"
```

### 2.3 保留策略

- **保留期**: 30 天
- **实现方式**: S3 生命周期规则自动删除 `postgres/` 前缀下超过 30 天的对象
- **生命周期规则示例**:

```json
{
  "Rules": [
    {
      "ID": "pg-backup-retention-30d",
      "Prefix": "postgres/",
      "Status": "Enabled",
      "Expiration": { "Days": 30 }
    }
  ]
}
```

### 2.4 恢复流程

**前置条件**: 确保目标 PostgreSQL 实例已启动且可连接。

```bash
# 步骤 1: 列出可用备份
aws s3 ls s3://sea-retailer-backups/postgres/ --recursive | sort -k1,2

# 步骤 2: 下载指定备份文件
aws s3 cp s3://sea-retailer-backups/postgres/pg_backup_20260225_020000.dump /tmp/

# 步骤 3: 停止应用层连接 (缩容 API 服务)
kubectl scale deployment sea-retailer-api --replicas=0 -n sea-retailer

# 步骤 4: 删除并重建数据库
psql -h $POSTGRES_HOST -U postgres -c "DROP DATABASE IF EXISTS sea_retailer;"
psql -h $POSTGRES_HOST -U postgres -c "CREATE DATABASE sea_retailer OWNER sea_retailer;"

# 步骤 5: 恢复数据
pg_restore \
  -h $POSTGRES_HOST \
  -U postgres \
  -d sea_retailer \
  --no-owner \
  --no-privileges \
  --jobs=4 \
  /tmp/pg_backup_20260225_020000.dump

# 步骤 6: 验证数据完整性
psql -h $POSTGRES_HOST -U sea_retailer -d sea_retailer \
  -c "SELECT count(*) FROM products; SELECT count(*) FROM price_snapshots;"

# 步骤 7: 恢复应用层
kubectl scale deployment sea-retailer-api --replicas=1 -n sea-retailer

# 步骤 8: 验证服务正常
curl -s https://sea-retailer.example.com/actuator/health | jq .
```

---

## 3. ClickHouse 备份

### 3.1 备份方式

ClickHouse 使用表级 Parquet 文件导出。每日对核心分析表执行 `SELECT ... INTO OUTFILE ... FORMAT Parquet`, 导出至本地后上传 S3。

### 3.2 备份脚本

```bash
#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/ch_backup_${TIMESTAMP}"
mkdir -p "${BACKUP_DIR}"

# 需要备份的表列表
TABLES=(
  "price_snapshots"
  "matched_products"
  "platform_metrics"
)

for TABLE in "${TABLES[@]}"; do
  clickhouse-client \
    --host "${CH_HOST}" \
    --user "${CH_USER}" \
    --password "${CH_PASSWORD}" \
    --query "SELECT * FROM sea_retailer.${TABLE} FORMAT Parquet" \
    > "${BACKUP_DIR}/${TABLE}.parquet"

  aws s3 cp "${BACKUP_DIR}/${TABLE}.parquet" \
    "s3://sea-retailer-backups/clickhouse/${TIMESTAMP}/${TABLE}.parquet" \
    --sse AES256
done

# 清理本地临时文件
rm -rf "${BACKUP_DIR}"

echo "[$(date)] ClickHouse 备份完成: ${TIMESTAMP}"
```

### 3.3 保留策略

- **保留期**: 30 天
- **实现方式**: S3 生命周期规则自动清理 `clickhouse/` 前缀下过期对象

### 3.4 恢复流程

```bash
# 步骤 1: 列出可用备份快照
aws s3 ls s3://sea-retailer-backups/clickhouse/ | sort

# 步骤 2: 下载指定快照
aws s3 cp s3://sea-retailer-backups/clickhouse/20260225_030000/ /tmp/ch_restore/ --recursive

# 步骤 3: 逐表恢复 (以 price_snapshots 为例)
# 先清空目标表
clickhouse-client --host $CH_HOST --user $CH_USER --password $CH_PASSWORD \
  --query "TRUNCATE TABLE sea_retailer.price_snapshots"

# 导入 Parquet 文件
clickhouse-client --host $CH_HOST --user $CH_USER --password $CH_PASSWORD \
  --query "INSERT INTO sea_retailer.price_snapshots FORMAT Parquet" \
  < /tmp/ch_restore/price_snapshots.parquet

# 步骤 4: 验证行数与最新时间戳
clickhouse-client --host $CH_HOST --user $CH_USER --password $CH_PASSWORD \
  --query "SELECT count(*), max(snapshot_time) FROM sea_retailer.price_snapshots"
```

---

## 4. DuckDB 本地开发备份

DuckDB 用于本地开发和 Streamlit 演示应用 (`app-mvp`), 数据文件为单个 `.duckdb` 文件。

### 4.1 备份方式

直接执行文件级复制:

```bash
# 确保没有进程正在写入 DuckDB 文件
cp data-pipeline/output/sea_retailer.duckdb \
   data-pipeline/output/sea_retailer.duckdb.bak.$(date +%Y%m%d)
```

### 4.2 注意事项

- DuckDB 为嵌入式数据库, 仅用于本地开发环境, **不部署至生产**
- 备份前务必确保无活跃写入连接, 否则可能导致文件损坏
- 如需重建, 可重新运行 `data-pipeline` 从原始数据重新生成

---

## 5. 原始数据保留策略

采用 Raw / Silver / Gold 三层数据分层, 不同层级有不同的保留期:

| 数据层级 | S3 前缀 | 保留期 | 说明 |
|----------|---------|--------|------|
| Raw (原始数据) | `s3://sea-retailer-data/raw/` | 90 天 | 爬虫直接输出的原始 JSON/HTML |
| Silver (标准化数据) | `s3://sea-retailer-data/silver/` | 180 天 | 清洗、标准化后的结构化数据 |
| Gold (服务数据) | `s3://sea-retailer-data/gold/` | 365 天 | 聚合、匹配后的最终服务数据 |

### 5.1 S3 生命周期配置

```json
{
  "Rules": [
    {
      "ID": "raw-data-90d",
      "Prefix": "raw/",
      "Status": "Enabled",
      "Transitions": [
        { "Days": 30, "StorageClass": "STANDARD_IA" },
        { "Days": 60, "StorageClass": "GLACIER" }
      ],
      "Expiration": { "Days": 90 }
    },
    {
      "ID": "silver-data-180d",
      "Prefix": "silver/",
      "Status": "Enabled",
      "Transitions": [
        { "Days": 60, "StorageClass": "STANDARD_IA" },
        { "Days": 120, "StorageClass": "GLACIER" }
      ],
      "Expiration": { "Days": 180 }
    },
    {
      "ID": "gold-data-365d",
      "Prefix": "gold/",
      "Status": "Enabled",
      "Transitions": [
        { "Days": 90, "StorageClass": "STANDARD_IA" },
        { "Days": 270, "StorageClass": "GLACIER" }
      ],
      "Expiration": { "Days": 365 }
    }
  ]
}
```

---

## 6. 灾难恢复流程

当生产环境发生严重故障 (数据库损坏、集群不可用等) 时, 按以下步骤执行灾难恢复:

### 6.1 故障评估 (预计耗时: 15 分钟)

1. 确认故障范围: 单组件故障还是全系统不可用
2. 检查监控面板: Grafana → `SEA Retailer Overview` 仪表盘
3. 检查 Pod 状态: `kubectl get pods -n sea-retailer`
4. 检查存储状态: `kubectl get pvc -n sea-retailer`
5. 在 `#ops-alerts` 频道通报故障

### 6.2 服务隔离 (预计耗时: 5 分钟)

```bash
# 缩容所有应用服务, 防止数据进一步损坏
kubectl scale deployment sea-retailer-api --replicas=0 -n sea-retailer
kubectl scale deployment sea-retailer-frontend --replicas=0 -n sea-retailer

# 暂停定时任务
kubectl patch cronjob sea-retailer-pipeline -n sea-retailer \
  -p '{"spec":{"suspend":true}}'
kubectl patch cronjob sea-retailer-matching -n sea-retailer \
  -p '{"spec":{"suspend":true}}'
```

### 6.3 数据恢复 (预计耗时: 1-2 小时)

按以下顺序恢复各组件:

1. **PostgreSQL**: 按第 2.4 节恢复流程操作
2. **ClickHouse**: 按第 3.4 节恢复流程操作
3. **验证数据一致性**:
   - 核对 PostgreSQL 商品数与 ClickHouse 价格快照数的关联完整性
   - 抽样检查匹配结果是否正确

### 6.4 服务恢复 (预计耗时: 30 分钟)

```bash
# 恢复定时任务
kubectl patch cronjob sea-retailer-pipeline -n sea-retailer \
  -p '{"spec":{"suspend":false}}'
kubectl patch cronjob sea-retailer-matching -n sea-retailer \
  -p '{"spec":{"suspend":false}}'

# 逐步恢复应用服务
kubectl scale deployment sea-retailer-api --replicas=1 -n sea-retailer

# 等待 API 健康检查通过
kubectl rollout status deployment sea-retailer-api -n sea-retailer --timeout=300s

# 恢复前端
kubectl scale deployment sea-retailer-frontend --replicas=1 -n sea-retailer
kubectl rollout status deployment sea-retailer-frontend -n sea-retailer --timeout=120s
```

### 6.5 恢复后验证

```bash
# API 健康检查
curl -s https://sea-retailer.example.com/actuator/health | jq .

# 核心业务功能验证
curl -s https://sea-retailer.example.com/api/v1/products?limit=5 | jq .
curl -s https://sea-retailer.example.com/api/v1/price-snapshots?limit=5 | jq .

# 通知恢复完成
echo "灾难恢复完成, 服务已全面恢复。" | slack-notify '#ops-alerts'
```

### 6.6 事后总结

恢复完成后 48 小时内必须完成:
- 撰写事故报告 (Incident Report)
- 召开事故复盘会议
- 更新本文档 (如有流程改进)

---

## 7. 备份验证演练

### 7.1 演练计划

- **频率**: 每月一次
- **时间**: 每月第一个周三 10:00-12:00 UTC
- **范围**: 轮流覆盖 PostgreSQL 和 ClickHouse 恢复
- **环境**: 在独立的 `sea-retailer-drill` 命名空间中执行, **不影响生产**

### 7.2 演练流程

1. 选取最新的一份备份文件
2. 在演练命名空间中部署临时数据库实例
3. 执行完整恢复流程
4. 验证数据完整性 (行数对比、抽样校验)
5. 记录恢复耗时
6. 清理演练环境
7. 填写演练记录

### 7.3 演练记录模板

```markdown
## 备份恢复演练记录

| 字段 | 内容 |
|------|------|
| 日期 | 2026-MM-DD |
| 执行人 | (姓名) |
| 演练类型 | PostgreSQL / ClickHouse |
| 备份文件 | (S3 路径) |
| 备份日期 | (备份时间戳) |

### 恢复过程

| 步骤 | 开始时间 | 结束时间 | 状态 |
|------|---------|---------|------|
| 下载备份文件 | HH:MM | HH:MM | 成功/失败 |
| 创建临时数据库 | HH:MM | HH:MM | 成功/失败 |
| 执行数据恢复 | HH:MM | HH:MM | 成功/失败 |
| 数据完整性验证 | HH:MM | HH:MM | 成功/失败 |
| 清理演练环境 | HH:MM | HH:MM | 成功/失败 |

### 验证结果

| 指标 | 预期值 | 实际值 | 通过 |
|------|--------|--------|------|
| 总行数 (products) | XXXX | XXXX | 是/否 |
| 总行数 (price_snapshots) | XXXX | XXXX | 是/否 |
| 最新时间戳 | YYYY-MM-DD | YYYY-MM-DD | 是/否 |
| 抽样校验 (10条) | 一致 | 一致/不一致 | 是/否 |

### 总恢复时间

- **RTO 实际值**: XX 分钟
- **是否达标** (< 4 小时): 是/否

### 发现的问题

(无 / 描述问题及改进措施)

### 签字确认

- 执行人: ___________
- 审核人: ___________
```
