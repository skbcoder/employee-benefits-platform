# Architecture Overview

This document provides a concise summary of the platform's architecture. For detailed Mermaid diagrams, state transitions, and the cloud evolution path, see [`system-architecture.md`](system-architecture.md).

## Local Runtime Flow

1. A client submits an enrollment to the Enrollment Service via `POST /api/enrollments`.
2. The Enrollment Service persists the enrollment record, benefit selections, and an outbox event in a single database transaction.
3. A scheduled dispatcher claims pending outbox rows using `FOR UPDATE SKIP LOCKED` and forwards each `EnrollmentEvent` through a publisher adapter.
4. The local HTTP publisher delivers the event to the Processing Service via `POST /internal/enrollment-events`.
5. The Processing Service writes an inbox message (for idempotency) and a processing record to PostgreSQL.
6. The Processing Service completes enrollment processing asynchronously.

Status can be retrieved by `enrollmentId`, `employeeId`, or `employeeName` from either service.

## Why HTTP Instead of EventBridge/SQS

The target architecture uses Amazon EventBridge and SQS for durable, decoupled event delivery. For local development, the HTTP publisher adapter keeps the same service boundaries and event contract while requiring only Java and Docker to run.

The dispatcher depends on a `EnrollmentEventPublisher` interface. Replacing the HTTP adapter with an EventBridge adapter is a configuration change (`PUBLISHER_TRANSPORT=eventbridge`) plus a new adapter implementation — the enrollment API, outbox flow, and processing logic remain unchanged.

## Build Dependency

Flyway migrations are packaged in the `shared-model` module. Both services consume migrations from that JAR, so any schema change requires rebuilding the shared artifact before restarting services:

```bash
./mvnw -N install
./mvnw -pl services/shared-model install
```
