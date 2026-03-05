-- ClickHouse schema for SEA Retailer Top Selling Intelligence
-- All read-only / OLAP tables

CREATE DATABASE IF NOT EXISTS sea_retailer;

-- Top selling items
CREATE TABLE IF NOT EXISTS sea_retailer.top_items (
    event_date       Date,
    platform         LowCardinality(String),
    item_id          String,
    title            String,
    category         LowCardinality(String),
    rank             UInt32,
    url              String DEFAULT '',
    brand_raw        Nullable(String),
    brand_std        Nullable(String),
    size_value       Nullable(Float64),
    size_unit        Nullable(String),
    pack_count       Nullable(UInt32),
    image_url        Nullable(String),
    source_type      LowCardinality(String) DEFAULT 'stub',
    ingested_at      DateTime DEFAULT now(),
    batch_id         String DEFAULT '',
    schema_version   String DEFAULT '1.0.0'
) ENGINE = ReplacingMergeTree(ingested_at)
PARTITION BY (event_date, platform)
ORDER BY (platform, category, item_id, event_date);

-- Price snapshots
CREATE TABLE IF NOT EXISTS sea_retailer.price_snapshots (
    event_date       Date,
    platform         LowCardinality(String),
    item_id          String,
    list_price       Int64,
    promo_price      Nullable(Int64),
    promo_flag       UInt8 DEFAULT 0,
    currency         LowCardinality(String) DEFAULT 'THB',
    ingested_at      DateTime DEFAULT now(),
    batch_id         String DEFAULT '',
    schema_version   String DEFAULT '1.0.0'
) ENGINE = ReplacingMergeTree(ingested_at)
PARTITION BY (event_date, platform)
ORDER BY (platform, item_id, event_date);

-- Sales proxy metrics
CREATE TABLE IF NOT EXISTS sea_retailer.sales_proxy (
    event_date       Date,
    platform         LowCardinality(String),
    item_id          String,
    proxy_type       LowCardinality(String),
    proxy_value      String,
    proxy_numeric    Nullable(Float64),
    ingested_at      DateTime DEFAULT now(),
    batch_id         String DEFAULT '',
    schema_version   String DEFAULT '1.0.0'
) ENGINE = ReplacingMergeTree(ingested_at)
PARTITION BY (event_date, platform)
ORDER BY (platform, item_id, event_date, proxy_type);

-- Cross-platform matching results
CREATE TABLE IF NOT EXISTS sea_retailer.match_map_platform (
    tiktok_item_id   String,
    shopee_item_id   String,
    match_type       LowCardinality(String),
    confidence       Float64,
    status           LowCardinality(String),
    reasons          String DEFAULT '{}',
    rule_version     String DEFAULT '1.0.0',
    model_version    Nullable(String),
    ingested_at      DateTime DEFAULT now(),
    batch_id         String DEFAULT '',
    schema_version   String DEFAULT '1.0.0'
) ENGINE = ReplacingMergeTree(ingested_at)
ORDER BY (tiktok_item_id, shopee_item_id);

-- Alerts and opportunities
CREATE TABLE IF NOT EXISTS sea_retailer.alerts (
    alert_id         String,
    event_date       Date,
    platform         Nullable(String),
    item_ids         String DEFAULT '[]',
    alert_type       LowCardinality(String),
    severity         LowCardinality(String),
    status           LowCardinality(String) DEFAULT 'open',
    title            String,
    description      Nullable(String),
    reasons          String DEFAULT '{}',
    suggested_action Nullable(String),
    batch_id         String DEFAULT '',
    schema_version   String DEFAULT '1.0.0'
) ENGINE = ReplacingMergeTree()
ORDER BY (alert_id, event_date);
