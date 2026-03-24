import { PERF_SECTIONS } from "../data/performance";

export default function AgenticTab() {
  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-400">AI capabilities powering the platform: 6-layer security hardening, RAG knowledge pipeline, evaluation framework, and governance controls.</p>

      {/* Security Hardening Layers */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-200">Security Hardening — 6 Defense Layers</h3>
        <div className="space-y-2">
          {[
            { layer: 1, title: "Input Guardrails", color: "#ef4444", items: ["26 prompt injection patterns", "8 harmful content patterns", "Unicode NFKC normalization", "Leet-speak decoding (1→i, 3→e, 0→o)", "2,000 char limit"] },
            { layer: 2, title: "System Prompt Hardening", color: "#a855f7", items: ["Prose-based identity framing", "Fixed response for system probes", "Persona permanence", "Benefits-only domain lock"] },
            { layer: 3, title: "Output Filtering", color: "#3b82f6", items: ["System prompt fragment detection", "Internal DB term detection", "UUID stripping", "Email redaction"] },
            { layer: 4, title: "Rate Limiting", color: "#eab308", items: ["Sliding window per-IP (20 RPM)", "X-Forwarded-For support", "HTTP 429 with Retry-After"] },
            { layer: 5, title: "Audit Logging", color: "#22c55e", items: ["Structured JSON-lines events", "8 event types tracked", "200-char preview truncation"] },
            { layer: 6, title: "RAG Sanitization", color: "#06b6d4", items: ["Scans knowledge chunks before LLM", "Strips injection patterns from context", "Prevents indirect prompt injection"] },
          ].map((l) => (
            <div key={l.layer} className="rounded-lg border bg-[#111118] p-4 flex gap-4" style={{ borderColor: l.color + "30" }}>
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold" style={{ backgroundColor: l.color + "20", color: l.color }}>{l.layer}</div>
              <div className="flex-1">
                <div className="text-xs font-semibold mb-1" style={{ color: l.color }}>{l.title}</div>
                <div className="flex flex-wrap gap-x-4 gap-y-0.5">
                  {l.items.map((item) => (<span key={item} className="text-[10px] text-gray-500">• {item}</span>))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* RAG Pipeline */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-200">RAG Pipeline</h3>
        <div className="flex items-center gap-0 overflow-x-auto py-2 mb-4">
          {["Document\nUpload", "Semantic\nChunking", "Embedding\nGeneration", "pgvector\nStore", "Vector\nSearch", "Context\nInjection"].map((label, i) => {
            const colors = ["#3b82f6", "#a855f7", "#eab308", "#22c55e", "#06b6d4", "#ec4899"];
            return (
              <div key={label} className="flex items-center">
                {i > 0 && <div className="mx-1 h-px w-8 bg-gray-700" />}
                <div className="rounded-lg px-3 py-2 text-center whitespace-pre-line" style={{ backgroundColor: colors[i] + "15" }}>
                  <div className="text-[10px] font-medium" style={{ color: colors[i] }}>{label}</div>
                </div>
              </div>
            );
          })}
        </div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[
            { label: "Chunk Size", value: "512 tokens" }, { label: "Overlap", value: "50 tokens" },
            { label: "Embedding", value: "nomic-embed-text" }, { label: "Dimensions", value: "768" },
            { label: "Index", value: "IVFFlat (cosine)" }, { label: "Top-K", value: "5 results" },
            { label: "Documents", value: "16 docs, 45 chunks" }, { label: "Categories", value: "policy, plan, faq, compliance, process" },
          ].map((s) => (
            <div key={s.label} className="rounded-lg border border-gray-800/50 bg-[#111118] p-2">
              <div className="text-[9px] text-gray-600 uppercase tracking-wider">{s.label}</div>
              <div className="mt-0.5 text-xs text-gray-300 font-mono">{s.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Evaluation Framework */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-200">Evaluation Framework</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 mb-4">
          {[
            { name: "Accuracy", color: "#3b82f6", desc: "Correct agent routing + expected tool calls", scoring: "1.0 both | 0.5 agent only | 0.0 wrong" },
            { name: "Relevance", color: "#22c55e", desc: "Response quality via LLM-as-judge", scoring: "1-5 scale → 0.0-1.0" },
            { name: "Safety", color: "#ef4444", desc: "Guardrail bypass resistance", scoring: "1.0 blocked | 0.0 bypassed" },
            { name: "Latency", color: "#eab308", desc: "Response time vs threshold", scoring: "1.0 at 0ms → 0.0 at 2× threshold" },
            { name: "Cost", color: "#a855f7", desc: "Token usage efficiency", scoring: "Budget-based linear decay" },
            { name: "Faithfulness", color: "#06b6d4", desc: "RAG grounding accuracy", scoring: "Grounded vs hallucinated ratio" },
          ].map((ev) => (
            <div key={ev.name} className="rounded-lg border bg-[#111118] p-3" style={{ borderColor: ev.color + "30" }}>
              <div className="text-xs font-bold mb-1" style={{ color: ev.color }}>{ev.name}</div>
              <p className="text-[10px] text-gray-400 mb-1">{ev.desc}</p>
              <div className="text-[9px] text-gray-600 font-mono">{ev.scoring}</div>
            </div>
          ))}
        </div>
        <div className="rounded-lg border border-gray-800 bg-[#111118] p-3">
          <div className="text-xs font-medium text-gray-300 mb-2">45 Golden Test Cases — 3 Datasets</div>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-[10px] text-gray-500"><span className="text-blue-400 font-medium">enrollment_queries</span> — 15 cases</div>
            <div className="text-[10px] text-gray-500"><span className="text-green-400 font-medium">policy_questions</span> — 15 cases</div>
            <div className="text-[10px] text-gray-500"><span className="text-red-400 font-medium">adversarial</span> — 15 cases</div>
          </div>
        </div>
      </div>

      {/* Governance Controls */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-200">Governance Controls</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {[
            { title: "Policy Engine", color: "#3b82f6", items: ["YAML-driven, 10 active policies", "6 condition operators", "5 effects: allow, deny, redact, log, require_approval", "Priority-ordered evaluation"] },
            { title: "PII Detection", color: "#ef4444", items: ["6 PII types: SSN, email, phone, credit card, DOB, address", "SSN risk=1.0, credit card=0.9, email=0.3", "Automatic redaction in responses"] },
            { title: "Risk Scoring", color: "#eab308", items: ["Multi-factor: action type, PII, tools, sensitivity", "read=0.1, submit=0.3, delete=0.8", "Thresholds: low<0.3, medium<0.7, high<0.9, critical≥0.9"] },
            { title: "Approval Workflow", color: "#22c55e", items: ["Human-in-the-loop for critical actions", "30 min timeout, auto-expiration", "Full context preserved for reviewer"] },
          ].map((card) => (
            <div key={card.title} className="rounded-lg border bg-[#111118] p-4" style={{ borderColor: card.color + "30" }}>
              <div className="text-xs font-bold mb-2" style={{ color: card.color }}>{card.title}</div>
              <ul className="space-y-0.5">
                {card.items.map((item) => (<li key={item} className="text-[10px] text-gray-500">• {item}</li>))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-200">Performance Metrics</h3>
        <div className="space-y-3">
          {PERF_SECTIONS.map((section) => (
            <div key={section.title} className="rounded-lg border border-gray-800/50 bg-[#111118] p-4">
              <h4 className="mb-3 flex items-center gap-2 text-xs font-semibold text-gray-300">
                <span>{section.icon}</span>{section.title}
              </h4>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 mb-2">
                {section.metrics.map((m) => (
                  <div key={m.label} className="rounded border border-gray-800/30 bg-gray-900/20 p-2">
                    <div className="text-[9px] text-gray-600 uppercase">{m.label}</div>
                    <div className="font-mono text-xs font-bold text-gray-300">{m.value}</div>
                    <div className="text-[9px] text-gray-600">{m.note}</div>
                  </div>
                ))}
              </div>
              <div className="rounded bg-amber-500/5 border border-amber-500/10 px-3 py-1.5">
                <span className="text-[9px] font-medium text-amber-400/80">Tradeoff:</span>
                <span className="ml-1 text-[9px] text-gray-500">{section.tradeoff}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
