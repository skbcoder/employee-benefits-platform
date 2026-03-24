export type ServiceStatus = "healthy" | "degraded" | "down" | "idle";

export interface ServiceNode {
  id: string;
  label: string;
  subtitle: string;
  port: number | null;
  description: string;
  tech: string;
  schemas?: string[];
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  group: "frontend" | "backend" | "ai" | "infra";
  status: ServiceStatus;
  endpoints?: string[];
  config?: Record<string, string>;
}

export interface Connection {
  from: string;
  to: string;
  label: string;
  style: "solid" | "dashed";
  protocol: string;
}

export interface FlowStep {
  id: string;
  title: string;
  desc: string;
  active: string[];
  activeConns: number[];
  status: string;
}

export const SERVICES: ServiceNode[] = [
  {
    id: "user",
    label: "User / Browser",
    subtitle: "Client",
    port: null,
    description: "End user accessing the enrollment platform through a web browser.",
    tech: "Browser",
    x: 420,
    y: 20,
    w: 160,
    h: 52,
    color: "#94a3b8",
    group: "frontend",
    status: "healthy",
  },
  {
    id: "frontend",
    label: "Next.js Frontend",
    subtitle: "UI + API Routes",
    port: 3000,
    description:
      "Enrollment submission UI, status dashboard, AI chatbot floating widget with markdown rendering (react-markdown + remark-gfm). API route handlers proxy to AI Gateway with configurable timeouts. Rewrites proxy enrollment and processing APIs transparently.",
    tech: "Next.js 16.1.6 · React 19.2.3 · Tailwind CSS 4",
    x: 370,
    y: 100,
    w: 260,
    h: 58,
    color: "#3b82f6",
    group: "frontend",
    status: "healthy",
    endpoints: [
      "/ — Home dashboard",
      "/enroll — New enrollment form",
      "/status — Check enrollment status",
      "/mcp-tools — MCP tool explorer",
      "/architecture — This page",
      "/api/ai/chat — Proxy → AI Gateway (120s timeout)",
      "/api/ai/health — Proxy → AI Gateway (10s timeout)",
      "/api/ai/tools — Proxy → AI Gateway (10s timeout)",
      "/api/ai/tools/execute — Proxy → AI Gateway (30s timeout)",
    ],
    config: {
      "ENROLLMENT_API": "http://localhost:8080",
      "PROCESSING_API": "http://localhost:8081",
      "AI_GATEWAY_API": "http://localhost:8200",
    },
  },
  {
    id: "enrollment",
    label: "Enrollment Service",
    subtitle: "REST API + Outbox Dispatcher",
    port: 8080,
    description:
      "Owns enrollment submission, status lookup, and the durable outbox dispatcher. Writes enrollment records, benefit selections, and outbox events in a single transaction. The scheduled dispatcher claims pending outbox rows using FOR UPDATE SKIP LOCKED, publishes via a transport-specific adapter (HTTP or EventBridge), and handles retries with configurable backoff.",
    tech: "Spring Boot 3.3.6 · Java 17 · JPA/Hibernate · Flyway",
    schemas: ["enrollment.enrollment_record", "enrollment.enrollment_selection", "messaging.outbox_event"],
    x: 140,
    y: 240,
    w: 260,
    h: 58,
    color: "#22c55e",
    group: "backend",
    status: "healthy",
    endpoints: [
      "POST /api/enrollments — Submit new enrollment",
      "GET  /api/enrollments/{enrollmentId} — Get by ID",
      "GET  /api/enrollments/by-employee/{employeeId}",
      "GET  /api/enrollments/by-name/{employeeName}",
      "GET  /api/enrollments/by-status?status=SUBMITTED|PROCESSING|COMPLETED",
      "GET  /actuator/health",
    ],
    config: {
      "Outbox poll interval": "2,000ms fixed delay",
      "Outbox batch size": "10 events/cycle",
      "Claim TTL": "15,000ms",
      "Retry delay": "5,000ms",
      "Publisher transport": "http (configurable: eventbridge)",
      "JPA DDL mode": "validate (Flyway manages schema)",
      "Open-in-view": "disabled",
    },
  },
  {
    id: "processing",
    label: "Processing Service",
    subtitle: "Event Consumer + Inbox",
    port: 8081,
    description:
      "Accepts internal enrollment events, enforces at-most-once processing through inbox idempotency (primary key dedup), creates processing records, and delegates to an async worker for completion. The inbox pattern guarantees that duplicate deliveries from the outbox dispatcher are safely ignored.",
    tech: "Spring Boot 3.3.6 · Java 17 · JPA/Hibernate · @Async",
    schemas: ["processing.enrollment_processing_record", "messaging.inbox_message"],
    x: 600,
    y: 240,
    w: 260,
    h: 58,
    color: "#22c55e",
    group: "backend",
    status: "healthy",
    endpoints: [
      "POST /internal/enrollment-events — Receive from outbox",
      "GET  /api/processed-enrollments/{enrollmentId}",
      "GET  /api/processed-enrollments/by-employee/{employeeId}",
      "GET  /api/processed-enrollments/by-name/{employeeName}",
      "GET  /actuator/health",
    ],
    config: {
      "Async executor": "Spring default ThreadPoolTaskExecutor",
      "Simulated processing": "500ms (placeholder for real logic)",
      "Idempotency": "inbox_message PK = event_id",
      "JPA DDL mode": "validate",
    },
  },
  {
    id: "ai-gateway",
    label: "AI Gateway",
    subtitle: "Agent Loop + RAG + MCP",
    port: 8200,
    description:
      "Orchestrates LLM calls with a two-phase agent loop. Phase 1: RAG search injects knowledge context. Phase 2: Classifies query as knowledge-only (direct LLM response) or data-requiring (tool execution via MCP). Tool results are post-processed to strip internal UUIDs. Session-based conversation history. Max 10 iterations to prevent runaway loops.",
    tech: "Python · FastAPI · Ollama client",
    x: 100,
    y: 400,
    w: 200,
    h: 58,
    color: "#a855f7",
    group: "ai",
    status: "idle",
    endpoints: [
      "POST /api/ai/chat — Chat completion",
      "GET  /api/ai/health — Health check",
    ],
    config: {
      "LLM model": "llama3.1:8b",
      "Max agent iterations": "10",
      "HTTP timeout (RAG)": "30s",
      "HTTP timeout (MCP)": "30s",
      "Tool keywords": "enrollment, status, employee id, ...",
    },
  },
  {
    id: "mcp-server",
    label: "MCP Server",
    subtitle: "Tool Definitions + SSE",
    port: 8100,
    description:
      "Exposes benefits APIs as 7 MCP-compatible tools for AI clients. SSE transport for remote clients (Claude Desktop, Claude Code). Stateless — no database, no LLM calls. Acts as a typed adapter between AI tool calling and REST APIs.",
    tech: "Python · MCP SDK · Starlette SSE",
    x: 340,
    y: 400,
    w: 200,
    h: 58,
    color: "#a855f7",
    group: "ai",
    status: "idle",
    endpoints: [
      "GET  /mcp/sse — SSE connection",
      "POST /mcp/messages/ — MCP protocol",
      "7 tools: submit, get, list, status, processing",
    ],
    config: {
      "Transport": "SSE (Server-Sent Events)",
      "Benefit types": "medical, dental, vision, life",
    },
  },
  {
    id: "knowledge",
    label: "Knowledge Service",
    subtitle: "RAG + Embeddings",
    port: 8300,
    description:
      "Document ingestion with word-based chunking (512 tokens, 50 token overlap). Generates embeddings via Ollama nomic-embed-text (768-dim vectors). Semantic search uses cosine similarity over pgvector. Category-based filtering: policy, plan, faq, compliance, process.",
    tech: "Python · FastAPI · SQLAlchemy · pgvector · asyncpg",
    schemas: ["knowledge.document", "knowledge.document_chunk (vector(768))"],
    x: 580,
    y: 400,
    w: 200,
    h: 58,
    color: "#a855f7",
    group: "ai",
    status: "idle",
    endpoints: [
      "POST /api/knowledge/search — Semantic search",
      "POST /api/knowledge/documents — Ingest document",
    ],
    config: {
      "Chunk size": "512 tokens",
      "Chunk overlap": "50 tokens",
      "Embedding model": "nomic-embed-text (768-dim)",
      "Similarity": "Cosine distance",
      "DB pool": "5 connections, max overflow 10",
      "Top-K default": "5 results",
    },
  },
  {
    id: "orchestrator",
    label: "Orchestrator",
    subtitle: "Multi-Agent Router",
    port: 8400,
    description:
      "Routes user requests to specialized agents (enrollment, advisor, compliance, escalation) using keyword or LLM-based classification. Enforces quality gates with heuristic scoring, manages token budgets, and coordinates with Governance for policy checks before returning responses.",
    tech: "Python · FastAPI · YAML policies",
    x: 100,
    y: 480,
    w: 200,
    h: 58,
    color: "#a855f7",
    group: "ai",
    status: "idle",
    endpoints: [
      "POST /api/orchestrate/chat — Orchestrated chat",
      "GET  /api/orchestrate/agents — List agents",
      "GET  /api/orchestrate/health — Health check",
    ],
    config: {
      "Routing": "Keyword (fast) or LLM (~200ms)",
      "Quality gate": "Heuristic scoring <1ms",
      "Token budget": "Per-request enforcement",
    },
  },
  {
    id: "governance",
    label: "Governance",
    subtitle: "Audit & Policy Engine",
    port: 8500,
    description:
      "Provides audit trail logging, PII detection (regex-based), policy enforcement via YAML rules, approval workflows for high-risk actions, and usage budget tracking. All AI interactions are logged for compliance.",
    tech: "Python · FastAPI · YAML policies",
    x: 340,
    y: 480,
    w: 200,
    h: 58,
    color: "#a855f7",
    group: "ai",
    status: "idle",
    endpoints: [
      "GET  /api/governance/audit — Audit trail",
      "GET  /api/governance/approvals — Pending approvals",
      "POST /api/governance/approvals/:id/approve",
      "POST /api/governance/approvals/:id/deny",
    ],
    config: {
      "PII detection": "Regex-based <1ms",
      "Policy engine": "<1ms for 10 YAML rules",
      "Audit storage": "PostgreSQL governance schema",
    },
  },
  {
    id: "evaluation",
    label: "Evaluation",
    subtitle: "Quality & Benchmarks",
    port: 8600,
    description:
      "Scores AI response quality using heuristic metrics (relevance, completeness, accuracy). Runs benchmark suites against test datasets. Provides evaluation APIs for continuous quality monitoring.",
    tech: "Python · FastAPI",
    x: 580,
    y: 480,
    w: 200,
    h: 58,
    color: "#a855f7",
    group: "ai",
    status: "idle",
    endpoints: [
      "POST /api/eval/score — Score a response",
      "POST /api/eval/benchmark — Run benchmark suite",
      "GET  /api/eval/health — Health check",
    ],
    config: {
      "Scoring": "Heuristic metrics <1ms",
      "Benchmarks": "Test dataset evaluation",
    },
  },
  {
    id: "ollama",
    label: "Ollama",
    subtitle: "Local LLM Runtime",
    port: 11434,
    description:
      "Runs local LLM models. llama3.1:8b for chat completions and tool calling. nomic-embed-text for embedding generation (768-dim vectors). Provides OpenAI-compatible API.",
    tech: "llama3.1:8b · nomic-embed-text",
    x: 820,
    y: 400,
    w: 150,
    h: 58,
    color: "#f97316",
    group: "infra",
    status: "idle",
  },
  {
    id: "postgres",
    label: "PostgreSQL 16 + pgvector",
    subtitle: "Single DB, Multi-Schema",
    port: 5433,
    description:
      "Single database (employee_benefits_platform) with schema-per-bounded-context isolation. pgvector extension for embedding storage and cosine similarity search. Flyway manages migrations across all schemas from shared-model. Volume-backed for data persistence.",
    tech: "PostgreSQL 16 · pgvector · Flyway 3 migrations",
    schemas: [
      "enrollment (enrollment_record, enrollment_selection)",
      "processing (enrollment_processing_record)",
      "messaging (outbox_event, inbox_message)",
      "knowledge (document, document_chunk + vector(768))",
      "governance (audit_trail, approval_request, usage_budget)",
      "orchestration (saga_instance, saga_step — future)",
    ],
    x: 370,
    y: 600,
    w: 260,
    h: 58,
    color: "#0ea5e9",
    group: "infra",
    status: "healthy",
    config: {
      "Health check": "pg_isready, 5s interval, 12 retries",
      "Volume": "postgres_data (persistent)",
      "Extensions": "pgvector",
    },
  },
  {
    id: "prometheus",
    label: "Prometheus",
    subtitle: "Metrics Scraping",
    port: 9090,
    description:
      "Scrapes /metrics endpoints from all AI platform services (Orchestrator, AI Gateway, Governance) and /actuator/prometheus from Java services every 15 seconds. 7-day retention. Powers the Grafana dashboards.",
    tech: "Prometheus v2.51 · 15s scrape interval · 5 targets",
    x: 30,
    y: 600,
    w: 150,
    h: 58,
    color: "#e6522c",
    group: "infra",
    status: "idle",
    endpoints: ["/-/healthy", "/api/v1/query", "/api/v1/targets"],
    config: {
      "Scrape interval": "15s",
      "Retention": "7 days",
      "Targets": "orchestrator, ai-gateway, governance, enrollment, processing",
    },
  },
  {
    id: "grafana",
    label: "Grafana",
    subtitle: "Dashboards",
    port: 3001,
    description:
      "Pre-configured dashboard 'AI Platform - Benefits Orchestrator' with 9 panels: request rate, p95 latency, tool calls, token usage, guardrail triggers, PII detections, governance decisions, RAG search duration. Embedded in the frontend UI via /grafana/ proxy.",
    tech: "Grafana 10.4 · Prometheus datasource · Anonymous viewer access",
    x: 670,
    y: 600,
    w: 150,
    h: 58,
    color: "#f46800",
    group: "infra",
    status: "idle",
    endpoints: ["/grafana/api/health", "/grafana/d/benefits-ai-platform"],
    config: {
      "Auth": "Anonymous viewer + admin/benefits",
      "Embedding": "Enabled (allow_embedding=true)",
      "Proxy": "Next.js /grafana/* → localhost:3001/grafana/*",
    },
  },
];

