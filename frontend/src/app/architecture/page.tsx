"use client";

import { useState, useCallback, useRef } from "react";

/* ================================================================== */
/*  DATA MODEL                                                         */
/* ================================================================== */

type ServiceStatus = "healthy" | "degraded" | "down" | "idle";
type Tab = "diagram" | "details" | "performance" | "data" | "cloud";

interface ServiceNode {
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

interface Connection {
  from: string;
  to: string;
  label: string;
  style: "solid" | "dashed";
  protocol: string;
}

/* ================================================================== */
/*  SERVICE DEFINITIONS                                                */
/* ================================================================== */

const SERVICES: ServiceNode[] = [
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
      "orchestration (saga_instance, saga_step — future)",
    ],
    x: 370,
    y: 540,
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
];

const CONNECTIONS: Connection[] = [
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
];

const GROUP_META: Record<string, { label: string; color: string; icon: string }> = {
  frontend: { label: "Frontend", color: "#3b82f6", icon: "M" },
  backend: { label: "Backend Services", color: "#22c55e", icon: "S" },
  ai: { label: "AI Platform", color: "#a855f7", icon: "A" },
  infra: { label: "Infrastructure", color: "#0ea5e9", icon: "I" },
};

const STATUS_COLORS: Record<ServiceStatus, string> = {
  healthy: "#22c55e",
  degraded: "#eab308",
  down: "#ef4444",
  idle: "#6b7280",
};

/* ================================================================== */
/*  FLOW STEPS                                                         */
/* ================================================================== */

