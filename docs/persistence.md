# Persistence Design

The platform uses a single PostgreSQL database (`employee_benefits_platform`) with logical schemas to enforce domain ownership and support multiple integration patterns.

## Schema Layout

| Schema | Purpose | Tables |
|--------|---------|--------|
| `enrollment` | Canonical enrollment request state and benefit selections | `enrollment_record`, `enrollment_selection` |
| `processing` | Downstream execution state for each enrollment | `enrollment_processing_record` |
| `messaging` | Durable event delivery (outbox publish, inbox consume) | `outbox_event`, `inbox_message` |
| `orchestration` | Reserved for saga coordinators and compensating steps | `saga_instance`, `saga_step` (future) |

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
