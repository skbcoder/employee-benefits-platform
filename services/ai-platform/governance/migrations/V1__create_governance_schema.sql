CREATE SCHEMA IF NOT EXISTS governance;

-- Append-only audit trail
CREATE TABLE governance.audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type VARCHAR(64) NOT NULL,
    conversation_id VARCHAR(64),
    agent VARCHAR(32),
    action VARCHAR(64),
    request_summary TEXT,
    response_summary TEXT,
    risk_level VARCHAR(16) DEFAULT 'low',
    risk_score NUMERIC(4,3) DEFAULT 0.000,
    policy_decisions JSONB DEFAULT '[]',
    pii_detected JSONB DEFAULT '[]',
    client_ip VARCHAR(45),
    metadata JSONB DEFAULT '{}'
);

-- Prevent updates/deletes on audit trail (append-only)
CREATE OR REPLACE FUNCTION governance.prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit trail is append-only. Updates and deletes are not permitted.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_trail_no_update
    BEFORE UPDATE ON governance.audit_trail
    FOR EACH ROW EXECUTE FUNCTION governance.prevent_audit_mutation();

CREATE TRIGGER audit_trail_no_delete
    BEFORE DELETE ON governance.audit_trail
    FOR EACH ROW EXECUTE FUNCTION governance.prevent_audit_mutation();

-- Indexes for audit queries
CREATE INDEX idx_audit_timestamp ON governance.audit_trail(timestamp);
CREATE INDEX idx_audit_conversation ON governance.audit_trail(conversation_id);
CREATE INDEX idx_audit_event_type ON governance.audit_trail(event_type);
CREATE INDEX idx_audit_risk_level ON governance.audit_trail(risk_level);

-- Approval workflow
CREATE TABLE governance.approval_request (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(64) NOT NULL,
    agent VARCHAR(32) NOT NULL,
    action VARCHAR(64) NOT NULL,
    context JSONB DEFAULT '{}',
    risk_level VARCHAR(16) NOT NULL,
    risk_score NUMERIC(4,3) DEFAULT 0.000,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    reviewer VARCHAR(128),
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'denied', 'expired'))
);

CREATE INDEX idx_approval_status ON governance.approval_request(status);
CREATE INDEX idx_approval_created ON governance.approval_request(created_at);

-- Token/cost budget tracking
CREATE TABLE governance.usage_budget (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner VARCHAR(128) NOT NULL,
    period VARCHAR(16) NOT NULL,
    period_start DATE NOT NULL,
    token_limit BIGINT NOT NULL DEFAULT 1000000,
    cost_limit_usd NUMERIC(10,4) NOT NULL DEFAULT 100.0000,
    tokens_used BIGINT NOT NULL DEFAULT 0,
    cost_used_usd NUMERIC(10,4) NOT NULL DEFAULT 0.0000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(owner, period, period_start)
);
