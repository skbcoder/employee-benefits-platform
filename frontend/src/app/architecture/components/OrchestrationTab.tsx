import { SERVICES, CONNECTIONS } from "../data/services";

export default function OrchestrationTab() {
  return (
    <div className="space-y-6">
      {/* Intro */}
      <p className="text-sm text-gray-400">Multi-agent orchestration powered by LangGraph. Each user query is classified by a Router and delegated to a specialist agent, with compliance checks and response synthesis.</p>

      {/* LangGraph Flow Diagram */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-6">
        <h3 className="mb-5 text-sm font-semibold text-gray-200">LangGraph Multi-Agent Flow</h3>
        <div className="flex flex-col items-center gap-0">
          {/* User Query */}
          <div className="rounded-lg border border-gray-700 bg-[#111118] px-6 py-2 text-xs font-medium text-gray-300">User Query</div>
          <div className="h-6 w-px bg-gray-700" />
          <svg className="h-3 w-3 text-gray-500" viewBox="0 0 12 12"><path d="M6 0L12 6H0z" fill="currentColor" transform="rotate(180 6 6)"/></svg>

          {/* Router */}
          <div className="rounded-lg border-2 border-purple-500/40 bg-purple-500/10 px-8 py-3 text-center">
            <div className="text-xs font-bold text-purple-400">Router Agent</div>
            <div className="text-[10px] text-gray-500 mt-0.5">Keyword match + LLM fallback</div>
          </div>

          {/* Branching arrows */}
          <div className="h-6 w-px bg-gray-700" />
          <div className="flex items-start gap-4">
            <div className="flex flex-col items-center w-36 h-full">
              <div className="w-px h-4 bg-gray-700" />
              <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-3 text-center w-full">
                <div className="text-xs font-bold text-blue-400">Enrollment</div>
                <div className="text-[10px] text-gray-500 mt-0.5">7 MCP tools</div>
              </div>
            </div>
            <div className="flex flex-col items-center w-36">
              <div className="w-px h-4 bg-gray-700" />
              <div className="rounded-lg border border-green-500/30 bg-green-500/10 px-4 py-3 text-center w-full">
                <div className="text-xs font-bold text-green-400">Benefits Advisor</div>
                <div className="text-[10px] text-gray-500 mt-0.5">RAG knowledge</div>
              </div>
            </div>
            <div className="flex flex-col items-center w-36">
              <div className="w-px h-4 bg-gray-700" />
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-center w-full">
                <div className="text-xs font-bold text-amber-400">Compliance</div>
                <div className="text-[10px] text-gray-500 mt-0.5">PII + risk scoring</div>
              </div>
            </div>
            <div className="flex flex-col items-center w-36">
              <div className="w-px h-4 bg-gray-700" />
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-center w-full">
                <div className="text-xs font-bold text-red-400">Escalation</div>
                <div className="text-[10px] text-gray-500 mt-0.5">Human-in-loop</div>
              </div>
            </div>
          </div>

          {/* Converge */}
          <div className="h-6 w-px bg-gray-700" />
          <svg className="h-3 w-3 text-gray-500" viewBox="0 0 12 12"><path d="M6 0L12 6H0z" fill="currentColor" transform="rotate(180 6 6)"/></svg>
          <div className="rounded-lg border border-gray-600 bg-gray-500/10 px-8 py-3 text-center">
            <div className="text-xs font-bold text-gray-300">Synthesis Node</div>
            <div className="text-[10px] text-gray-500 mt-0.5">Merge + sanitize + table fix</div>
          </div>
          <div className="h-6 w-px bg-gray-700" />
          <svg className="h-3 w-3 text-gray-500" viewBox="0 0 12 12"><path d="M6 0L12 6H0z" fill="currentColor" transform="rotate(180 6 6)"/></svg>
          <div className="rounded-lg border border-green-500/40 bg-green-500/10 px-6 py-2 text-xs font-medium text-green-400">Response</div>
        </div>
      </div>

      {/* Agent Profiles */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-gray-200">Agent Profiles</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { name: "Router", color: "purple", role: "Classifies user intent and delegates to the appropriate specialist agent.", tools: ["Keyword pattern matching", "LLM classification (fallback)", "Conversation history for context continuity"], model: "Fast (Haiku / llama3.1:8b)" },
            { name: "Enrollment", color: "blue", role: "Handles all enrollment CRUD operations via tool calling.", tools: ["submit_enrollment", "get_enrollment", "list_enrollments_by_status", "get_enrollment_summary", "check_enrollment_status"], model: "Tool-calling (Sonnet / llama3.1:8b)" },
            { name: "Benefits Advisor", color: "green", role: "Answers plan, coverage, eligibility, and policy questions using RAG.", tools: ["Knowledge Service vector search", "Contextual RAG re-query", "Conversation history"], model: "General (Sonnet / llama3.1:8b)" },
            { name: "Compliance", color: "amber", role: "Checks agent actions for PII, policy violations, and risk levels.", tools: ["PII regex detection (6 types)", "Risk factor scoring model", "YAML policy evaluation engine"], model: "General (Sonnet / llama3.1:8b)" },
            { name: "Escalation", color: "red", role: "Routes high-risk or low-confidence requests to human reviewers.", tools: ["Approval queue creation", "Notification dispatch", "Context preservation"], model: "N/A (workflow)" },
            { name: "Synthesis", color: "gray", role: "Merges multi-agent results and sanitizes output for the user.", tools: ["UUID/PII/internal term stripping", "Markdown table repair", "Email redaction", "Compliance warning injection"], model: "N/A (post-processing)" },
          ].map((agent) => (
            <div key={agent.name} className={`rounded-xl border bg-[#111118] p-4 border-${agent.color}-500/20`}>
              <div className={`mb-2 inline-block rounded-full px-2.5 py-0.5 text-[10px] font-bold bg-${agent.color}-500/15 text-${agent.color}-400`}>{agent.name}</div>
              <p className="text-xs text-gray-400 mb-2">{agent.role}</p>
              <div className="text-[10px] text-gray-500 mb-1 font-medium">Tools & Data:</div>
              <ul className="space-y-0.5">
                {agent.tools.map((t) => (
                  <li key={t} className="text-[10px] text-gray-500 flex items-start gap-1">
                    <span className="text-gray-600 mt-0.5">•</span> {t}
                  </li>
                ))}
              </ul>
              <div className="mt-2 text-[10px] text-gray-600">Model: {agent.model}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Request Lifecycle */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-gray-200">Request Lifecycle</h3>
        <div className="relative space-y-0 pl-6">
          <div className="absolute left-[11px] top-2 bottom-2 w-px bg-gray-800" />
          {[
            { step: 1, title: "Input Guardrails", latency: "< 1ms", color: "red", desc: "26 prompt injection patterns + 8 harmful content patterns. Unicode NFKC normalization, leet-speak decoding, 2000 char limit, non-Latin script detection." },
            { step: 2, title: "Router Classification", latency: "< 1ms / ~200ms", color: "purple", desc: "Fast keyword matching for obvious intents (enrollment, compliance, off-topic). Falls back to LLM for ambiguous queries. Checks conversation history for context continuity." },
            { step: 3, title: "Agent Execution", latency: "5-30s", color: "blue", desc: "Specialist agent runs with full conversation history. Enrollment agent calls real APIs via 7 tools. Advisor searches 16 documents via pgvector RAG. Fabrication guard blocks fake employee data." },
            { step: 4, title: "Compliance Post-Check", latency: "< 1ms", color: "amber", desc: "PII detection for 6 types (SSN, email, phone, credit card, DOB, address). Multi-factor risk scoring. Policy evaluation against 10 YAML rules. HIGH+ risk logged for review." },
            { step: 5, title: "Synthesis & Sanitization", latency: "< 1ms", color: "gray", desc: "Merges multi-agent results. Strips UUIDs, PII, internal terms (outbox_event, inbox_message). Fixes malformed markdown tables — adds missing separators, removes code fences, strips extra separator rows." },
            { step: 6, title: "Output Delivery", latency: "—", color: "green", desc: "Final response with agent metadata (agent used, confidence %, compliance risk, latency). Rendered in chatbot with markdown tables, tool call badges, and agent indicators." },
          ].map((s) => (
            <div key={s.step} className="relative flex items-start gap-4 pb-5">
              <div className={`relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-${s.color}-500/20 text-[10px] font-bold text-${s.color}-400 ring-2 ring-[#0a0a0f]`}>{s.step}</div>
              <div className="flex-1 rounded-lg border border-gray-800 bg-[#111118] p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-gray-200">{s.title}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[9px] font-mono bg-${s.color}-500/10 text-${s.color}-400`}>{s.latency}</span>
                </div>
                <p className="text-[11px] text-gray-500 leading-relaxed">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Enrollment State Machine */}
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
                ["Multi-agent routing", "Orchestrator", "Keyword/LLM classification, quality gates, token budgets"],
                ["Audit & compliance", "Governance Service", "Audit trail, PII detection, policy enforcement, approvals"],
                ["Quality evaluation", "Evaluation Service", "Heuristic scoring, benchmark suites"],
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
}