const FLOW_STEPS = [
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

/* ================================================================== */
/*  PERFORMANCE & TRADEOFFS DATA                                       */
/* ================================================================== */

const PERF_SECTIONS = [
  {
    title: "Outbox Dispatcher",
    icon: "⚡",
    metrics: [
      { label: "Poll interval", value: "2,000ms", note: "Fixed delay between dispatch cycles" },
      { label: "Batch size", value: "10 events/cycle", note: "Max outbox rows claimed per cycle" },
      { label: "Claim strategy", value: "FOR UPDATE SKIP LOCKED", note: "Lock-free multi-instance safe" },
      { label: "Claim TTL", value: "15,000ms", note: "Expired claims reclaimed by other instances" },
      { label: "Retry delay", value: "5,000ms", note: "Backoff before next attempt on failed rows" },
      { label: "Throughput", value: "~5 events/sec", note: "10 events / 2s cycle (single instance)" },
    ],
    tradeoff:
      "The 2s fixed delay trades latency for simplicity — no complex polling or backpressure. Multi-instance scales linearly via SKIP LOCKED without coordination overhead. Claim TTL prevents stuck rows from blocking the pipeline.",
  },
  {
    title: "Inbox Idempotency",
    icon: "🛡️",
    metrics: [
      { label: "Dedup key", value: "event_id (PK)", note: "Natural idempotency via primary key constraint" },
      { label: "Check cost", value: "existsById()", note: "Single PK lookup, O(1) in B-tree index" },
      { label: "Guarantee", value: "At-most-once processing", note: "Combined with outbox = exactly-once semantic" },
    ],
    tradeoff:
      "PK-based dedup is the simplest idempotency pattern — zero additional infrastructure. The tradeoff is that the inbox table grows monotonically; a future TTL-based cleanup would be needed at scale.",
  },
  {
    title: "Timeouts & Latency",
    icon: "⏱️",
    metrics: [
      { label: "Frontend → AI Gateway", value: "120s", note: "Accounts for LLM generation latency" },
      { label: "Frontend → Tools execute", value: "30s", note: "Tool execution round-trip" },
      { label: "Frontend → Health/Tools list", value: "10s", note: "Fast endpoints, tight timeout" },
      { label: "AI Gateway → RAG", value: "30s", note: "Embedding + vector search" },
      { label: "AI Gateway → Benefits APIs", value: "30s", note: "REST API calls for tool results" },
      { label: "Enrollment → Processing", value: "Default", note: "RestClient default (no explicit timeout)" },
    ],
    tradeoff:
      "The 120s chat timeout reflects real-world LLM latency with tool loops (up to 10 iterations). The enrollment HTTP publisher lacks an explicit timeout — a production hardening opportunity to prevent hung connections from blocking the dispatcher.",
  },
  {
    title: "RAG Pipeline",
    icon: "🔍",
    metrics: [
      { label: "Chunk size", value: "512 tokens", note: "~384 words per chunk" },
      { label: "Chunk overlap", value: "50 tokens", note: "Context continuity between chunks" },
      { label: "Embedding dim", value: "768", note: "nomic-embed-text output dimension" },
      { label: "Similarity", value: "Cosine distance", note: "pgvector operator" },
      { label: "Top-K", value: "5", note: "Results returned per search" },
      { label: "DB pool", value: "5 + 10 overflow", note: "asyncpg connection pool" },
    ],
    tradeoff:
      "512-token chunks balance context richness vs. retrieval precision. Sequential embedding (not batched) is simple but would bottleneck at high ingestion volume. The cosine distance search has no IVFFlat index configured — fine for small corpora but needs indexing above ~100K chunks.",
  },
  {
    title: "Agent Loop",
    icon: "🤖",
    metrics: [
      { label: "Max iterations", value: "10", note: "Prevents runaway tool loops" },
      { label: "Classification", value: "Keyword-based", note: "Fast but not ML-based routing" },
      { label: "UUID stripping", value: "Post-processing", note: "Internal IDs never leak to LLM responses" },
      { label: "Conversation", value: "Session-based", note: "In-memory history per session" },
    ],
    tradeoff:
      "Keyword-based query classification is fast and deterministic but less nuanced than embedding-based routing. The 10-iteration cap is conservative — most queries resolve in 1-3 iterations. Session-based memory is lost on restart; persistent conversation storage is a future consideration.",
  },
  {
    title: "Database & Connection Pooling",
    icon: "💾",
    metrics: [
      { label: "Database", value: "Single instance", note: "All schemas in one PostgreSQL DB" },
      { label: "Schema isolation", value: "5 schemas", note: "Bounded context per schema" },
      { label: "HikariCP (Java)", value: "Default (10)", note: "Spring Boot default pool size" },
      { label: "asyncpg (Python)", value: "5 + 10 overflow", note: "Knowledge Service only" },
      { label: "Flyway", value: "3 migrations", note: "Shared across all services" },
      { label: "DDL mode", value: "validate", note: "Schema managed by Flyway, not Hibernate" },
    ],
    tradeoff:
      "Single-database, multi-schema trades operational simplicity for logical isolation. Services share a physical database but respect schema boundaries — no cross-schema joins. This is the right trade for a small team; splitting to separate databases adds operational overhead without clear benefit at current scale.",
  },
];

/* ================================================================== */
/*  CLOUD EVOLUTION                                                    */
/* ================================================================== */

const CLOUD_STAGES = [
  {
    stage: "Current — Local",
    color: "#22c55e",
    items: [
      "HTTP publisher adapter (Enrollment → Processing)",
      "Docker Compose (PostgreSQL + pgvector, Java services)",
      "Ollama for local LLM (llama3.1:8b + nomic-embed-text)",
      "Single PostgreSQL instance, schema-per-service",
    ],
  },
  {
    stage: "Phase 1 — Cloud Messaging",
    color: "#3b82f6",
    items: [
      "EventBridge publisher adapter (replaces HTTP)",
      "SQS queue between EventBridge and Processing Service",
      "RDS PostgreSQL (multi-AZ) replaces local Docker DB",
      "Enrollment API unchanged — only transport swapped",
    ],
  },
  {
    stage: "Phase 2 — Managed AI",
    color: "#a855f7",
    items: [
      "Amazon Bedrock replaces Ollama for LLM inference",
      "RDS pgvector for production embedding storage",
      "ECS/Fargate for AI Gateway and Knowledge Service",
      "CloudWatch observability and X-Ray tracing",
    ],
  },
  {
    stage: "Phase 3 — Orchestration",
    color: "#f97316",
    items: [
      "Saga orchestrator for long-running enrollment workflows",
      "Compensation steps in orchestration schema",
      "Step Functions or custom saga engine",
      "Multi-step enrollment with approval gates",
    ],
  },
];

/* ================================================================== */
/*  DATA MODEL                                                         */
/* ================================================================== */

const SCHEMA_TABLES = [
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

/* ================================================================== */
/*  SVG HELPERS                                                        */
/* ================================================================== */

function center(s: ServiceNode) {
  return { x: s.x + s.w / 2, y: s.y + s.h / 2 };
}

function edgePoint(s: ServiceNode, target: { x: number; y: number }) {
  const c = center(s);
  const dx = target.x - c.x;
  const dy = target.y - c.y;
  const hw = s.w / 2;
  const hh = s.h / 2;

  if (dx === 0 && dy === 0) return c;

  const scaleX = hw / Math.abs(dx || 1);
  const scaleY = hh / Math.abs(dy || 1);
  const scale = Math.min(scaleX, scaleY);

  return { x: c.x + dx * scale, y: c.y + dy * scale };
}

function computePath(from: ServiceNode, to: ServiceNode): string {
  const fc = center(from);
  const tc = center(to);
  const a = edgePoint(from, tc);
  const b = edgePoint(to, fc);

  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2;
  const cx = mx + (b.y - a.y) * 0.08;
  const cy = my - (b.x - a.x) * 0.08;

  return `M${a.x},${a.y} Q${cx},${cy} ${b.x},${b.y}`;
}

/* ================================================================== */
/*  COMPONENT                                                          */
/* ================================================================== */

export default function ArchitecturePage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [flowStep, setFlowStep] = useState<number | null>(null);
  const [activeGroup, setActiveGroup] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("diagram");
  const detailRef = useRef<HTMLDivElement>(null);

  const selectedService = SERVICES.find((s) => s.id === selected) ?? null;
  const currentFlow = flowStep !== null ? FLOW_STEPS[flowStep] : null;

  const isNodeHighlighted = useCallback(
    (id: string) => {
      if (currentFlow) return currentFlow.active.includes(id);
      if (activeGroup) return SERVICES.find((s) => s.id === id)?.group === activeGroup;
      return true;
    },
    [currentFlow, activeGroup]
  );

  const isConnHighlighted = useCallback(
    (idx: number) => {
      if (currentFlow) return currentFlow.activeConns.includes(idx);
      if (activeGroup) {
        const conn = CONNECTIONS[idx];
        const fromG = SERVICES.find((s) => s.id === conn.from)?.group;
        const toG = SERVICES.find((s) => s.id === conn.to)?.group;
        return fromG === activeGroup || toG === activeGroup;
      }
      return true;
    },
    [currentFlow, activeGroup]
  );

  const handleNodeClick = (id: string) => {
    setSelected(selected === id ? null : id);
    if (selected !== id) {
      setTimeout(() => detailRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 100);
    }
  };

  /* ---------------------------------------------------------------- */
  /*  TAB CONTENT RENDERERS                                            */
  /* ---------------------------------------------------------------- */

  const renderDiagramTab = () => (
    <div className="space-y-5">
      {/* Group filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => { setActiveGroup(null); setFlowStep(null); }}
          className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${activeGroup === null && flowStep === null ? "bg-gray-700 text-gray-100" : "bg-gray-800/50 text-gray-500 hover:text-gray-300"}`}
        >
          All Services
        </button>
        {Object.entries(GROUP_META).map(([key, { label, color }]) => (
          <button
            key={key}
            onClick={() => { setActiveGroup(activeGroup === key ? null : key); setFlowStep(null); setSelected(null); }}
            className="rounded-full px-3 py-1.5 text-xs font-medium transition"
            style={{
              backgroundColor: activeGroup === key ? color + "20" : "rgba(255,255,255,0.04)",
              color: activeGroup === key ? color : "#9ca3af",
              border: `1px solid ${activeGroup === key ? color + "40" : "transparent"}`,
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Flow stepper */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Request Flow Trace</span>
          <div className="flex gap-2">
            {currentFlow && (
              <span className="rounded-md bg-green-500/10 px-2 py-0.5 text-xs font-mono text-green-400">
                {currentFlow.status}
              </span>
            )}
            {flowStep !== null && (
              <button onClick={() => { setFlowStep(null); setSelected(null); }} className="text-xs text-gray-500 hover:text-gray-300">Clear</button>
            )}
          </div>
        </div>
        <div className="grid grid-cols-5 gap-2">
          {FLOW_STEPS.map((step, i) => (
            <button
              key={i}
              onClick={() => { setFlowStep(flowStep === i ? null : i); setActiveGroup(null); setSelected(null); }}
              className="rounded-lg px-2 py-2.5 text-left text-xs transition"
              style={{
                backgroundColor: flowStep === i ? "#22c55e12" : "rgba(255,255,255,0.02)",
                border: `1px solid ${flowStep === i ? "#22c55e40" : "#1f2937"}`,
                color: flowStep === i ? "#4ade80" : "#9ca3af",
              }}
            >
              <span className="font-bold">{step.title}</span>
            </button>
          ))}
        </div>
        {currentFlow && (
          <p className="mt-3 text-sm leading-relaxed text-gray-300">{currentFlow.desc}</p>
        )}
      </div>

      {/* SVG Diagram */}
      <div className="overflow-x-auto rounded-xl border border-gray-800 bg-[#080810] p-2">
        <svg viewBox="0 0 1020 640" className="w-full" style={{ minWidth: 800 }}>
          <defs>
            <marker id="arr" viewBox="0 0 10 6" refX="9" refY="3" markerWidth="7" markerHeight="5" orient="auto-start-reverse">
              <path d="M0,0 L10,3 L0,6Z" fill="#4b5563" />
            </marker>
            <marker id="arr-g" viewBox="0 0 10 6" refX="9" refY="3" markerWidth="7" markerHeight="5" orient="auto-start-reverse">
              <path d="M0,0 L10,3 L0,6Z" fill="#4ade80" />
            </marker>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          {/* Group backgrounds */}
          <rect x="350" y="6" width="290" height="170" rx="16" fill="#3b82f608" stroke="#3b82f615" strokeWidth="1" />
          <text x="365" y="168" fill="#3b82f640" fontSize="9" fontFamily="monospace">FRONTEND</text>
          <rect x="120" y="220" width="760" height="100" rx="16" fill="#22c55e06" stroke="#22c55e12" strokeWidth="1" />
          <text x="135" y="310" fill="#22c55e35" fontSize="9" fontFamily="monospace">BACKEND SERVICES</text>
          <rect x="80" y="378" width="910" height="100" rx="16" fill="#a855f706" stroke="#a855f712" strokeWidth="1" />
          <text x="95" y="468" fill="#a855f735" fontSize="9" fontFamily="monospace">AI PLATFORM</text>
          <rect x="350" y="520" width="290" height="110" rx="16" fill="#0ea5e906" stroke="#0ea5e912" strokeWidth="1" />
          <text x="365" y="622" fill="#0ea5e935" fontSize="9" fontFamily="monospace">INFRASTRUCTURE</text>

          {/* Connections */}
          {CONNECTIONS.map((conn, i) => {
            const from = SERVICES.find((s) => s.id === conn.from)!;
            const to = SERVICES.find((s) => s.id === conn.to)!;
            const path = computePath(from, to);
            const hl = isConnHighlighted(i);
            const dimmed = (currentFlow || activeGroup) && !hl;

            return (
              <g key={i} style={{ opacity: dimmed ? 0.07 : 1, transition: "opacity 0.3s" }}>
                <path
                  d={path}
                  fill="none"
                  stroke={hl && currentFlow ? "#4ade80" : "#374151"}
                  strokeWidth={hl && currentFlow ? 2.5 : 1.2}
                  strokeDasharray={conn.style === "dashed" ? "6,4" : undefined}
                  markerEnd={hl && currentFlow ? "url(#arr-g)" : "url(#arr)"}
                />
              </g>
            );
          })}

          {/* Service nodes */}
          {SERVICES.map((svc) => {
            const hl = isNodeHighlighted(svc.id);
            const dimmed = (currentFlow || activeGroup) && !hl;
            const isSel = selected === svc.id;

            return (
              <g
                key={svc.id}
                onClick={() => handleNodeClick(svc.id)}
                style={{ cursor: "pointer", opacity: dimmed ? 0.1 : 1, transition: "opacity 0.3s" }}
              >
                {isSel && (
                  <rect x={svc.x - 3} y={svc.y - 3} width={svc.w + 6} height={svc.h + 6} rx={12} fill="none" stroke={svc.color} strokeWidth={2} opacity={0.6} filter="url(#glow)" />
                )}
                <rect x={svc.x} y={svc.y} width={svc.w} height={svc.h} rx={10} fill="#111118" stroke={isSel ? svc.color : "#1e293b"} strokeWidth={isSel ? 1.5 : 0.8} />
                <rect x={svc.x} y={svc.y} width={svc.w} height={3} rx={1.5} fill={svc.color} opacity={0.8} />
                <circle cx={svc.x + svc.w - 12} cy={svc.y + 14} r={3.5} fill={STATUS_COLORS[svc.status]} />
                <text x={svc.x + 12} y={svc.y + 22} fill="#e5e7eb" fontSize="11" fontWeight="600" fontFamily="system-ui, sans-serif">{svc.label}</text>
                <text x={svc.x + 12} y={svc.y + 37} fill="#6b7280" fontSize="9" fontFamily="monospace">
                  {svc.port ? `:${svc.port}` : ""}{svc.port && svc.subtitle ? " · " : ""}{svc.subtitle}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Detail panel */}
      <div ref={detailRef}>
        {selectedService && (
          <div className="rounded-xl border p-5 transition-all" style={{ borderColor: selectedService.color + "30", backgroundColor: selectedService.color + "06" }}>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-bold text-gray-100">{selectedService.label}</h2>
                <div className="mt-1 flex items-center gap-2">
                  <span className="rounded-full px-2 py-0.5 text-xs font-medium" style={{ backgroundColor: selectedService.color + "18", color: selectedService.color }}>{selectedService.group}</span>
                  <span className="flex items-center gap-1.5 text-xs text-gray-400">
                    <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: STATUS_COLORS[selectedService.status] }} />
                    {selectedService.status}
                  </span>
                  {selectedService.port && <code className="rounded bg-gray-800 px-1.5 py-0.5 text-xs text-gray-300">:{selectedService.port}</code>}
                </div>
              </div>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-gray-300">{selectedService.description}</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">Technology</h3>
                <p className="text-sm text-gray-300">{selectedService.tech}</p>
              </div>
              {selectedService.schemas && (
                <div>
                  <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">DB Schemas</h3>
                  {selectedService.schemas.map((s, i) => <p key={i} className="font-mono text-xs text-gray-400">{s}</p>)}
                </div>
              )}
            </div>
            {selectedService.endpoints && (
              <div className="mt-4">
                <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">Endpoints</h3>
                <div className="grid gap-0.5 sm:grid-cols-2">
                  {selectedService.endpoints.map((ep, i) => <span key={i} className="font-mono text-xs text-gray-400">{ep}</span>)}
                </div>
              </div>
            )}
            {selectedService.config && (
              <div className="mt-4">
                <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">Configuration</h3>
                <div className="grid gap-1 sm:grid-cols-2">
                  {Object.entries(selectedService.config).map(([k, v]) => (
                    <div key={k} className="flex gap-2 text-xs">
                      <span className="text-gray-500">{k}:</span>
                      <span className="font-mono text-gray-300">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="mt-4">
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">Connections</h3>
              <div className="flex flex-wrap gap-1.5">
                {CONNECTIONS.filter((c) => c.from === selectedService.id || c.to === selectedService.id).map((c, i) => {
                  const other = c.from === selectedService.id ? c.to : c.from;
                  const otherSvc = SERVICES.find((s) => s.id === other);
                  const dir = c.from === selectedService.id ? "\u2192" : "\u2190";
                  return (
                    <span key={i} className="rounded-md bg-gray-800/60 px-2 py-1 text-xs text-gray-300">
                      {dir} {otherSvc?.label} <span className="text-gray-500">({c.protocol})</span>
                    </span>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-5 rounded-lg border border-gray-800/50 bg-[#0d0d14] px-4 py-2.5 text-xs text-gray-500">
        {Object.entries(STATUS_COLORS).map(([s, c]) => (
          <span key={s} className="flex items-center gap-1.5"><span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: c }} />{s}</span>
        ))}
        <span className="ml-2 border-l border-gray-800 pl-3">Click nodes for details</span>
        <span>Use flow stepper to trace requests</span>
      </div>
    </div>
  );

  const renderDetailsTab = () => (
    <div className="space-y-6">
      {/* State machine */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-200">Enrollment State Machine</h3>
        <div className="flex items-center justify-center gap-3 overflow-x-auto py-2">
          {[
            { state: "SUBMITTED", color: "#eab308" },
            { state: "PROCESSING", color: "#3b82f6" },
            { state: "COMPLETED", color: "#22c55e" },
          ].map((s, i) => (
            <div key={s.state} className="flex items-center gap-3">
              <div className="rounded-lg px-4 py-2 text-center" style={{ backgroundColor: s.color + "15", border: `1px solid ${s.color}40` }}>
                <span className="font-mono text-sm font-bold" style={{ color: s.color }}>{s.state}</span>
              </div>
              {i < 2 && (
                <svg width="32" height="16"><path d="M2,8 L26,8" stroke="#4b5563" strokeWidth="2" markerEnd="url(#arr)" /><defs><marker id="arr2" viewBox="0 0 10 6" refX="9" refY="3" markerWidth="8" markerHeight="6" orient="auto"><path d="M0,0L10,3L0,6Z" fill="#4b5563" /></marker></defs></svg>
              )}
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center justify-center gap-2">
          <span className="rounded-md bg-red-500/10 px-2 py-1 text-xs font-mono text-red-400">DISPATCH_FAILED</span>
          <span className="text-xs text-gray-500">↻ retries back to SUBMITTED</span>
        </div>
      </div>

      {/* Outbox/Inbox pattern */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-3 text-sm font-semibold text-gray-200">Outbox / Inbox Messaging Pattern</h3>
        <div className="space-y-3 text-sm text-gray-300">
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-3">
              <h4 className="mb-2 font-semibold text-green-400">Outbox (Producer Side)</h4>
              <ul className="space-y-1 text-xs text-gray-400">
                <li>• Enrollment + outbox event in <span className="text-green-300">single transaction</span></li>
                <li>• Dispatcher polls every <span className="font-mono text-green-300">2s</span>, claims <span className="font-mono text-green-300">10</span> rows</li>
                <li>• <span className="font-mono text-green-300">FOR UPDATE SKIP LOCKED</span> — no contention</li>
                <li>• Claims expire after <span className="font-mono text-green-300">15s</span> TTL</li>
                <li>• Failed rows retry after <span className="font-mono text-green-300">5s</span> backoff</li>
                <li>• Attempt count + last_error for observability</li>
              </ul>
            </div>
            <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">
              <h4 className="mb-2 font-semibold text-blue-400">Inbox (Consumer Side)</h4>
              <ul className="space-y-1 text-xs text-gray-400">
                <li>• <span className="text-blue-300">PK dedup</span> — event_id is inbox primary key</li>
                <li>• Duplicate delivery = <span className="text-blue-300">no-op</span> (existsById check)</li>
                <li>• Creates processing record on first receive</li>
                <li>• Async worker handles completion (<span className="font-mono text-blue-300">@Async</span>)</li>
                <li>• Combined guarantee: <span className="text-blue-300">exactly-once semantic</span></li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* AI Architecture */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-3 text-sm font-semibold text-gray-200">AI Platform — Two-Phase Agent Loop</h3>
        <div className="space-y-2 text-sm">
          <div className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-500/20 text-xs font-bold text-purple-400">1</div>
              <div className="mt-1 h-full w-px bg-gray-800" />
            </div>
            <div className="pb-4">
              <h4 className="font-semibold text-purple-300">RAG Context Injection</h4>
              <p className="text-xs text-gray-400">Query → Knowledge Service → Ollama embedding (768-dim) → pgvector cosine search → top-5 chunks injected into system prompt</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-purple-500/20 text-xs font-bold text-purple-400">2</div>
            </div>
            <div>
              <h4 className="font-semibold text-purple-300">Query Classification & Execution</h4>
              <p className="text-xs text-gray-400">Keyword matching → knowledge-only (direct LLM, no tools) OR data-requiring (tool calls via MCP → Benefits APIs → UUID stripping → final LLM response). Max 10 iterations.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Service responsibility matrix */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-3 text-sm font-semibold text-gray-200">Service Responsibility Matrix</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-800 text-left text-gray-500">
                <th className="py-2 pr-4 font-medium">Capability</th>
                <th className="py-2 pr-4 font-medium">Owner</th>
                <th className="py-2 font-medium">Notes</th>
              </tr>
            </thead>
            <tbody className="text-gray-400">
              {[
                ["Enrollment submission", "Enrollment Service", "Atomic write: enrollment + selections + outbox"],
                ["Status lookup", "Enrollment Service", "By ID, employee ID, employee name, or status"],
                ["Outbox dispatch + retry", "Enrollment Service", "Scheduled, SKIP LOCKED, configurable batch/TTL"],
                ["Event transport", "Publisher Adapter", "http (current), eventbridge (future)"],
                ["Idempotent consume", "Processing Service", "Inbox PK dedup on event_id"],
                ["Async processing", "Processing Service", "@Async worker, simulated 500ms"],
                ["LLM orchestration", "AI Gateway", "Two-phase agent loop, max 10 iterations"],
                ["RAG search", "Knowledge Service", "512-token chunks, nomic-embed-text, pgvector"],
                ["MCP tools", "MCP Server", "7 tools, SSE transport, stateless"],
                ["Document ingestion", "Knowledge Service", "Chunking + embedding + vector storage"],
                ["Schema migrations", "shared-model (Flyway)", "V1–V3, shared across all services"],
              ].map(([cap, owner, notes], i) => (
                <tr key={i} className="border-b border-gray-800/50">
                  <td className="py-2 pr-4 font-medium text-gray-300">{cap}</td>
                  <td className="py-2 pr-4 font-mono">{owner}</td>
                  <td className="py-2">{notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Port allocation */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-3 text-sm font-semibold text-gray-200">Port Allocation</h3>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {SERVICES.filter((s) => s.port).map((s) => (
            <div key={s.id} className="rounded-lg border border-gray-800 bg-gray-900/30 px-3 py-2 text-center">
              <code className="text-lg font-bold" style={{ color: s.color }}>{s.port}</code>
              <p className="mt-0.5 text-xs text-gray-400">{s.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderPerformanceTab = () => (
    <div className="space-y-6">
      {PERF_SECTIONS.map((section) => (
        <div key={section.title} className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-gray-200">
            <span>{section.icon}</span>
            {section.title}
          </h3>
          <div className="mb-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {section.metrics.map((m) => (
              <div key={m.label} className="rounded-lg border border-gray-800 bg-gray-900/30 p-3">
                <div className="text-xs text-gray-500">{m.label}</div>
                <div className="mt-0.5 font-mono text-sm font-bold text-gray-200">{m.value}</div>
                <div className="mt-0.5 text-xs text-gray-500">{m.note}</div>
              </div>
            ))}
          </div>
          <div className="rounded-lg border border-amber-500/15 bg-amber-500/5 px-4 py-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-400/80">Tradeoff Analysis</span>
            <p className="mt-1 text-sm leading-relaxed text-gray-300">{section.tradeoff}</p>
          </div>
        </div>
      ))}
    </div>
  );

  const renderDataTab = () => (
    <div className="space-y-6">
      {SCHEMA_TABLES.map((schema) => (
        <div key={schema.schema} className="rounded-xl border bg-[#0d0d14] p-5" style={{ borderColor: schema.color + "30" }}>
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold">
            <span className="inline-block h-3 w-3 rounded" style={{ backgroundColor: schema.color }} />
            <span style={{ color: schema.color }}>{schema.schema}</span>
            <span className="text-gray-500">schema</span>
          </h3>
          <div className="space-y-4">
            {schema.tables.map((table) => (
              <div key={table.name} className="rounded-lg border border-gray-800 bg-gray-900/20 p-4">
                <h4 className="mb-2 font-mono text-sm font-bold text-gray-200">{table.name}</h4>
                <div className="space-y-0.5">
                  {table.columns.map((col, i) => {
                    const isPK = col.includes("PK");
                    const isFK = col.includes("FK");
                    return (
                      <div key={i} className="flex items-center gap-2 font-mono text-xs">
                        {isPK && <span className="rounded bg-yellow-500/20 px-1 text-yellow-400">PK</span>}
                        {isFK && <span className="rounded bg-blue-500/20 px-1 text-blue-400">FK</span>}
                        <span className={isPK || isFK ? "text-gray-200" : "text-gray-400"}>{col}</span>
                      </div>
                    );
                  })}
                </div>
                {table.indices && (
                  <div className="mt-2 border-t border-gray-800 pt-2">
                    <span className="text-xs text-gray-500">Indices: </span>
                    {table.indices.map((idx, i) => (
                      <span key={i} className="ml-1 rounded bg-gray-800 px-1.5 py-0.5 font-mono text-xs text-gray-400">{idx}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );

  const renderCloudTab = () => (
    <div className="space-y-6">
      {/* Evolution timeline */}
      <div className="space-y-4">
        {CLOUD_STAGES.map((stage, i) => (
          <div key={stage.stage} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold" style={{ backgroundColor: stage.color + "20", color: stage.color, border: `2px solid ${stage.color}40` }}>
                {i + 1}
              </div>
              {i < CLOUD_STAGES.length - 1 && <div className="mt-1 h-full w-px" style={{ backgroundColor: stage.color + "30" }} />}
            </div>
            <div className="flex-1 rounded-xl border bg-[#0d0d14] p-4" style={{ borderColor: stage.color + "25" }}>
              <h3 className="font-semibold" style={{ color: stage.color }}>{stage.stage}</h3>
              <ul className="mt-2 space-y-1">
                {stage.items.map((item, j) => (
                  <li key={j} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="mt-1.5 inline-block h-1.5 w-1.5 rounded-full" style={{ backgroundColor: stage.color + "60" }} />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      {/* Cloud architecture diagram */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-200">Target Cloud Architecture</h3>
        <div className="overflow-x-auto">
          <svg viewBox="0 0 800 300" className="w-full" style={{ minWidth: 600 }}>
            {/* Nodes */}
            {[
              { x: 20, y: 120, w: 100, h: 44, label: "UI / Client", color: "#3b82f6" },
              { x: 160, y: 60, w: 130, h: 44, label: "Enrollment Service", color: "#22c55e" },
              { x: 160, y: 180, w: 130, h: 44, label: "AI Gateway", color: "#a855f7" },
              { x: 340, y: 60, w: 120, h: 44, label: "EventBridge", color: "#f97316" },
              { x: 340, y: 180, w: 120, h: 44, label: "Knowledge Svc", color: "#a855f7" },
              { x: 510, y: 60, w: 100, h: 44, label: "SQS Queue", color: "#f97316" },
              { x: 510, y: 180, w: 120, h: 44, label: "LLM (Bedrock)", color: "#f97316" },
              { x: 660, y: 60, w: 120, h: 44, label: "Processing Svc", color: "#22c55e" },
              { x: 660, y: 180, w: 120, h: 44, label: "RDS PostgreSQL", color: "#0ea5e9" },
            ].map((n, i) => (
              <g key={i}>
                <rect x={n.x} y={n.y} width={n.w} height={n.h} rx={8} fill="#111118" stroke={n.color + "50"} strokeWidth={1} />
                <rect x={n.x} y={n.y} width={n.w} height={3} rx={1.5} fill={n.color} opacity={0.7} />
                <text x={n.x + n.w / 2} y={n.y + 27} textAnchor="middle" fill="#d1d5db" fontSize="10" fontWeight="600" fontFamily="system-ui">{n.label}</text>
              </g>
            ))}
            {/* Arrows */}
            {[
              "M120,142 L160,82", "M120,142 L160,202",
              "M290,82 L340,82", "M460,82 L510,82", "M610,82 L660,82",
              "M290,82 L290,240 Q290,250 300,250 L650,250 Q660,250 660,240 L660,215",
              "M720,104 L720,180",
              "M290,202 L340,202", "M460,202 L510,202",
              "M160,202 Q140,202 140,180 L140,100 Q140,82 160,82",
            ].map((d, i) => (
              <path key={i} d={d} fill="none" stroke="#374151" strokeWidth={1.2} markerEnd="url(#arr)" />
            ))}
          </svg>
        </div>
      </div>

      {/* Key migration decisions */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-3 text-sm font-semibold text-gray-200">Key Migration Decisions</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            { title: "Publisher Adapter Pattern", desc: "HTTP → EventBridge swap requires only a new adapter implementation + config change. No API or schema changes needed.", color: "#22c55e" },
            { title: "Schema-per-Service", desc: "Physical DB split is possible later — each service already respects schema boundaries with no cross-schema joins.", color: "#3b82f6" },
            { title: "LLM Portability", desc: "Ollama → Bedrock is a client configuration change. AI Gateway abstracts the LLM provider behind a unified interface.", color: "#a855f7" },
            { title: "Saga Orchestration", desc: "orchestration schema is pre-created. Saga tables exist in V1 migration, ready for long-running workflow coordination.", color: "#f97316" },
          ].map((d) => (
            <div key={d.title} className="rounded-lg border border-gray-800 bg-gray-900/20 p-3">
              <h4 className="text-sm font-semibold" style={{ color: d.color }}>{d.title}</h4>
              <p className="mt-1 text-xs text-gray-400">{d.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  /* ---------------------------------------------------------------- */
  /*  MAIN RENDER                                                      */
  /* ---------------------------------------------------------------- */

  const TABS: { id: Tab; label: string }[] = [
    { id: "diagram", label: "Deployment Diagram" },
    { id: "details", label: "Architecture Details" },
    { id: "performance", label: "Performance & Tradeoffs" },
    { id: "data", label: "Data Model" },
    { id: "cloud", label: "Cloud Evolution" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">System Architecture</h1>
        <p className="mt-1 text-sm text-gray-400">
          Employee Benefits Platform — interactive deployment diagram, architecture details, performance analysis, and cloud evolution roadmap.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border border-gray-800 bg-[#0d0d14] p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id); setSelected(null); setFlowStep(null); setActiveGroup(null); }}
            className={`flex-1 rounded-md px-3 py-2 text-xs font-medium transition ${
              activeTab === tab.id
                ? "bg-gray-800 text-gray-100"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "diagram" && renderDiagramTab()}
      {activeTab === "details" && renderDetailsTab()}
      {activeTab === "performance" && renderPerformanceTab()}
      {activeTab === "data" && renderDataTab()}
      {activeTab === "cloud" && renderCloudTab()}

      {/* Footer */}
      <div className="border-t border-gray-800 pt-4 text-center text-xs text-gray-600">
        Employee Benefits Platform · 8 services · 5 DB schemas · 3 Flyway migrations · Outbox/Inbox messaging · RAG-powered AI
      </div>
    </div>
  );
}
