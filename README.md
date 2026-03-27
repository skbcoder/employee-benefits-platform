<p align="center">
  <img src=".github/banner.svg" alt="Employee Benefits Platform" width="100%"/>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"/></a>
  <img src="https://img.shields.io/badge/Tests-114%20passing-brightgreen.svg" alt="Tests"/>
  <img src="https://img.shields.io/badge/Services-13-blue.svg" alt="Services"/>
</p>

<p align="center">
  <a href="https://spring.io/projects/spring-boot"><img src="https://img.shields.io/badge/Spring%20Boot-3.3.6-6DB33F.svg?logo=springboot&logoColor=white" alt="Spring Boot"/></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.115-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js-16-000000.svg?logo=nextdotjs&logoColor=white" alt="Next.js"/></a>
  <a href="https://www.langchain.com/langgraph"><img src="https://img.shields.io/badge/LangGraph-Multi--Agent-7C3AED.svg" alt="LangGraph"/></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-4169E1.svg?logo=postgresql&logoColor=white" alt="PostgreSQL"/></a>
  <a href="https://ollama.com/"><img src="https://img.shields.io/badge/Ollama-llama3.1-000000.svg" alt="Ollama"/></a>
</p>

<p align="center">
  <a href="https://aws.amazon.com/"><img src="https://img.shields.io/badge/AWS-Bedrock%20%7C%20ECS%20%7C%20RDS-FF9900.svg?logo=amazonaws&logoColor=white" alt="AWS"/></a>
  <a href="https://www.terraform.io/"><img src="https://img.shields.io/badge/Terraform-IaC-844FBA.svg?logo=terraform&logoColor=white" alt="Terraform"/></a>
  <a href="https://prometheus.io/"><img src="https://img.shields.io/badge/Prometheus-Metrics-E6522C.svg?logo=prometheus&logoColor=white" alt="Prometheus"/></a>
  <a href="https://grafana.com/"><img src="https://img.shields.io/badge/Grafana-Dashboards-F46800.svg?logo=grafana&logoColor=white" alt="Grafana"/></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white" alt="Docker"/></a>
  <a href="https://github.com/features/actions"><img src="https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF.svg?logo=githubactions&logoColor=white" alt="GitHub Actions"/></a>
</p>

---

## What Is This?

A full-stack reference implementation of an **enterprise employee benefits enrollment system** augmented with **AI-powered multi-agent orchestration**. It demonstrates how to build a production-grade platform where:

- Employees submit and track benefit enrollments (medical, dental, vision, life insurance)
- An **AI chatbot** answers questions about benefits plans, checks enrollment status, and helps with submissions — all through natural language
- A **multi-agent system** (LangGraph) routes each user query to the right specialist agent, enforces governance policies, detects PII, scores risk, and audits every decision
- The entire stack runs locally with **zero cloud dependencies** (Ollama for LLM, PostgreSQL for everything) while being architecturally ready for AWS (Bedrock, ECS, RDS)

This is not a toy demo. It implements the patterns you need in production: durable event delivery (transactional outbox/inbox), idempotent processing, policy-as-code governance, RAG with semantic search, 6-layer security hardening, and full observability with Prometheus and Grafana.

---

## How It Works

### The Core Problem

Employee benefit enrollments are high-stakes transactions. A lost enrollment means an employee without health coverage. The platform treats every enrollment as a **durable event**:

```
Employee submits enrollment
        |
        v
[ Enrollment Service ]  ──>  Save to DB + write outbox event (same transaction)
        |
        v
[ Outbox Dispatcher ]  ──>  Claim row (FOR UPDATE SKIP LOCKED) + publish
        |
        v
[ Processing Service ]  ──>  Inbox dedup + process + mark COMPLETED
```

The transactional outbox guarantees **at-least-once delivery**: even if the Processing Service is down, the enrollment is safely persisted and will be delivered when it comes back. The inbox table ensures **idempotent consumption**: duplicate deliveries are ignored.

