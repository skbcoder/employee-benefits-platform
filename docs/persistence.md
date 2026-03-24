# Persistence Design

The platform uses a single PostgreSQL database (`employee_benefits_platform`) with logical schemas to enforce domain ownership and support multiple integration patterns.

## Schema Layout

| Schema | Purpose | Tables |
|--------|---------|--------|
| `enrollment` | Canonical enrollment request state and benefit selections | `enrollment_record`, `enrollment_selection` |
| `processing` | Downstream execution state for each enrollment | `enrollment_processing_record` |
| `messaging` | Durable event delivery (outbox publish, inbox consume) | `outbox_event`, `inbox_message` |
| `orchestration` | Reserved for saga coordinators and compensating steps | `saga_instance`, `saga_step` (future) |
| `governance` | Audit trail, approval workflows, usage budgets | `audit_trail`, `approval_request`, `usage_budget` |

## Why This Layout

**Event-driven style** — The `messaging.outbox_event` and `messaging.inbox_message` tables support reliable at-least-once delivery and idempotent consumption without distributed transactions.

**Saga style** — The `orchestration` schema is already provisioned so a coordinator can persist long-running workflow state without altering the enrollment or processing schemas.

Both patterns can coexist. The schema boundaries make it clear which service owns which data regardless of the integration pattern in use.

## Service Data Ownership

**Enrollment Service** writes to:
- `enrollment.enrollment_record`
- `enrollment.enrollment_selection`
- `messaging.outbox_event` (the scheduled dispatcher also reads and updates outbox rows)

**Processing Service** writes to:
- `processing.enrollment_processing_record`
- `messaging.inbox_message`

Services must not read or write tables owned by the other service. Cross-service communication flows through the outbox/publisher/inbox path.

**Governance Service** writes to `governance.*` (audit_trail, approval_request, usage_budget). Reads from audit data only — never writes to enrollment or processing schemas.

**Evaluation Service** is stateless — stores results in-memory or exports to JSON/CSV. No database tables.

**Orchestrator Service** delegates data operations to specialist agents. Does not write to any database schema directly.

## Migration Strategy

Flyway migrations live in the `shared-model` module so both services apply the same schema definition against a single database without drift.

After any change to migrations or shared contracts, rebuild the shared artifact before restarting services:

```bash
./mvnw -N install
./mvnw -pl services/shared-model install
```

Current migrations:

| Version | Description |
|---------|-------------|
| V1 | Create platform schemas and base tables |
| V2 | Harden outbox dispatch (claim TTL, attempt count, backoff) |
| V3 | Add employee name support |

### governance schema

Owned by: **Governance Service** (:8500)

| Table | Purpose |
|-------|---------|
| `audit_trail` | Append-only audit log (mutation-prevention triggers) |
| `approval_request` | Human-in-the-loop approval workflows |
| `usage_budget` | Token/cost budget tracking per owner/period |

**Note:** The governance migration (`V1__create_governance_schema.sql`) lives in `services/ai-platform/governance/migrations/`, not in shared-model. It runs independently via the governance service's database initialization.

**Append-only design:** The `audit_trail` table has `BEFORE UPDATE` and `BEFORE DELETE` triggers that raise exceptions, ensuring immutability for compliance requirements.

### Governance Migrations

The governance schema is managed independently from the shared Flyway migrations:
- Location: `services/ai-platform/governance/migrations/V1__create_governance_schema.sql`
- Creates: `governance` schema with `audit_trail`, `approval_request`, `usage_budget` tables
- Includes mutation-prevention triggers on `audit_trail`
- Runs via the governance service's database initialization (not via shared-model)
