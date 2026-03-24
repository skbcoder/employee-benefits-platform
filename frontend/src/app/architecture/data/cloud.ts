export interface CloudStage {
  stage: string;
  color: string;
  items: string[];
}

export const CLOUD_STAGES: CloudStage[] = [
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
    stage: "Phase 2 — AI Orchestration (Implemented)",
    color: "#a855f7",
    items: [
      "Multi-agent orchestrator with keyword/LLM routing (port 8400)",
      "Governance service: audit trail, PII detection, policy engine, approvals (port 8500)",
      "Evaluation service: heuristic scoring, benchmark suites (port 8600)",
      "Quality gates, token budgets, and compliance risk assessment",
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
