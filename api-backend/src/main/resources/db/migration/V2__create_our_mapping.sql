CREATE TABLE our_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(16) NOT NULL,
    item_id VARCHAR(64) NOT NULL,
    our_status VARCHAR(32) NOT NULL,
    our_sku_id VARCHAR(64),
    notes TEXT,
    updated_by VARCHAR(128),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT uk_mapping UNIQUE (platform, item_id)
);
