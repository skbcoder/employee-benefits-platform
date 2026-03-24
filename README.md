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

An enterprise-grade platform for processing employee benefit enrollments, featuring **multi-agent AI orchestration**, **governance and compliance controls**, **evaluation frameworks**, and **production observability** — all built on event-driven microservices with a transactional outbox/inbox messaging pattern.

## Platform Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js 16)                             │
│  Enrollment UI · Status Dashboard · AI Chatbot · Governance Dashboard     │
│  Architecture Diagrams · Embedded Grafana Dashboards                      │
└────────┬──────────────────────┬──────────────────────┬────────────────────┘
         │                      │                      │
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│  Enrollment     │    │  AI Gateway     │    │  Governance     │
│  Service :8080  │    │  :8200          │    │  Service :8500  │
│  REST + Outbox  │    │  Chat + Proxy   │    │  Policy + Audit │
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

## Why This Architecture

Employee benefit enrollments are high-stakes, low-tolerance-for-loss transactions. This platform treats every enrollment as a durable event:

- **No silent failures** — the transactional outbox guarantees that every accepted enrollment is eventually delivered downstream, even if the processing service is temporarily unavailable
- **Idempotent processing** — the inbox pattern ensures duplicate deliveries are safely ignored
- **Cloud-ready boundaries** — the local HTTP transport can be swapped for EventBridge + SQS without changing the API, data model, or processing logic
- **Multi-agent AI** — a LangGraph orchestrator routes queries to specialist agents (enrollment, benefits advisor, compliance) with conversation context
- **Enterprise governance** — every AI action is audited, risk-scored, and policy-checked before reaching the user
- **Production observability** — Prometheus metrics, Grafana dashboards, and structured logging across all services

## Quick Start

**Prerequisites:** Java 17+, Docker

```bash
# 1. Clone
git clone https://github.com/skbcoder/employee-benefits-platform.git
cd employee-benefits-platform

# 2. Setup (detects/installs prerequisites, creates .env, builds)
./scripts/setup.sh

# 3. Start core services
./scripts/run-local.sh

# 4. Start everything (AI + Frontend + Monitoring)
./scripts/run-local.sh --all
```

Health checks:
```bash
curl http://localhost:8080/actuator/health   # Enrollment Service
curl http://localhost:8081/actuator/health   # Processing Service
curl http://localhost:8400/health            # Orchestrator
curl http://localhost:8500/health            # Governance
```

Submit a test enrollment:
```bash
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
```

### Monitoring Stack

```bash
# Start Prometheus + Grafana
docker compose -f infrastructure/docker-compose.yml up -d prometheus grafana

# Grafana: http://localhost:3001 (admin/benefits)
# Also embedded in the UI at: Governance → Usage & Cost tab
```

For the complete setup guide, see [docs/local-setup.md](docs/local-setup.md).

## Services

| Service | Port | Tech | Description |
|---------|------|------|-------------|
| **Enrollment Service** | 8080 | Spring Boot / Java 17 | Enrollment REST API, outbox dispatcher, Prometheus metrics |
| **Processing Service** | 8081 | Spring Boot / Java 17 | Event consumer, inbox idempotency, async processing |
| **AI Gateway** | 8200 | FastAPI / Python | Chat proxy, guardrails, orchestrator delegation |
| **Orchestrator** | 8400 | FastAPI / LangGraph | Multi-agent routing, tool calling, RAG, compliance checks |
| **MCP Server** | 8100 | Python / MCP SDK | 7 benefits API tools exposed via SSE transport |
| **Knowledge Service** | 8300 | FastAPI / pgvector | Document ingestion, semantic chunking, vector search |
| **Governance Service** | 8500 | FastAPI / Python | Policy engine, PII detection, audit trail, risk scoring |
| **Evaluation Service** | 8600 | FastAPI / Python | 6 evaluators, 45 golden test cases, A/B testing |
| **Frontend** | 3000 | Next.js 16 / React 19 | Enrollment UI, governance dashboard, architecture diagrams |
| **PostgreSQL** | 5433 | PostgreSQL 16 + pgvector | 6 schemas, Flyway migrations, append-only audit trail |
| **Ollama** | 11434 | llama3.1:8b | Local LLM for chat + nomic-embed-text for embeddings |
| **Prometheus** | 9090 | Prometheus v2.51 | Metrics scraping (15s interval, 5 service targets) |
| **Grafana** | 3001 | Grafana 10.4 | Pre-configured dashboard, embedded in frontend UI |