### The AI Layer

On top of the enrollment pipeline sits an AI platform that provides a conversational interface. Here's how a user query flows through the system:

```
User: "What dental plans are available?"
  |
  v
[ Next.js Frontend ]  ──>  POST /api/ai/chat (120s timeout for LLM latency)
  |
  v
[ AI Gateway ]  ──>  Guardrail check (26 injection patterns)
  |                   Delegate to Orchestrator
  v
[ Orchestrator (LangGraph) ]
  |
  ├── Router: classify intent ──> "benefits_knowledge"
  |
  ├── Benefits Advisor Agent:
  |     Query Knowledge Service ──> semantic search ──> "dental_plans.md" chunks
  |     Send to LLM with RAG context (NO tools, to avoid spurious tool calls)
  |
  ├── Compliance Agent:
  |     PII scan (6 types) ──> risk score ──> policy check (10 YAML rules)
  |
  └── Synthesis Node:
        Strip UUIDs ──> redact PII ──> fix markdown tables ──> return
  |
  v
User sees: formatted table of dental plan options with coverage details
```

For a data query like "Show me Jane Doe's enrollment status," the Router sends it to the **Enrollment Agent** instead, which calls the `get_enrollment_by_name` MCP tool, gets live data from the Enrollment Service API, and formats it for the user.

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js 16)                             │
│  Enrollment UI · Status Dashboard · AI Chatbot · Governance Dashboard     │
│  Architecture Diagrams · MCP Tool Explorer · Embedded Grafana             │
└────────┬──────────────────────┬──────────────────────┬────────────────────┘
         │                      │                      │
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│  Enrollment     │    │  AI Gateway     │    │  Governance     │
│  Service :8080  │    │  :8200          │    │  Service :8500  │
│  REST + Outbox  │    │  Chat + Guard   │    │  Policy + Audit │
└────────┬────────┘    └────────┬────────┘    └─────────────────┘
         │                      │
┌────────▼────────┐    ┌────────▼────────┐    ┌─────────────────┐
│  Processing     │    │  Orchestrator   │    │  Evaluation     │
│  Service :8081  │    │  :8400          │    │  Service :8600  │
│  Inbox + Async  │    │  LangGraph      │    │  Benchmarks     │
└─────────────────┘    │  Multi-Agent    │    └─────────────────┘
                       └────────┬────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│  MCP Server     │    │  Knowledge      │    │  Ollama         │
│  :8100          │    │  Service :8300  │    │  :11434         │
│  7 Tools (SSE)  │    │  RAG + pgvector │    │  llama3.1:8b    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│  PostgreSQL 16  │    │  Prometheus     │    │  Grafana        │
│  + pgvector     │    │  :9090          │    │  :3001          │
│  6 schemas      │    │  Metrics        │    │  Dashboards     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Loose Coupling by Design

Every service communicates through **well-defined boundaries** and can be developed, deployed, and scaled independently:

| Boundary | Mechanism | Why It Matters |
|----------|-----------|----------------|
| Enrollment ↔ Processing | Transactional outbox + publisher adapter | Transport is a config flag (`http` or `eventbridge`). Swap to SQS without changing a line of business logic. |
| AI Gateway ↔ Orchestrator | HTTP API delegation | Gateway handles auth, rate limiting, guardrails. Orchestrator handles agent logic. Each evolves independently. |
| Orchestrator ↔ Benefits APIs | MCP tools via `_benefits_proxy` | Tools are defined once in the MCP Server. The Orchestrator calls them by name — it doesn't know or care about REST endpoints. |
| Orchestrator ↔ Knowledge Base | RAG client over HTTP | Knowledge Service owns chunking, embedding, and search. Orchestrator just asks "what's relevant to this query?" |
| Governance ↔ Everything | Policy-as-code (YAML) | Add a governance rule by editing a YAML file. No code changes in any service. |
| Java ↔ Python services | REST APIs only | Java services own enrollment data. Python services own AI logic. Neither shares a database or internal model. |

