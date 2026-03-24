export interface PerfMetric {
  label: string;
  value: string;
  note: string;
}

export interface PerfSection {
  title: string;
  icon: string;
  metrics: PerfMetric[];
  tradeoff: string;
}

export const PERF_SECTIONS: PerfSection[] = [
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
    title: "Phase 2 — AI Orchestration",
    icon: "🧠",
    metrics: [
      { label: "Agent routing (keyword)", value: "<1ms", note: "Fast keyword-based classification" },
      { label: "Agent routing (LLM)", value: "~200ms", note: "LLM-based intent classification" },
      { label: "Quality gate", value: "<1ms", note: "Heuristic scoring per response" },
      { label: "PII detection", value: "<1ms", note: "Regex-based per response" },
      { label: "Policy engine", value: "<1ms", note: "For 10 YAML rules" },
      { label: "Token budget", value: "Per-request", note: "Enforcement adds negligible overhead" },
    ],
    tradeoff:
      "Keyword routing is near-instant but less nuanced — LLM routing adds ~200ms for ambiguous queries. Heuristic quality scoring is fast but less accurate than LLM-as-judge. Regex PII detection catches common patterns but may miss obfuscated PII. YAML policy engine is simple and auditable but lacks complex conditional logic.",
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
