CREATE SCHEMA IF NOT EXISTS enrollment;
CREATE SCHEMA IF NOT EXISTS processing;
CREATE SCHEMA IF NOT EXISTS messaging;
CREATE SCHEMA IF NOT EXISTS orchestration;

CREATE TABLE IF NOT EXISTS enrollment.enrollment_record (
    enrollment_id VARCHAR(64) PRIMARY KEY,
    employee_id VARCHAR(64) NOT NULL,
    employee_email VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL,
    status_message TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS enrollment.enrollment_selection (
    selection_id VARCHAR(64) PRIMARY KEY,
    enrollment_id VARCHAR(64) NOT NULL REFERENCES enrollment.enrollment_record (enrollment_id) ON DELETE CASCADE,
    benefit_type VARCHAR(100) NOT NULL,
    benefit_plan VARCHAR(100) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_enrollment_record_employee_id
    ON enrollment.enrollment_record (employee_id);

CREATE TABLE IF NOT EXISTS processing.enrollment_processing_record (
    enrollment_id VARCHAR(64) PRIMARY KEY,
    employee_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    processing_message TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_processing_record_employee_id
    ON processing.enrollment_processing_record (employee_id);

CREATE TABLE IF NOT EXISTS messaging.outbox_event (
    event_id VARCHAR(64) PRIMARY KEY,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    delivery_status VARCHAR(32) NOT NULL,
    correlation_id VARCHAR(64) NOT NULL,
    payload TEXT NOT NULL,
    available_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_outbox_event_delivery_status
    ON messaging.outbox_event (delivery_status, available_at);

CREATE TABLE IF NOT EXISTS messaging.inbox_message (
    message_id VARCHAR(64) PRIMARY KEY,
    source_system VARCHAR(100) NOT NULL,
    message_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(64) NOT NULL,
    processing_status VARCHAR(32) NOT NULL,
    payload TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_inbox_message_aggregate_id
    ON messaging.inbox_message (aggregate_id);

CREATE TABLE IF NOT EXISTS orchestration.saga_instance (
    saga_id VARCHAR(64) PRIMARY KEY,
    saga_type VARCHAR(100) NOT NULL,
    business_key VARCHAR(128) NOT NULL,
    saga_state VARCHAR(32) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_saga_instance_type_key
    ON orchestration.saga_instance (saga_type, business_key);

CREATE TABLE IF NOT EXISTS orchestration.saga_step (
    step_id VARCHAR(64) PRIMARY KEY,
    saga_id VARCHAR(64) NOT NULL REFERENCES orchestration.saga_instance (saga_id) ON DELETE CASCADE,
    step_name VARCHAR(100) NOT NULL,
    step_state VARCHAR(32) NOT NULL,
    compensation_state VARCHAR(32),
    step_message TEXT,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_saga_step_saga_id
    ON orchestration.saga_step (saga_id);