## Multi-Agent Orchestration (LangGraph)

The orchestrator replaces a single-agent chatbot with a multi-agent system:

```
User Query → Router → [Enrollment Agent | Benefits Advisor | Compliance Agent | Escalation]
                                    ↓
                              Synthesis Node
                         (merge + sanitize + table fix)
                                    ↓
                               Response
```

| Agent | Role | Tools / Data |
|-------|------|-------------|
| **Router** | Intent classification, delegation | Keyword match + LLM fallback, conversation history |
| **Enrollment** | CRUD operations on enrollments | 7 MCP tools, fabrication guard, plan-tier validation |
| **Benefits Advisor** | Plan/coverage Q&A via RAG | Knowledge Service vector search (16 docs, 45 chunks) |
| **Compliance** | PII detection, risk scoring | 6 PII types, multi-factor risk model, 10 YAML policies |
| **Escalation** | Human-in-the-loop | Approval queue, context preservation |
| **Synthesis** | Response post-processing | UUID/PII stripping, markdown table repair, output sanitization |

### Key Features
- **Context continuity** — router checks conversation history to maintain enrollment context across turns
- **Fabrication guard** — blocks the LLM from submitting enrollments with made-up employee data
- **Correct plan tiers** — medical (basic/silver/gold/platinum), dental (basic/premium), vision (basic/premium)
- **Markdown table repair** — fixes malformed GFM tables from small LLMs (missing separators, code fences)
- **Dual LLM provider** — Ollama (local) / AWS Bedrock (production) with config-based switching

## Governance & Compliance

Every AI agent action is monitored, scored, and enforced:

| Control | Implementation |
|---------|---------------|
| **Policy Engine** | 10 YAML-driven rules, 6 condition operators, 5 effects (allow/deny/redact/log/require_approval) |
| **PII Detection** | 6 types: SSN, email, phone, credit card, DOB, address. Auto-redaction in responses |
| **Risk Scoring** | Multi-factor: action type (0.1-0.8), PII (+0.4), tool count, data sensitivity |
| **Audit Trail** | Append-only PostgreSQL table with mutation-prevention triggers |
| **Approval Workflow** | Human-in-the-loop for critical-risk actions (30 min timeout, auto-expiration) |
| **Compliance Reports** | Risk distribution, policy triggers, violation history |

## Evaluation Framework

Custom evaluation system for measuring agent quality:

| Evaluator | What It Measures |
|-----------|-----------------|
| **Accuracy** | Correct agent routing + expected tool calls |
| **Relevance** | Response quality (LLM-as-judge) |
| **Safety** | Guardrail bypass resistance |
| **Latency** | Response time vs threshold |
| **Cost** | Token usage efficiency |
| **Faithfulness** | RAG grounding accuracy |

- **45 golden test cases** across 3 datasets (enrollment, policy, adversarial)
- **4 named experiments**: enrollment_accuracy, knowledge_quality, security_audit, full_suite
- **A/B testing** between model versions with per-evaluator comparison
- **CI integration** — eval runs on PR, regression blocks merge

## Security Hardening (6 Layers)

