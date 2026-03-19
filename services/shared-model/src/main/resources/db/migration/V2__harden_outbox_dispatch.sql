ALTER TABLE messaging.outbox_event
    ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_error TEXT,
    ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS claimed_by VARCHAR(128);

CREATE INDEX IF NOT EXISTS idx_outbox_event_claimable
    ON messaging.outbox_event (delivery_status, available_at, claimed_at);
