CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(128) NOT NULL,
    action VARCHAR(32) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    comment TEXT,
    actor VARCHAR(128) NOT NULL,
    batch_id VARCHAR(64),
    rule_version VARCHAR(16),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_actor ON audit_log(actor, created_at);
