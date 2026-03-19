# AI Platform — Benefits Intelligence Layer

An AI-powered service layer that adds natural language interaction, intelligent automation, and context-aware decision making to the Employee Benefits Event Processing Platform.

## What This Does

- **MCP Server** (port 8100) — Exposes benefits enrollment APIs as MCP tools, enabling AI assistants (Claude Desktop, Claude Code, custom agents) to interact with enrollments via natural language.
- **AI Gateway** (port 8200) — Orchestrates conversations between users, Ollama (local LLM), MCP tools, and the RAG knowledge base. Runs agentic workflows for enrollment validation, benefits advising, and compliance checking.
- **Knowledge Service** (port 8300) — RAG pipeline that ingests benefits policy documents, generates embeddings via Ollama, stores them in pgvector, and provides semantic search for context-aware AI responses.

## Architecture

```
User ──▶ AI Gateway ──▶ Ollama (local LLM)
              │
              ├──▶ MCP Server ──▶ Benefits APIs (enrollment:8080, processing:8081)
              │
              └──▶ Knowledge Service ──▶ pgvector (PostgreSQL)
```

All LLM inference runs locally via **Ollama** — no external API keys, no data leaves your machine.

For detailed architecture, technology decisions, and design rationale, see [docs/architecture.md](docs/architecture.md).

## Prerequisites

- Python 3.11+
- Ollama (installed and running)
- PostgreSQL 16 with pgvector extension
- Benefits Platform services running (enrollment:8080, processing:8081)

## Quick Start

```bash
# 1. Setup (install deps, pull Ollama models, create DB schema)
./scripts/setup.sh

# 2. Start all services
./scripts/run-local.sh
```

### Manual Start

```bash
# Pull required Ollama models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Start each service (separate terminals)
cd mcp-server && pip install -r requirements.txt && uvicorn src.main:app --port 8100
cd ai-gateway && pip install -r requirements.txt && uvicorn src.main:app --port 8200
cd knowledge-service && pip install -r requirements.txt && uvicorn src.main:app --port 8300
```

## Tech Stack

- **Python 3.11+** / **FastAPI** — async web framework with automatic OpenAPI docs
- **Ollama** — local LLM inference (`llama3.1:8b` for chat, `nomic-embed-text` for embeddings)
- **MCP SDK** (`mcp` Python package) — Model Context Protocol for tool exposure
- **pgvector** — vector similarity search in PostgreSQL
- **httpx** — async HTTP client for service-to-service communication
- **Pydantic** — data validation and serialization

## Port Allocation

| Service | Port | Description |
|---------|------|-------------|
| MCP Server | 8100 | MCP tool definitions and execution |
| AI Gateway | 8200 | Chat API, agent workflows, orchestration |
| Knowledge Service | 8300 | Document ingestion, RAG search |
| Ollama | 11434 | LLM inference (external dependency) |
