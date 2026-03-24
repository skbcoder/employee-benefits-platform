export interface SchemaTable {
  name: string;
  columns: string[];
  indices?: string[];
}

export interface SchemaGroup {
  schema: string;
  color: string;
  tables: SchemaTable[];
}

export const SCHEMA_TABLES: SchemaGroup[] = [
  {
    schema: "enrollment",
    color: "#22c55e",
    tables: [
      {
        name: "enrollment_record",
        columns: [
          "enrollment_id VARCHAR(64) PK",
          "employee_id VARCHAR(64) NOT NULL",
          "employee_name VARCHAR(255)",
          "employee_email VARCHAR(255)",
          "status VARCHAR(30) NOT NULL",
          "created_at TIMESTAMPTZ",
          "updated_at TIMESTAMPTZ",
        ],
        indices: ["employee_id", "employee_name (case-insensitive)"],
      },
      {
        name: "enrollment_selection",
        columns: [
          "selection_id BIGSERIAL PK",
          "enrollment_id VARCHAR(64) FK",
          "benefit_type VARCHAR(100)",
          "plan_name VARCHAR(100)",
        ],
      },
    ],
  },
  {
    schema: "messaging",
    color: "#eab308",
    tables: [
      {
        name: "outbox_event",
        columns: [
          "event_id VARCHAR(64) PK",
          "aggregate_type VARCHAR(100)",
          "aggregate_id VARCHAR(64)",
          "event_type VARCHAR(100)",
          "delivery_status VARCHAR(20) — PENDING | PUBLISHED | FAILED",
          "correlation_id VARCHAR(64)",
          "payload TEXT",
          "attempt_count INTEGER DEFAULT 0",
          "last_error TEXT(500)",
          "claimed_at TIMESTAMPTZ",
          "claimed_by VARCHAR(128)",
          "available_at TIMESTAMPTZ",
          "created_at, updated_at TIMESTAMPTZ",
        ],
        indices: ["(delivery_status, available_at, claimed_at)"],
      },
      {
        name: "inbox_message",
        columns: [
          "message_id VARCHAR(64) PK",
          "source_system VARCHAR(100)",
          "message_type VARCHAR(100)",
          "aggregate_id VARCHAR(64)",
          "processing_status VARCHAR(20) — RECEIVED | PROCESSED",
          "payload TEXT",
          "received_at, processed_at, updated_at TIMESTAMPTZ",
        ],
        indices: ["aggregate_id"],
      },
    ],
  },
  {
    schema: "processing",
    color: "#3b82f6",
    tables: [
      {
        name: "enrollment_processing_record",
        columns: [
          "enrollment_id VARCHAR(64) PK",
          "employee_id VARCHAR(64)",
          "employee_name VARCHAR(255)",
          "status VARCHAR(30)",
          "processing_message TEXT",
          "received_at, completed_at, updated_at TIMESTAMPTZ",
        ],
        indices: ["employee_id", "employee_name (case-insensitive)"],
      },
    ],
  },
  {
    schema: "knowledge",
    color: "#a855f7",
    tables: [
      {
        name: "document",
        columns: [
          "document_id UUID PK",
          "title, source, category TEXT",
          "content TEXT",
          "metadata JSONB",
          "created_at, updated_at TIMESTAMPTZ",
        ],
      },
      {
        name: "document_chunk",
        columns: [
          "chunk_id UUID PK",
          "document_id UUID FK",
          "chunk_index INTEGER",
          "content TEXT",
          "token_count INTEGER",
          "embedding VECTOR(768)",
          "created_at TIMESTAMPTZ",
        ],
        indices: ["document_id", "cosine similarity (pgvector)"],
      },
    ],
  },
  {
    schema: "governance",
    color: "#eab308",
    tables: [
      {
        name: "audit_trail",
        columns: [
          "id UUID PK",
          "timestamp TIMESTAMPTZ NOT NULL",
          "event_type VARCHAR(100)",
          "agent VARCHAR(100)",
          "action TEXT",
          "risk_level VARCHAR(20)",
          "risk_score NUMERIC(4,2)",
          "policy_decisions JSONB",
          "pii_detected BOOLEAN DEFAULT false",
        ],
        indices: ["timestamp", "agent", "risk_level"],
      },
      {
        name: "approval_request",
        columns: [
          "id UUID PK",
          "conversation_id VARCHAR(64)",
          "agent VARCHAR(100)",
          "action TEXT",
          "risk_level VARCHAR(20)",
          "status VARCHAR(20) — PENDING | APPROVED | DENIED",
          "created_at TIMESTAMPTZ",
          "expires_at TIMESTAMPTZ",
          "reviewer VARCHAR(255)",
        ],
        indices: ["status", "conversation_id"],
      },
      {
        name: "usage_budget",
        columns: [
          "id UUID PK",
          "owner VARCHAR(100)",
          "period VARCHAR(20)",
          "token_limit BIGINT",
          "cost_limit_usd NUMERIC(10,2)",
          "tokens_used BIGINT DEFAULT 0",
          "cost_used_usd NUMERIC(10,2) DEFAULT 0",
        ],
        indices: ["owner", "period"],
      },
    ],
  },
  {
    schema: "orchestration (future)",
    color: "#f97316",
    tables: [
      {
        name: "saga_instance",
        columns: [
          "saga_id UUID PK",
          "saga_type VARCHAR(100)",
          "business_key VARCHAR(64)",
          "status, current_step VARCHAR",
          "context JSONB",
          "started_at, completed_at TIMESTAMPTZ",
        ],
        indices: ["(saga_type, business_key)"],
      },
      {
        name: "saga_step",
        columns: [
          "step_id BIGSERIAL PK",
          "saga_id UUID FK",
          "step_name, status VARCHAR",
          "payload, result JSONB",
          "started_at, completed_at TIMESTAMPTZ",
        ],
      },
    ],
  },
];