---

## How MCP Connects AI to the Enrollment Pipeline

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is the bridge between the AI layer and the benefits APIs. Instead of hardcoding API calls into the LLM prompts, we define **tools** that the LLM can choose to invoke:

### MCP Tools (7)

| Tool | Maps To | What It Does |
|------|---------|-------------|
| `submit_enrollment` | `POST /api/enrollments` | Submit a new benefits enrollment |
| `get_enrollment` | `GET /api/enrollments/{id}` | Look up enrollment by ID |
| `get_enrollment_by_employee` | `GET /api/enrollments/by-employee/{id}` | Look up by employee ID |
| `get_enrollment_by_name` | `GET /api/enrollments/by-name/{name}` | Look up by employee name |
| `list_enrollments_by_status` | `GET /api/enrollments/by-status?status=` | List enrollments by status |
| `get_processing_details` | `GET /api/processed-enrollments/{id}` | Get processing record |
| `check_enrollment_status` | Combined lookup | Full status with state derivation |

### Why MCP?

1. **The LLM doesn't call REST APIs directly.** It requests a tool by name with structured arguments. The MCP Server translates that into the right HTTP call.
2. **Tool definitions are reusable.** The same MCP tools work with Claude Desktop, Claude Code, or our custom Orchestrator — any MCP-compatible client.
3. **Adding a new capability is one tool definition.** When we add a new endpoint to the Enrollment Service, we add one tool to the MCP Server. The Orchestrator automatically discovers it.
4. **SSE transport** for remote clients. The MCP Server exposes tools via Server-Sent Events, so external AI clients can discover and invoke them over HTTP.

### Tool Result Post-Processing

Raw API responses contain internal UUIDs (`enrollmentId`, `processedEnrollmentId`) that are meaningless to users. The MCP client strips these before the LLM sees them:

```python
_UUID_FIELDS = {"enrollmentId", "id", "processedEnrollmentId"}

def _strip_internal_ids(data):
    if isinstance(data, dict):
        return {k: _strip_internal_ids(v) for k, v in data.items() if k not in _UUID_FIELDS}
    if isinstance(data, list):
        return [_strip_internal_ids(item) for item in data]
    return data
```

The LLM only sees Employee Name, Employee ID, Status, Benefit Type, and dates — the fields users actually care about.

---

## Multi-Agent Orchestration (LangGraph)

A single LLM with all tools attached produces poor results with smaller models (8B parameters) — it tries to call tools for knowledge questions, fabricates employee data, and ignores RAG context. The solution is a **multi-agent architecture** where each agent is specialized:

```
User Query
    │
    ▼
┌─────────┐
│  Router │ ──> Classify intent (keyword match + LLM fallback)
└────┬────┘     Check conversation history for context continuity
     │
     ├──> enrollment_query ──> [ Enrollment Agent ]
     │                           7 MCP tools, fabrication guard,
     │                           plan-tier validation
     │
     ├──> benefits_knowledge ──> [ Benefits Advisor ]
     │                            RAG search (16 docs, 45 chunks),
     │                            contextual re-query
     │
     ├──> compliance_check ──> [ Compliance Agent ]
     │                          PII detection (6 types),
     │                          risk scoring (5 factors)
     │
     └──> critical_risk ──> [ Escalation Agent ]
                             Human-in-the-loop approval,
                             30-min timeout
     │
     ▼
┌───────────────┐
│ Synthesis Node│ ──> Merge responses, strip UUIDs/PII,
└───────────────┘     repair markdown tables, sanitize output
     │
     ▼
  Response
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Two-phase routing** (knowledge vs. data) | Small LLMs (8B) are biased toward tool calling when tools are present. Knowledge questions are sent to the LLM *without* tools, so it answers from RAG context instead of making spurious tool calls. |
| **Fabrication guard** | The LLM can't submit enrollments with employee IDs it made up. The guard validates that referenced data exists before executing write operations. |
| **Dual LLM provider** | Ollama for local development, AWS Bedrock for production. A config flag switches the provider — no code changes. |
| **Markdown table repair** | Small LLMs produce malformed GFM tables (missing separators, wrapped in code fences). The Synthesis Node fixes these before rendering. |

---

## RAG Knowledge Base

The Knowledge Service provides context-aware answers about benefits policies without requiring the LLM to memorize documentation:

```
Admin uploads "dental_plans.md"
    │
    ▼
