# Local Setup Guide

This guide gives copy-paste-ready commands to install, start, verify, stop, and clean up the Employee Benefits Event Processing Platform locally.

## 1. Automated Setup (Recommended)

The fastest way to get started — the setup script checks prerequisites, installs what's missing, and prepares the project:

```bash
./scripts/setup.sh
```

This will:
- Check for Java 17+, Docker, Python 3.11+, Node.js 20+, Ollama
- Offer to install anything missing (Homebrew on macOS, apt on Debian/Ubuntu)
- Create `.env` from `.env.example`
- Start PostgreSQL
- Build Java services
- Set up Python venvs for AI Platform
- Install frontend npm dependencies
- Pull Ollama models

Run `./scripts/setup.sh --check` to see what's installed without changing anything.

Once setup is complete, start the platform:

```bash
./scripts/run-local.sh              # Core services (enrollment + processing)
./scripts/run-local.sh --with-ai    # Core + AI chatbot
./scripts/run-local.sh --with-ui    # Core + frontend
./scripts/run-local.sh --all        # Everything
```

Press `Ctrl+C` to stop all services.

If the automated setup doesn't work for your environment, follow the manual steps below.

## 2. Pre-requisites (Manual)

- Java 17 or newer
- Docker Desktop or Docker Engine
- `curl`
- Python 3.11+ (optional — for AI Platform)
- Node.js 20+ (optional — for the frontend UI)
- Ollama (optional — for AI chatbot)

Maven is **not** required globally — the project includes a Maven Wrapper (`./mvnw`).

Verify each dependency:

```bash
java -version
docker --version
docker compose version
curl --version
```

Repository root for all commands below:

```bash
cd <repo-root>
```

Replace `<repo-root>` with the absolute path where you cloned this repository.

## 3. One-command startup

The quickest way to get the full platform running:

```bash
./scripts/run-local.sh
```

This starts PostgreSQL (port 5433 by default), builds the project, and launches both services. To use a different database port:

```bash
DB_PORT=5434 ./scripts/run-local.sh
```

Press `Ctrl+C` to stop the services. PostgreSQL will keep running — see section 4 to stop it.

If you prefer a manual step-by-step setup, continue below.

## 3. Manual setup

### Build

```bash
./mvnw clean install -DskipTests
```

### Start PostgreSQL

Choose a port that is free on your machine and use it consistently for the rest of the commands:

```bash
export DB_PORT=5433
POSTGRES_HOST_PORT=$DB_PORT docker compose -f infrastructure/docker-compose.yml up -d postgres
```

Verify the PostgreSQL container is running:

```bash
docker ps --filter name=employee-benefits-postgres
```

Optional verification of the database connection:

```bash
PGPASSWORD=benefits_app psql -h localhost -p $DB_PORT -U benefits_app -d employee_benefits_platform -c "select 1;"
```

### Start services

Start the Processing Service in terminal 1:

```bash
cd <repo-root>
DB_PORT=$DB_PORT ./mvnw -f services/processing-service/pom.xml spring-boot:run
```

Start the Enrollment Service in terminal 2:

```bash
cd <repo-root>
DB_PORT=$DB_PORT PUBLISHER_TRANSPORT=http PROCESSING_SERVICE_URL=http://localhost:8081 ./mvnw -f services/enrollment-service/pom.xml spring-boot:run
```

> **Note:** `DB_PORT` is required — there is no default. Always set it to the port you exposed PostgreSQL on.

### Verify

Verify both services are healthy:

```bash
curl http://localhost:8080/actuator/health
curl http://localhost:8081/actuator/health
```

Submit a sample enrollment:

```bash
curl -X POST http://localhost:8080/api/enrollments \
  -H "Content-Type: application/json" \
  -d '{
    "employeeId": "E12345",
    "employeeName": "Jane Doe",
    "employeeEmail": "employee@example.com",
    "selections": [
      { "type": "medical", "plan": "gold" },
      { "type": "dental", "plan": "basic" }
    ]
  }'
```

Check enrollment status with the `enrollmentId` from the previous response:

```bash
curl http://localhost:8080/api/enrollments/{enrollmentId}
```

Check enrollment status by employee ID:

```bash
curl http://localhost:8080/api/enrollments/by-employee/E12345
```

Check enrollment status by employee name:

```bash
curl http://localhost:8080/api/enrollments/by-name/Jane%20Doe
```

Check processing status:

```bash
curl http://localhost:8081/api/processed-enrollments/{enrollmentId}
```

Check processing status by employee ID:

```bash
curl http://localhost:8081/api/processed-enrollments/by-employee/E12345
```

Check processing status by employee name:

```bash
curl http://localhost:8081/api/processed-enrollments/by-name/Jane%20Doe
```

Open Swagger UI:

```bash
open http://localhost:8080/swagger-ui/index.html
open http://localhost:8081/swagger-ui/index.html
```

Optional database verification:

```bash
PGPASSWORD=benefits_app psql -h localhost -p $DB_PORT -U benefits_app -d employee_benefits_platform -c "select installed_rank, version, description, success from public.flyway_schema_history order by installed_rank;"
PGPASSWORD=benefits_app psql -h localhost -p $DB_PORT -U benefits_app -d employee_benefits_platform -c "select enrollment_id, employee_id, status, updated_at from enrollment.enrollment_record order by updated_at desc limit 5;"
PGPASSWORD=benefits_app psql -h localhost -p $DB_PORT -U benefits_app -d employee_benefits_platform -c "select delivery_status, attempt_count, last_error from messaging.outbox_event order by created_at desc limit 5;"
PGPASSWORD=benefits_app psql -h localhost -p $DB_PORT -U benefits_app -d employee_benefits_platform -c "select enrollment_id, employee_id, status, updated_at from processing.enrollment_processing_record order by updated_at desc limit 5;"
```

