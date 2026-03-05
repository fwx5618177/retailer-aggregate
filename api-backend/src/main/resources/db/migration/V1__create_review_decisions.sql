CREATE TABLE review_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tiktok_item_id VARCHAR(64) NOT NULL,
    shopee_item_id VARCHAR(64) NOT NULL,
    decision VARCHAR(32) NOT NULL,
    match_type VARCHAR(32),
    comment TEXT,
    reviewer VARCHAR(128) NOT NULL,
    rule_version VARCHAR(16),
    batch_id VARCHAR(64),
    idempotency_key VARCHAR(128),
    old_status VARCHAR(32),
    new_status VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uk_review_idempotency UNIQUE (idempotency_key)
);

CREATE INDEX idx_review_items ON review_decisions(tiktok_item_id, shopee_item_id);