[ Chunker ]  ──>  Split into 512-token chunks with 50-token overlap
    │
    ▼
[ Ollama nomic-embed-text ]  ──>  Generate 768-dim vector per chunk
    │
    ▼
[ PostgreSQL pgvector ]  ──>  Store with IVFFlat cosine similarity index
```

At query time:
1. User query is embedded into a 768-dim vector
2. pgvector finds the top-k most similar chunks (cosine similarity)
3. Chunks are injected into the LLM prompt as system context
4. LLM answers using the retrieved context

**Seeded with 16 documents** across 5 categories:
- **Policy**: eligibility rules, open enrollment, life events, COBRA
- **Plan**: medical, dental, vision, life insurance details
- **FAQ**: enrollment FAQ, claims FAQ
- **Compliance**: HIPAA, ACA, ERISA, Section 125
- **Process**: enrollment workflow, admin guide

---

## Governance and Compliance

Every AI agent action passes through the Governance Service before reaching the user:

### Policy Engine

10 YAML-driven rules with declarative conditions and effects:

```yaml
# Example: auto-redact PII in responses
- name: pii_redaction
  conditions:
    - field: pii_detected
      operator: equals
      value: true
  effect: redact
  priority: 1
```

**6 condition operators**: `equals`, `not_equals`, `greater_than`, `less_than`, `contains`, `in`
**5 effects**: `allow`, `deny`, `redact`, `log`, `require_approval`

### PII Detection

Regex-based detection for 6 types with automatic redaction:
- SSN (`\d{3}-\d{2}-\d{4}`)
- Email addresses
- Phone numbers
- Credit card numbers
- Dates of birth
- Physical addresses

### Risk Scoring

Multi-factor model that determines whether an action needs human approval:

| Factor | Weight |
|--------|--------|
| Action type | 0.1 (read) to 0.8 (delete) |
| PII present | +0.4 |
| Number of tool calls | +0.1 per tool |
| Data sensitivity | +0.2 (employee data) |
| User role | modifier |

Actions scoring above the critical threshold are routed to the **Escalation Agent** for human approval (30-minute timeout, auto-expiration).

### Audit Trail

Append-only PostgreSQL table with **mutation-prevention triggers** — rows cannot be updated or deleted after insertion. Every AI decision, tool call, policy evaluation, and risk score is recorded.

---

## Security Hardening (6 Layers)

| Layer | What It Does | Details |
|-------|-------------|---------|
| **Input Guardrails** | Block prompt injection and harmful input | 26 injection patterns, 8 harmful patterns, unicode normalization, leet-speak decoding |
| **System Prompt Hardening** | Prevent persona hijacking | Prose-based identity, off-topic deflection, persona permanence |
| **Output Filtering** | Prevent data leakage | System prompt leak detection, UUID stripping, email redaction |
| **Rate Limiting** | Prevent abuse | Per-IP sliding window (20 RPM default) |
| **Audit Logging** | Full traceability | Structured JSON events for all security-relevant actions |
| **RAG Sanitization** | Protect the knowledge base | Strips injection patterns from ingested documents |

---

## Evaluation Framework

Custom evaluation system for measuring and maintaining agent quality:

| Evaluator | What It Measures |
|-----------|-----------------|
| **Accuracy** | Correct agent routing + expected tool calls |
| **Relevance** | Response quality scored by LLM-as-judge |
| **Safety** | Resistance to guardrail bypass attempts |
| **Latency** | Response time vs. configurable threshold |
| **Cost** | Token usage efficiency |
| **Faithfulness** | Whether the response is grounded in RAG context |

- **45 golden test cases** across 3 datasets: enrollment queries, policy questions, adversarial/security tests
- **4 named experiments**: `enrollment_accuracy`, `knowledge_quality`, `security_audit`, `full_suite`
- **A/B testing** between model versions with per-evaluator comparison
- **CI integration** — evaluation runs on every PR, regressions block merge

---

## Observability

### Prometheus Metrics (9 Custom)

| Metric | Type | What It Tracks |
|--------|------|---------------|
| `agent_request_duration_seconds` | Histogram | End-to-end latency per request |
| `agent_request_total` | Counter | Total requests by agent and status |
| `agent_tool_call_total` | Counter | Tool invocations by tool name |
| `agent_token_usage_total` | Counter | LLM tokens (input + output) |
| `agent_guardrail_trigger_total` | Counter | Security guardrail activations |
| `agent_governance_decision_total` | Counter | Policy decisions (allow/deny/redact) |
| `rag_search_duration_seconds` | Histogram | Knowledge Service search latency |
| `pii_detection_total` | Counter | PII detections by type |
| `agent_cost_usd` | Gauge | Estimated LLM inference cost |

### Grafana Dashboard

Pre-configured 9-panel dashboard with request rate, P95 latency, tool call distribution, token usage, guardrail triggers, PII detections, governance decisions, RAG search performance, and cost tracking. Embedded directly in the frontend UI.

### Java Service Metrics

Both Spring Boot services expose Micrometer metrics via `/actuator/prometheus`, scraped by Prometheus alongside the Python services.

---

## Quick Start

**Prerequisites:** Java 17+, Docker, Node.js 18+, Python 3.11+, [Ollama](https://ollama.com)

```bash
# Clone
git clone https://github.com/skbcoder/employee-benefits-platform.git
cd employee-benefits-platform