### Start the frontend (optional)

Prerequisites: Node.js 18+

```bash
cd <repo-root>/frontend
npm install
npm run dev
```

Open the UI at `http://localhost:3000`. The Next.js dev server proxies API requests to the backend services running on ports 8080 and 8081.

### Start the AI Platform (optional)

Prerequisites: Python 3.11+, Ollama

**First-time setup:**

```bash
cd <repo-root>/services/ai-platform
./scripts/setup.sh
```

This installs Python dependencies, pulls Ollama models (`llama3.1:8b`, `nomic-embed-text`), creates the `knowledge` schema in PostgreSQL, and offers to seed the knowledge base with benefits documents.

**Start with core services:**

```bash
./scripts/run-local.sh --with-ai
```

**Or start AI services separately:**

```bash
cd <repo-root>/services/ai-platform
./scripts/run-local.sh
```

**Seed the knowledge base** (requires Knowledge Service on port 8300):

```bash
python3 services/ai-platform/knowledge-service/seed-data/seed.py
```

**Verify AI services:**

```bash
curl http://localhost:8100/health               # MCP Server
curl http://localhost:8200/api/ai/health         # AI Gateway
curl http://localhost:8300/api/knowledge/health   # Knowledge Service
```

| Service | Port | Docs |
|---------|------|------|
| MCP Server | 8100 | http://localhost:8100/docs |
| AI Gateway | 8200 | http://localhost:8200/docs |
| Knowledge Service | 8300 | http://localhost:8300/docs |

## 4. Stopping and cleaning up

Stop the Processing Service:

- go to the terminal where it is running
- press `Ctrl+C`

Stop the Enrollment Service:

- go to the terminal where it is running
- press `Ctrl+C`

Stop PostgreSQL but keep the data:

```bash
cd <repo-root>
docker compose -f infrastructure/docker-compose.yml down
```

Stop PostgreSQL and remove the database volume:

```bash
cd <repo-root>
docker compose -f infrastructure/docker-compose.yml down -v
```

Rebuild the shared artifact after changing shared contracts or Flyway migrations:

```bash
cd <repo-root>
./mvnw -pl services/shared-model install
```

## Troubleshooting

### Maven cannot resolve `shared-model` or the parent `pom`

Run from the repository root:

```bash
cd <repo-root>
./mvnw clean install -DskipTests
```

### Docker PostgreSQL port is already in use

Start PostgreSQL on a different host port:

```bash
cd <repo-root>
export DB_PORT=55432
POSTGRES_HOST_PORT=$DB_PORT docker compose -f infrastructure/docker-compose.yml up -d postgres
```

Then use `DB_PORT=55432` when starting both services.

### Enrollment Service or Processing Service port is already in use

Find the process using port `8080`:

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
```

Find the process using port `8081`:

```bash
lsof -nP -iTCP:8081 -sTCP:LISTEN
```

Stop the conflicting process:

```bash
kill <PID>
```

### Flyway or Hibernate reports missing tables or columns

Rebuild and recreate the local database:

```bash
cd <repo-root>
./mvnw -pl services/shared-model install
docker compose -f infrastructure/docker-compose.yml down -v
POSTGRES_HOST_PORT=$DB_PORT docker compose -f infrastructure/docker-compose.yml up -d postgres
```

Then restart both services.

### Enrollment remains `SUBMITTED`

Verify both services are healthy:

```bash
curl http://localhost:8080/actuator/health
curl http://localhost:8081/actuator/health
```

Verify the Enrollment Service is using the local HTTP publisher:

```bash
cd <repo-root>
DB_PORT=$DB_PORT PUBLISHER_TRANSPORT=http PROCESSING_SERVICE_URL=http://localhost:8081 ./mvnw -f services/enrollment-service/pom.xml spring-boot:run
```

Inspect the latest outbox rows:

```bash
PGPASSWORD=benefits_app psql -h localhost -p $DB_PORT -U benefits_app -d employee_benefits_platform -c "select event_id, delivery_status, attempt_count, last_error, available_at from messaging.outbox_event order by created_at desc limit 10;"
```

### Processing record is not created

Verify the Processing Service is running:

```bash
curl http://localhost:8081/actuator/health
```

Inspect inbox and processing tables:

```bash
PGPASSWORD=benefits_app psql -h localhost -p $DB_PORT -U benefits_app -d employee_benefits_platform -c "select message_id, processing_status, received_at from messaging.inbox_message order by received_at desc limit 10;"
PGPASSWORD=benefits_app psql -h localhost -p $DB_PORT -U benefits_app -d employee_benefits_platform -c "select enrollment_id, employee_id, status, updated_at from processing.enrollment_processing_record order by updated_at desc limit 10;"
```

### Verify the database migration level

```bash
PGPASSWORD=benefits_app psql -h localhost -p $DB_PORT -U benefits_app -d employee_benefits_platform -c "select installed_rank, version, description, success from public.flyway_schema_history order by installed_rank;"
```

Expected versions:

- `1` — create platform schemas
- `2` — harden outbox dispatch
- `3` — add employee name support
