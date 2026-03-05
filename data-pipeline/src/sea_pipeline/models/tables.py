"""DuckDB table DDL statements for the SEA data pipeline.

Each constant is a CREATE TABLE IF NOT EXISTS statement that can be executed
directly against a DuckDB connection.
"""

CREATE_TOP_ITEMS = """
CREATE TABLE IF NOT EXISTS top_items (
    event_date      DATE        NOT NULL,
    platform        VARCHAR     NOT NULL,
    category        VARCHAR     NOT NULL,
    site            VARCHAR     NOT NULL,
    rank            INTEGER     NOT NULL,
    item_id         VARCHAR     NOT NULL,
    title           VARCHAR,
    url             VARCHAR,
    image_url       VARCHAR,
    brand_raw       VARCHAR,
    brand_std       VARCHAR,
    size_value      DOUBLE,
    size_unit       VARCHAR,
    pack_count      INTEGER     DEFAULT 1,
    normalized_ml   DOUBLE,
    normalized_g    DOUBLE,
    run_id          VARCHAR     NOT NULL,
    batch_id        VARCHAR     NOT NULL,
    ingested_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_date, platform, category, site, rank)
);
"""

CREATE_PRICE_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS price_snapshots (
    event_date      DATE        NOT NULL,
    platform        VARCHAR     NOT NULL,
    item_id         VARCHAR     NOT NULL,
    price           INTEGER     NOT NULL,
    promo_price     INTEGER,
    currency        VARCHAR     NOT NULL,
    price_per_ml    DOUBLE,
    price_per_g     DOUBLE,
    run_id          VARCHAR     NOT NULL,
    batch_id        VARCHAR     NOT NULL,
    captured_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_date, platform, item_id)
);
"""

CREATE_SALES_PROXY = """
CREATE TABLE IF NOT EXISTS sales_proxy (
    event_date      DATE        NOT NULL,
    platform        VARCHAR     NOT NULL,
    item_id         VARCHAR     NOT NULL,
    proxy_type      VARCHAR     NOT NULL,
    proxy_value     VARCHAR,
    proxy_numeric   DOUBLE,
    run_id          VARCHAR     NOT NULL,
    batch_id        VARCHAR     NOT NULL,
    ingested_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_date, platform, item_id, proxy_type)
);
"""

CREATE_MATCH_MAP_PLATFORM = """
CREATE TABLE IF NOT EXISTS match_map_platform (
    tiktok_item_id      VARCHAR     NOT NULL,
    shopee_item_id      VARCHAR     NOT NULL,
    match_type          VARCHAR,
    confidence          DOUBLE,
    status              VARCHAR,
    reasons             VARCHAR,
    rule_version        VARCHAR,
    model_version       VARCHAR,
    event_date          DATE,
    batch_id            VARCHAR,
    run_id              VARCHAR     NOT NULL,
    ingested_at         TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    schema_version      VARCHAR     DEFAULT '1.0.0',
    PRIMARY KEY (tiktok_item_id, shopee_item_id)
);
"""

CREATE_OUR_MAPPING = """
CREATE TABLE IF NOT EXISTS our_mapping (
    platform            VARCHAR     NOT NULL,
    item_id             VARCHAR     NOT NULL,
    our_status          VARCHAR     NOT NULL,
    our_sku_id          VARCHAR,
    notes               VARCHAR,
    updated_by          VARCHAR,
    updated_at          TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    schema_version      VARCHAR     DEFAULT '1.0.0',
    PRIMARY KEY (platform, item_id)
);
"""

CREATE_ALERTS = """
CREATE TABLE IF NOT EXISTS alerts (
    alert_id        VARCHAR     NOT NULL,
    event_date      DATE        NOT NULL,
    platform        VARCHAR     NOT NULL,
    item_id         VARCHAR     NOT NULL,
    alert_type      VARCHAR     NOT NULL,
    severity        VARCHAR     NOT NULL,
    status          VARCHAR     DEFAULT 'open',
    message         VARCHAR,
    details         VARCHAR,
    suggested_action VARCHAR,
    run_id          VARCHAR     NOT NULL,
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (alert_id)
);
"""

ALL_DDL = [
    CREATE_TOP_ITEMS,
    CREATE_PRICE_SNAPSHOTS,
    CREATE_SALES_PROXY,
    CREATE_MATCH_MAP_PLATFORM,
    CREATE_OUR_MAPPING,
    CREATE_ALERTS,
]