# Start core services only (PostgreSQL + Enrollment + Processing)
./scripts/run-local.sh

# Start core + AI platform
./scripts/run-local.sh --with-ai

# Start core + frontend
./scripts/run-local.sh --with-ui

# Start everything
./scripts/run-local.sh --all
```

### First-Time AI Setup

```bash
# Pull LLM models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Set up Python environments + seed knowledge base
cd services/ai-platform && ./scripts/setup.sh
```

### Verify It Works

```bash
# Health checks
curl http://localhost:8080/actuator/health   # Enrollment Service
curl http://localhost:8081/actuator/health   # Processing Service
curl http://localhost:8200/api/ai/health     # AI Gateway
curl http://localhost:8400/health            # Orchestrator

# Submit a test enrollment
curl -X POST http://localhost:8080/api/enrollments \
  -H "Content-Type: application/json" \
  -d '{
    "employeeId": "E12345",
    "employeeName": "Jane Doe",
    "employeeEmail": "jane@company.com",
    "selections": [
      { "type": "medical", "plan": "gold" },
      { "type": "dental", "plan": "basic" }
    ]
  }'

# Ask the AI chatbot
curl -X POST http://localhost:8200/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What dental plans are available?"}'
```

### Monitoring

```bash
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3001 (admin/benefits)
# Also embedded in the frontend: Governance > Usage & Cost tab
```

For the full setup guide with troubleshooting, see [docs/local-setup.md](docs/local-setup.md).

---

## Services

| Service | Port | Tech | Role |
|---------|------|------|------|
| **Enrollment Service** | 8080 | Spring Boot / Java 17 | Enrollment REST API, outbox dispatcher, Prometheus metrics |
| **Processing Service** | 8081 | Spring Boot / Java 17 | Event consumer, inbox idempotency, async processing |
| **AI Gateway** | 8200 | FastAPI / Python | Chat endpoint, input guardrails, orchestrator delegation |
| **Orchestrator** | 8400 | FastAPI / LangGraph | Multi-agent routing, 6 specialist agents, quality gates |
| **MCP Server** | 8100 | Python / MCP SDK | 7 benefits API tools via SSE transport |
| **Knowledge Service** | 8300 | FastAPI / pgvector | Document ingestion, 768-dim embeddings, semantic search |
| **Governance Service** | 8500 | FastAPI / Python | 10 YAML policies, PII detection, audit trail, risk scoring |
| **Evaluation Service** | 8600 | FastAPI / Python | 6 evaluators, 45 golden test cases, A/B testing |
| **Frontend** | 3000 | Next.js 16 / React 19 | Enrollment UI, governance dashboard, MCP tool explorer, AI chatbot |
| **PostgreSQL** | 55432 | PostgreSQL 16 + pgvector | 6 schemas, Flyway migrations, append-only audit trail |
| **Ollama** | 11434 | llama3.1:8b + nomic-embed-text | Local LLM inference and embedding generation |
| **Prometheus** | 9090 | Prometheus v2.51 | Metrics scraping (15s interval, 5 service targets) |
| **Grafana** | 3001 | Grafana 10.4 | Pre-configured 9-panel dashboard, embedded in frontend |

---

## Frontend

| Page | What You Can Do |
|------|-----------------|
| **Home** | See live health status of all 13 services, enrollment lifecycle counts, quick-action cards |
| **Enrollment** | Submit new enrollments and look up status (tabbed view), inline validation |
| **Governance** | Browse audit trail (filterable, expandable), manage approvals, view compliance reports, edit policies, monitor usage and cost (embedded Grafana) |
| **Architecture** | Interactive architecture diagrams: deployment topology, LangGraph orchestration flow, agentic AI data flow, database schema, cloud evolution |
| **MCP Tools** | Browse all 7 MCP tools, fill in parameters, execute them interactively, see raw JSON responses |
| **AI Chatbot** | Floating widget on every page. Agent badges show which specialist handled the query. Markdown tables, confidence indicators, risk scores. |

---

## Infrastructure

### Docker Compose Profiles

```bash
docker compose -f infrastructure/docker-compose.yml up                       # Core only
docker compose -f infrastructure/docker-compose.yml --profile ai up          # + AI platform
docker compose -f infrastructure/docker-compose.yml --profile monitoring up   # + Prometheus + Grafana
docker compose -f infrastructure/docker-compose.yml --profile all up         # Everything
```

### Terraform (AWS)

5 modules for full AWS deployment:

```bash
cd infrastructure/terraform
terraform init && terraform plan -var-file=env/dev.tfvars
```

| Module | Resources |
|--------|-----------|
| **networking** | VPC (2 AZs), public/private subnets, NAT gateway, security groups |
| **database** | RDS PostgreSQL 16 with pgvector extension |
| **messaging** | EventBridge bus + SQS queues (replaces HTTP publisher) |
| **ecs** | ECS Fargate clusters for all services, ECR repos, Bedrock IAM |
| **observability** | CloudWatch dashboards, alarms, Secrets Manager |

### CI/CD (GitHub Actions)

4-job pipeline:

1. **Java Build & Test** — Maven verify with PostgreSQL service container
2. **Python Tests** — Orchestrator (39) + Governance (44) + Evaluation (16) + Observability (15) = **114 tests**
3. **Frontend Build** — Next.js TypeScript compilation
4. **Docker Build** — All 8 service Dockerfiles verified

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Java 17, Spring Boot 3.3.6, JPA/Hibernate, Flyway, Micrometer, Maven |
| **AI Orchestration** | Python 3.11, FastAPI, LangGraph, Ollama / AWS Bedrock |
| **Knowledge** | pgvector, nomic-embed-text (768-dim), semantic chunking (512 tokens, 50 overlap), cosine similarity |
| **Governance** | YAML policy engine (6 operators, 5 effects), PII regex detection, multi-factor risk scoring |
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4, react-markdown, remark-gfm |
| **Monitoring** | Prometheus v2.51, Grafana 10.4, structured JSON logging, CloudWatch |
| **Infrastructure** | Docker Compose (13 services), Terraform (5 modules), GitHub Actions (4 jobs) |
| **Database** | PostgreSQL 16, pgvector, 6 schemas (`enrollment`, `processing`, `messaging`, `knowledge`, `governance`, `orchestration`) |

---

## Project Structure

```
.
├── services/
│   ├── enrollment-service/       # Spring Boot: enrollment REST API + outbox dispatcher
│   ├── processing-service/       # Spring Boot: event consumer + inbox idempotency
│   ├── shared-model/             # Shared DTOs + Flyway migrations (V1-V3)
│   └── ai-platform/
│       ├── ai-gateway/           # Chat endpoint, guardrails, orchestrator delegation
│       ├── orchestrator/         # LangGraph multi-agent engine (6 specialist nodes)
│       ├── mcp-server/           # 7 MCP tools wrapping benefits REST APIs
│       ├── knowledge-service/    # RAG: chunking, embedding, pgvector search
│       │   └── seed-data/        # 16 benefits documents across 5 categories
│       ├── governance/           # Policy engine, PII detection, audit trail
│       │   └── policies/         # 3 YAML policy files (10 rules total)
│       ├── evaluation/           # 6 evaluators, 45 test cases, A/B testing
│       │   └── datasets/         # 3 golden datasets (enrollment, policy, adversarial)
│       └── observability/        # Shared Prometheus metrics + structured logging
├── frontend/                     # Next.js 16: enrollment, governance, architecture, MCP tools
├── infrastructure/
│   ├── docker-compose.yml        # 13 services with profiles (ai, monitoring, all)
│   ├── monitoring/               # Prometheus config + Grafana dashboard JSON
│   └── terraform/                # 5 modules (networking, database, ecs, messaging, observability)
├── docs/                         # Architecture, setup, security, AWS documentation
├── scripts/
│   ├── setup.sh                  # One-time prerequisite setup
│   └── run-local.sh              # Quick-start (--with-ai, --with-ui, --all)
├── .github/workflows/ci.yml     # 4-job CI pipeline (114 tests)
└── LICENSE                       # Apache License 2.0
```

---

## Cloud Evolution

| Phase | Status | What Changes |
|-------|--------|-------------|
| **Local Development** | Done | HTTP publisher, Docker Compose, Ollama, local PostgreSQL |
| **AI Orchestration** | Done | Multi-agent LangGraph, governance, evaluation, observability |
| **Messaging** | Planned | EventBridge + SQS replaces HTTP publisher adapter |
| **Managed Infrastructure** | Planned | RDS, ECS Fargate, Bedrock replaces Ollama |
| **Saga Orchestration** | Planned | Long-running multi-step enrollment workflows |

See [docs/aws-architecture.md](docs/aws-architecture.md) for the full AWS architecture plan.

---

## Documentation

| Document | What It Covers |
|----------|---------------|
| [System Architecture](docs/system-architecture.md) | Full architecture with Mermaid diagrams, all service interactions |
| [AI Platform Architecture](services/ai-platform/docs/architecture.md) | Deep dive: MCP tools, agent loop, RAG pipeline, technology decisions |
| [Local Setup](docs/local-setup.md) | Step-by-step setup with troubleshooting |
| [AWS Architecture](docs/aws-architecture.md) | Cloud evolution: VPC, ECS Fargate, RDS, Bedrock |
| [AI Chatbot Hardening](docs/ai-chatbot-hardening.md) | 6-layer security deep dive |
| [AI Loopback Refinement](docs/ai-loopback-refinement.md) | RAG enrichment and quality gates |
| [Persistence](docs/persistence.md) | Schema design, migration strategy, data ownership |

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