export const CONNECTIONS: Connection[] = [
  { from: "user", to: "frontend", label: "HTTPS", style: "solid", protocol: "HTTPS" },
  { from: "frontend", to: "enrollment", label: "REST (rewrite proxy)", style: "solid", protocol: "HTTP" },
  { from: "frontend", to: "processing", label: "REST (rewrite proxy)", style: "solid", protocol: "HTTP" },
  { from: "frontend", to: "ai-gateway", label: "Proxy /api/ai/* (120s)", style: "solid", protocol: "HTTP" },
  { from: "enrollment", to: "processing", label: "Outbox → HTTP Publish", style: "solid", protocol: "HTTP POST" },
  { from: "enrollment", to: "postgres", label: "enrollment + messaging", style: "solid", protocol: "JDBC" },
  { from: "processing", to: "postgres", label: "processing + messaging", style: "solid", protocol: "JDBC" },
  { from: "ai-gateway", to: "ollama", label: "Chat completions", style: "solid", protocol: "HTTP" },
  { from: "ai-gateway", to: "enrollment", label: "Benefits API proxy", style: "dashed", protocol: "HTTP" },
  { from: "ai-gateway", to: "processing", label: "Benefits API proxy", style: "dashed", protocol: "HTTP" },
  { from: "ai-gateway", to: "knowledge", label: "RAG search (30s)", style: "solid", protocol: "HTTP" },
  { from: "mcp-server", to: "enrollment", label: "MCP tool calls", style: "dashed", protocol: "HTTP" },
  { from: "mcp-server", to: "processing", label: "MCP tool calls", style: "dashed", protocol: "HTTP" },
  { from: "knowledge", to: "ollama", label: "Embeddings", style: "solid", protocol: "HTTP" },
  { from: "knowledge", to: "postgres", label: "knowledge (pgvector)", style: "solid", protocol: "asyncpg" },
  { from: "ai-gateway", to: "orchestrator", label: "Delegates routing", style: "solid", protocol: "HTTP" },
  { from: "orchestrator", to: "knowledge", label: "RAG context", style: "dashed", protocol: "HTTP" },
  { from: "orchestrator", to: "governance", label: "Policy checks", style: "solid", protocol: "HTTP" },
  { from: "prometheus", to: "orchestrator", label: "Scrape /metrics", style: "dashed", protocol: "HTTP" },
  { from: "prometheus", to: "ai-gateway", label: "Scrape /metrics", style: "dashed", protocol: "HTTP" },
  { from: "prometheus", to: "governance", label: "Scrape /metrics", style: "dashed", protocol: "HTTP" },
  { from: "prometheus", to: "enrollment", label: "Scrape /actuator/prometheus", style: "dashed", protocol: "HTTP" },
  { from: "prometheus", to: "processing", label: "Scrape /actuator/prometheus", style: "dashed", protocol: "HTTP" },
  { from: "grafana", to: "prometheus", label: "PromQL queries", style: "solid", protocol: "HTTP" },
  { from: "frontend", to: "grafana", label: "Embedded dashboard", style: "dashed", protocol: "HTTP proxy" },
];

