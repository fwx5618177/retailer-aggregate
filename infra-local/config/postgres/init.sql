-- PostgreSQL init for SEA Retailer (write-side tables)
-- These will also be managed by Flyway in api-backend, but we include them
-- here as a fallback for standalone database setup.

-- Review decisions (written by reviewers via API)
CREATE TABLE IF NOT EXISTS review_decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tiktok_item_id  VARCHAR(64) NOT NULL,
    shopee_item_id  VARCHAR(64) NOT NULL,
    decision        VARCHAR(32) NOT NULL,
    match_type      VARCHAR(32),
    comment         TEXT,
    reviewer        VARCHAR(128) NOT NULL,
    rule_version    VARCHAR(16),
    batch_id        VARCHAR(64),
    idempotency_key VARCHAR(128),
    old_status      VARCHAR(32),
    new_status      VARCHAR(32),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uk_review_idempotency UNIQUE (idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_review_items ON review_decisions(tiktok_item_id, shopee_item_id);
CREATE INDEX IF NOT EXISTS idx_review_reviewer ON review_decisions(reviewer, created_at);

-- Our internal mapping
CREATE TABLE IF NOT EXISTS our_mapping (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform    VARCHAR(16) NOT NULL,
    item_id     VARCHAR(64) NOT NULL,
    our_status  VARCHAR(32) NOT NULL,
    our_sku_id  VARCHAR(64),
    notes       TEXT,
    updated_by  VARCHAR(128),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uk_mapping UNIQUE (platform, item_id)
);

-- Audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type  VARCHAR(32) NOT NULL,
    entity_id    VARCHAR(128) NOT NULL,
    action       VARCHAR(32) NOT NULL,
    old_value    TEXT,
    new_value    TEXT,
    comment      TEXT,
    actor        VARCHAR(128) NOT NULL,
    batch_id     VARCHAR(64),
    rule_version VARCHAR(16),
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor, created_at);