1. **Input Guardrails** — 26 injection patterns, 8 harmful patterns, unicode normalization, leet-speak decoding
2. **System Prompt Hardening** — prose-based identity, off-topic deflection, persona permanence
3. **Output Filtering** — system prompt leak detection, UUID stripping, email redaction
4. **Rate Limiting** — per-IP sliding window (20 RPM default)
5. **Audit Logging** — structured JSON events for all security-relevant actions
6. **RAG Sanitization** — strips injection patterns from knowledge base documents

## Observability

| Component | Details |
|-----------|---------|
| **Prometheus** | 9 custom metrics: request duration, tool calls, token usage, guardrails, governance, PII, RAG, cost |
| **Grafana** | Pre-configured dashboard with 9 panels, embedded in frontend via `/grafana/` proxy |
| **Java Metrics** | Micrometer + Prometheus registry on both Spring Boot services (`/actuator/prometheus`) |
| **Structured Logging** | JSON-formatted, CloudWatch-compatible, with service context and request correlation |
| **Cost Tracking** | Per-model Bedrock pricing (Haiku/Sonnet), daily summaries, token usage metrics |

## Frontend

| Page | Features |
|------|----------|
| **Home** | Live service health indicators, enrollment lifecycle with counts, quick-action cards |
| **Enrollment** | Combined enroll form + status lookup (tabbed), inline validation, refresh timestamps |
| **Governance** | 5 tabs: Audit Trail (filterable, expandable), Approvals, Compliance, Policies, Usage & Cost (Grafana) |
| **Architecture** | 5 tabs: Deployment (interactive SVG), Orchestration (LangGraph flow), Agentic AI, Data, Cloud |
| **MCP Tools** | Interactive tool explorer with parameter forms and execution |
| **AI Chatbot** | Floating widget, agent badges, confidence %, risk indicators, markdown tables |

## Infrastructure

### Docker Compose Profiles

```bash
docker compose -f infrastructure/docker-compose.yml up                       # Core only
docker compose -f infrastructure/docker-compose.yml --profile ai up          # + AI platform (6 services)
docker compose -f infrastructure/docker-compose.yml --profile monitoring up   # + Prometheus + Grafana
docker compose -f infrastructure/docker-compose.yml --profile all up         # Everything
```

### Terraform (AWS)

```bash
cd infrastructure/terraform
terraform init && terraform plan -var-file=env/dev.tfvars
```

Provisions: VPC (2 AZs), RDS PostgreSQL + pgvector, EventBridge + SQS, ECS Fargate (all services), ECR repos, Bedrock IAM, Secrets Manager, CloudWatch dashboards + alarms.

### CI/CD (GitHub Actions)

4-job pipeline:
1. **Java Build & Test** — Maven verify with PostgreSQL service container
2. **Python Tests** — Orchestrator (39), Governance (44), Evaluation (16), Observability (15) = **114 tests**
3. **Frontend Build** — Next.js TypeScript compilation
4. **Docker Build** — All 8 service Dockerfiles verified

## Project Structure