export const FLOW_STEPS: FlowStep[] = [
  {
    id: "submit",
    title: "1. Submit",
    desc: "Client POST /api/enrollments → Enrollment Service saves enrollment_record + enrollment_selection + outbox_event in single TX → returns 202 Accepted (SUBMITTED)",
    active: ["user", "frontend", "enrollment", "postgres"],
    activeConns: [0, 1, 5],
    status: "SUBMITTED",
  },
  {
    id: "dispatch",
    title: "2. Dispatch",
    desc: "Scheduled dispatcher (2s interval) claims up to 10 pending outbox rows using FOR UPDATE SKIP LOCKED with 15s claim TTL → publishes via HTTP adapter",
    active: ["enrollment", "postgres"],
    activeConns: [5],
    status: "SUBMITTED → dispatching",
  },
  {
    id: "publish",
    title: "3. Publish",
    desc: "Publisher POST /internal/enrollment-events → Processing Service saves inbox_message (idempotency key = event_id) + enrollment_processing_record → Dispatcher marks outbox PUBLISHED, enrollment PROCESSING",
    active: ["enrollment", "processing", "postgres"],
    activeConns: [4, 5, 6],
    status: "PROCESSING",
  },
  {
    id: "process",
    title: "4. Complete",
    desc: "@Async worker processes enrollment (500ms simulated) → marks processing record COMPLETED, inbox message PROCESSED",
    active: ["processing", "postgres"],
    activeConns: [6],
    status: "COMPLETED",
  },
  {
    id: "ai-chat",
    title: "5. AI Chat",
    desc: "User message → Frontend proxies to AI Gateway → Phase 1: RAG search (Knowledge Service → Ollama embeddings → pgvector cosine search) → Phase 2: LLM decides knowledge-only or tool-call → Tool execution hits Benefits APIs → UUID stripping → response",
    active: ["user", "frontend", "ai-gateway", "knowledge", "ollama", "enrollment"],
    activeConns: [0, 3, 7, 10, 13, 8],
    status: "AI Flow",
  },
];
