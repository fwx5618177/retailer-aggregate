# 数据生命周期管理

> SEA Retailer Top Selling Intelligence Platform
> 最后更新: 2026-02-26

---

## 目录

1. [数据分层定义](#1-数据分层定义)
2. [各层级保留策略](#2-各层级保留策略)
3. [数据归档与清理流程](#3-数据归档与清理流程)
4. [数据流转生命周期图](#4-数据流转生命周期图)

---

## 1. 数据分层定义

SEA Retailer 平台采用经典的三层数据架构 (Medallion Architecture), 数据从采集到最终服务经历三个阶段:

### 1.1 Raw 层 -- 原始数据

| 属性 | 说明 |
|------|------|
| **中文名称** | 原始数据层 |
| **S3 前缀** | `s3://sea-retailer-data/raw/` |
| **数据来源** | 爬虫 (data-pipeline) 直接输出 |
| **数据格式** | JSON, HTML, CSV (按平台/日期分区) |
| **数据特征** | 未经处理的原始抓取结果, 可能包含重复、缺失、格式不一致的数据 |
| **典型内容** | Shopee/Lazada/TikTok Shop 商品页面原始响应, 价格列表, 分类目录 |
| **保留期** | 90 天 |
| **目录结构** | `raw/{platform}/{date}/{batch_id}/` |

**示例路径**:
```
s3://sea-retailer-data/raw/shopee/2026-02-25/batch_001/products.json
s3://sea-retailer-data/raw/lazada/2026-02-25/batch_001/products.json
s3://sea-retailer-data/raw/tiktok/2026-02-25/batch_001/products.json
```

### 1.2 Silver 层 -- 标准化数据

| 属性 | 说明 |
|------|------|
| **中文名称** | 标准化数据层 |
| **S3 前缀** | `s3://sea-retailer-data/silver/` |
| **数据来源** | data-pipeline 对 Raw 层清洗、标准化后的输出 |
| **数据格式** | Parquet (列式存储, 压缩高效) |
| **数据特征** | 统一 schema, 去重, 字段标准化, 类型校正 |
| **典型内容** | 标准化商品信息 (名称/价格/分类统一格式), 价格快照 (price 以 satang 整数存储) |
| **保留期** | 180 天 |
| **目录结构** | `silver/{entity}/{date}/` |

**数据清洗规则**:
- 商品名称: 去除特殊字符, Unicode 标准化
- 价格: 统一转换为泰铢最小单位 satang (整数)
- 分类: 映射至统一分类体系
- 去重: 基于平台 + 商品 ID 去重

**示例路径**:
```
s3://sea-retailer-data/silver/products/2026-02-25/part-00000.parquet
s3://sea-retailer-data/silver/price_snapshots/2026-02-25/part-00000.parquet
```

### 1.3 Gold 层 -- 服务数据

| 属性 | 说明 |
|------|------|
| **中文名称** | 服务数据层 |
| **S3 前缀** | `s3://sea-retailer-data/gold/` |
| **数据来源** | matching-engine 跨平台匹配 + 聚合分析结果 |
| **数据格式** | Parquet |
| **数据特征** | 面向业务查询优化, 包含跨平台匹配结果、价格趋势分析 |
| **典型内容** | 跨平台匹配商品对, 价格竞争力评分, 畅销排行 |
| **保留期** | 365 天 |
| **目录结构** | `gold/{dataset}/{date}/` |

**示例路径**:
```
s3://sea-retailer-data/gold/matched_products/2026-02-25/part-00000.parquet
s3://sea-retailer-data/gold/price_comparison/2026-02-25/part-00000.parquet
s3://sea-retailer-data/gold/top_selling/2026-02-25/part-00000.parquet
```

---

## 2. 各层级保留策略

### 2.1 保留期总览

```
┌──────────┬──────────────┬──────────────────────────────────────┐
│  层级    │   保留期     │  存储类别转换                        │
├──────────┼──────────────┼──────────────────────────────────────┤
│  Raw     │   90 天      │  0-30天 STANDARD → 30天 IA → 60天   │
│          │              │  GLACIER → 90天 删除                 │
├──────────┼──────────────┼──────────────────────────────────────┤
│  Silver  │  180 天      │  0-60天 STANDARD → 60天 IA → 120天  │
│          │              │  GLACIER → 180天 删除                │
├──────────┼──────────────┼──────────────────────────────────────┤
│  Gold    │  365 天      │  0-90天 STANDARD → 90天 IA → 270天  │
│          │              │  GLACIER → 365天 删除                │
└──────────┴──────────────┴──────────────────────────────────────┘
```

### 2.2 存储类别转换说明

| 存储类别 | 适用场景 | 访问频率 | 成本 |
|---------|---------|---------|------|
| STANDARD | 近期数据, 频繁访问 | 高 | 最高 |
| STANDARD_IA (低频访问) | 较旧数据, 偶尔访问 | 低 | 中等 |
| GLACIER | 归档数据, 极少访问 | 极低 | 最低 |

### 2.3 数据库中的保留策略

除 S3 上的文件数据外, 数据库中的数据也有对应的保留策略:

| 数据库 | 表 | 保留策略 |
|--------|-----|---------|
| PostgreSQL | `products` | 永久保留 (主数据) |
| PostgreSQL | `matched_products` | 永久保留 (匹配关系) |
| ClickHouse | `price_snapshots` | 365 天 (TTL 自动清理) |
| ClickHouse | `platform_metrics` | 180 天 (TTL 自动清理) |

ClickHouse TTL 配置示例:
```sql
ALTER TABLE sea_retailer.price_snapshots
  MODIFY TTL snapshot_time + INTERVAL 365 DAY;

ALTER TABLE sea_retailer.platform_metrics
  MODIFY TTL metric_time + INTERVAL 180 DAY;
```

---

## 3. 数据归档与清理流程

### 3.1 自动清理 (S3 生命周期)

S3 生命周期规则自动管理数据的存储类别转换与过期删除, 无需人工干预。
规则配置参见 `backup-recovery.md` 第 5 节。

**验证命令**:
```bash
# 查看当前生命周期规则
aws s3api get-bucket-lifecycle-configuration \
  --bucket sea-retailer-data

# 查看各前缀下的存储类别分布
aws s3api list-objects-v2 \
  --bucket sea-retailer-data \
  --prefix raw/ \
  --query "Contents[].{Key:Key, StorageClass:StorageClass, Size:Size}" \
  --output table
```

### 3.2 手动归档 (特殊情况)

当需要在保留期结束前提前归档或永久保留某些数据时:

```bash
# 将特定日期的数据提前转移至 GLACIER
aws s3 cp \
  s3://sea-retailer-data/silver/products/2026-01-15/ \
  s3://sea-retailer-data/archive/silver/products/2026-01-15/ \
  --recursive \
  --storage-class GLACIER

# 对重要数据设置对象锁定, 防止误删
aws s3api put-object-retention \
  --bucket sea-retailer-data \
  --key "gold/matched_products/2026-02-25/part-00000.parquet" \
  --retention '{"Mode":"GOVERNANCE","RetainUntilDate":"2027-02-25T00:00:00Z"}'
```

### 3.3 ClickHouse 手动清理

当 TTL 未生效或需要紧急清理时:

```bash
# 查看各分区的数据量
clickhouse-client --query "
  SELECT
    partition,
    count() AS parts,
    formatReadableSize(sum(bytes_on_disk)) AS size
  FROM system.parts
  WHERE database = 'sea_retailer' AND table = 'price_snapshots'
  GROUP BY partition
  ORDER BY partition
"

# 手动删除指定分区
clickhouse-client --query "
  ALTER TABLE sea_retailer.price_snapshots
  DROP PARTITION '202501'
"
```

### 3.4 清理操作审计

所有手动清理操作必须:
1. 在 `#ops-alerts` 频道提前通知
2. 清理前记录受影响的数据范围和行数
3. 清理后确认释放的存储空间
4. 记录至运维操作日志

---

## 4. 数据流转生命周期图

### 4.1 数据流转总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                      数据生命周期流转图                              │
│                                                                     │
│  ┌──────────┐    data-pipeline     ┌──────────┐    matching-engine  │
│  │  外部平台  │ ─────────────────→  │          │ ──────────────────→ │
│  │          │    (每日 06:00 UTC)  │          │   (每日 06:30 UTC)  │
│  │ Shopee   │                     │  Silver  │                     │
│  │ Lazada   │ ───→ ┌────────┐ ──→ │  标准化   │ ──→ ┌────────┐     │
│  │ TikTok   │      │  Raw   │     │  数据     │     │  Gold  │     │
│  └──────────┘      │ 原始   │     │          │     │ 服务   │     │
│                    │ 数据   │     └──────────┘     │ 数据   │     │
│                    └────────┘                      └────────┘     │
│                     90 天          180 天           365 天         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    存储层                                     │   │
│  │                                                              │   │
│  │  S3 STANDARD ──→ S3 STANDARD_IA ──→ S3 GLACIER ──→ 删除    │   │
│  │  (近期数据)       (低频访问)          (归档)        (过期)    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    数据库层                                   │   │
│  │                                                              │   │
│  │  PostgreSQL (主数据)                ClickHouse (分析数据)     │   │
│  │  ├─ products (永久)                ├─ price_snapshots (365天) │   │
│  │  └─ matched_products (永久)        └─ platform_metrics (180天)│   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 单条数据生命周期示例

以一条 Shopee 商品价格数据为例:

```
时间轴 (天)
──────────────────────────────────────────────────────────────→

Day 0: 爬虫抓取
  │
  ├─ raw/shopee/2026-02-25/products.json     ← Raw 层 (JSON)
  │   存储: S3 STANDARD
  │
Day 0 + 数分钟: data-pipeline 处理
  │
  ├─ silver/products/2026-02-25/part-00000.parquet  ← Silver 层
  │   存储: S3 STANDARD
  │   同时写入 → ClickHouse price_snapshots 表
  │
Day 0 + 30分钟: matching-engine 处理
  │
  ├─ gold/matched_products/2026-02-25/part-00000.parquet  ← Gold 层
  │   存储: S3 STANDARD
  │   同时写入 → PostgreSQL matched_products 表
  │
Day 30: Raw 数据转为低频访问
  │   raw/ → S3 STANDARD_IA
  │
Day 60: Raw 数据归档 / Silver 数据转为低频访问
  │   raw/ → S3 GLACIER
  │   silver/ → S3 STANDARD_IA
  │
Day 90: Raw 数据删除 / Gold 数据转为低频访问
  │   raw/ → 删除
  │   gold/ → S3 STANDARD_IA
  │
Day 120: Silver 数据归档
  │   silver/ → S3 GLACIER
  │
Day 180: Silver 数据删除 / ClickHouse platform_metrics TTL 清理
  │   silver/ → 删除
  │
Day 270: Gold 数据归档
  │   gold/ → S3 GLACIER
  │
Day 365: Gold 数据删除 / ClickHouse price_snapshots TTL 清理
      gold/ → 删除
```

### 4.3 数据量预估

基于当前 200 商品/平台 (3个平台, 600 商品总计) 的规模:

| 层级 | 单日数据量 | 30 天累计 | 保留期内总量 |
|------|-----------|----------|-------------|
| Raw | ~5 MB | ~150 MB | ~450 MB (90天) |
| Silver | ~2 MB | ~60 MB | ~360 MB (180天) |
| Gold | ~1 MB | ~30 MB | ~365 MB (365天) |
| **合计** | **~8 MB** | **~240 MB** | **~1.2 GB** |

> 注: 以上为当前 MVP 阶段的估算。生产规模扩大后需重新评估存储成本。