```
.
├── services/
│   ├── enrollment-service/       # Enrollment REST API, outbox dispatcher
│   ├── processing-service/       # Event consumer, inbox idempotency
│   ├── shared-model/             # Shared DTOs + Flyway migrations (V1–V3)
│   └── ai-platform/
│       ├── ai-gateway/           # Chat proxy, guardrails, orchestrator delegation
│       ├── orchestrator/         # LangGraph multi-agent engine (6 agents)
│       ├── mcp-server/           # Benefits APIs as MCP tools
│       ├── knowledge-service/    # RAG document store + pgvector search
│       ├── governance/           # Policy engine, PII detection, audit trail
│       ├── evaluation/           # 6 evaluators, 45 test cases, A/B testing
│       └── observability/        # Shared Prometheus metrics + structured logging
├── frontend/                     # Next.js 16 (modular: architecture, governance split)
├── infrastructure/
│   ├── docker-compose.yml        # 13 services with profiles (ai, monitoring, all)
│   ├── monitoring/               # Prometheus config + Grafana dashboards
│   ├── cloudformation/           # AWS CloudFormation templates
│   └── terraform/                # Modular Terraform (networking, database, ecs, messaging, observability)
├── docs/                         # Architecture, setup, security, AWS docs
├── scripts/
│   ├── setup.sh                  # One-time prerequisite setup
│   └── run-local.sh              # Quick-start (--with-ai, --with-ui, --all)
├── .github/workflows/ci.yml     # 4-job CI pipeline
├── .env.example                  # Environment variable template
├── CONTRIBUTING.md               # Contributor guidelines
└── LICENSE                       # Apache License 2.0
```

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Java 17, Spring Boot 3.3.6, JPA/Hibernate, Flyway, Micrometer, Maven |
| **AI Orchestration** | Python 3.11, FastAPI, LangGraph, Ollama / AWS Bedrock |
| **Knowledge** | pgvector, nomic-embed-text (768-dim), semantic chunking, cosine search |
| **Governance** | YAML policy engine, PII regex detection, multi-factor risk scoring |
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4, react-markdown |
| **Monitoring** | Prometheus, Grafana, structured JSON logging, CloudWatch |
| **Infrastructure** | Docker Compose, Terraform, CloudFormation, GitHub Actions |
| **Database** | PostgreSQL 16, pgvector, 6 schemas, append-only audit trail |

## Cloud Evolution

| Phase | Status | What Changes |
|-------|--------|-------------|
| **Local** | ✅ Done | HTTP publisher, Docker Compose, Ollama, local PostgreSQL |
| **Phase 1: Messaging** | Planned | EventBridge + SQS replaces HTTP publisher |
| **Phase 2: AI Orchestration** | ✅ Done | Multi-agent orchestrator, governance, evaluation, observability |
| **Phase 3: Managed Infra** | Planned | RDS, ECS Fargate, Bedrock replaces Ollama |
| **Phase 4: Orchestration** | Planned | Saga coordinator for multi-step enrollment workflows |

See [docs/aws-architecture.md](docs/aws-architecture.md) for the full AWS architecture.

## Documentation

| Document | Description |
|----------|-------------|
| [System Architecture](docs/system-architecture.md) | Full architecture with Mermaid diagrams |
| [Local Setup](docs/local-setup.md) | Step-by-step setup and troubleshooting |
| [AWS Architecture](docs/aws-architecture.md) | Cloud evolution plan, VPC design, ECS/Fargate |
| [AI Chatbot Hardening](docs/ai-chatbot-hardening.md) | 6-layer security deep dive |
| [AI Loopback Refinement](docs/ai-loopback-refinement.md) | RAG enrichment and quality gates |
| [Persistence](docs/persistence.md) | Schema design and migration strategy |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Roadmap

- [x] Core enrollment pipeline (outbox/inbox pattern)
- [x] Next.js frontend with enrollment UI
- [x] AI Platform — MCP Server, AI Gateway, Knowledge Service
- [x] AI chatbot with RAG, agent loop, and 6-layer security hardening
- [x] Semantic-aware document chunking + loopback refinement
- [x] Multi-agent LangGraph orchestrator (6 specialist agents)
- [x] Governance service (policy engine, PII detection, audit trail, risk scoring)
- [x] Evaluation framework (6 evaluators, 45 test cases, A/B testing)
- [x] Observability (Prometheus metrics, Grafana dashboards, structured logging)
- [x] Terraform IaC for full AWS deployment
- [x] CI/CD pipeline (Java + Python + Frontend + Docker, 114 tests)
- [x] Modular frontend (architecture + governance pages split into components)
- [ ] EventBridge + SQS publisher adapter
- [ ] Distributed tracing (OpenTelemetry / X-Ray)
- [ ] Saga orchestration for multi-step workflows
- [ ] AWS deployment (ECS Fargate, RDS, Bedrock)

## License

This project is licensed under the [Apache License 2.0](LICENSE).
