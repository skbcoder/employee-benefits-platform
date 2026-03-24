"use client";

import { useState, useMemo, Fragment } from "react";
import type { AuditEntry } from "../types";
import { ServiceError } from "./ServiceError";

/* ================================================================== */
/*  HELPERS                                                            */
/* ================================================================== */

function riskBadgeClass(level: string) {
  const styles: Record<string, string> = {
    low: "bg-green-500/15 text-green-400",
    medium: "bg-amber-500/15 text-amber-400",
    high: "bg-red-500/15 text-red-400",
    critical: "bg-red-900/30 text-red-400 font-bold",
  };
  return styles[level] || "bg-gray-500/15 text-gray-400";
}

function effectBadgeClass(effect: string) {
  const styles: Record<string, string> = {
    allow: "bg-green-500/15 text-green-400",
    deny: "bg-red-500/15 text-red-400",
    redact: "bg-amber-500/15 text-amber-400",
    log: "bg-gray-500/15 text-gray-400",
    require_approval: "bg-blue-500/15 text-blue-400",
  };
  return styles[effect] || "bg-gray-500/15 text-gray-400";
}

function relativeTime(ts: string): string {
  try {
    const now = Date.now();
    const then = new Date(ts).getTime();
    const diff = now - then;
    if (diff < 0) return "just now";
    const seconds = Math.floor(diff / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  } catch {
    return ts;
  }
}

function formatTimestamp(ts: string) {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

/* ================================================================== */
/*  ICONS                                                              */
/* ================================================================== */

function IconChevron({ open, className = "h-4 w-4" }: { open: boolean; className?: string }) {
  return (
    <svg className={`${className} transition-transform ${open ? "rotate-90" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
  );
}

function IconDownload({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
    </svg>
  );
}

function IconSearch({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
    </svg>
  );
}

function IconSpinner({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg className={`${className} animate-spin`} fill="none" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" opacity="0.25" />
      <path d="M12 3a9 9 0 0 1 9 9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

/* ================================================================== */
/*  AUDIT DETAIL (expanded row)                                        */
/* ================================================================== */

function AuditDetail({ entry }: { entry: AuditEntry }) {
  return (
    <div className="space-y-4 text-xs">
      {/* Summaries */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="text-gray-500 font-medium mb-1">Request Summary</div>
          <div className="text-gray-300 bg-[#111118] rounded-lg p-3 border border-gray-800">
            {entry.request_summary || "No request summary available"}
          </div>
        </div>
        <div>
          <div className="text-gray-500 font-medium mb-1">Response Summary</div>
          <div className="text-gray-300 bg-[#111118] rounded-lg p-3 border border-gray-800">
            {entry.response_summary || "No response summary available"}
          </div>
        </div>
      </div>

      {/* Policy Decisions */}
      {entry.policy_decisions && entry.policy_decisions.length > 0 && (
        <div>
          <div className="text-gray-500 font-medium mb-2">Policy Decisions</div>
          <div className="space-y-2">
            {entry.policy_decisions.map((pd, i) => (
              <div key={i} className="bg-[#111118] rounded-lg p-3 border border-gray-800">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${pd.allowed ? "bg-green-500/15 text-green-400" : "bg-red-500/15 text-red-400"}`}>
                    {pd.allowed ? "Allowed" : "Denied"}
                  </span>
                  {pd.effects.map((eff, j) => (
                    <span key={j} className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${effectBadgeClass(eff)}`}>
                      {eff}
                    </span>
                  ))}
                </div>
                <div className="text-gray-400 mt-1">{pd.explanation}</div>
                {pd.matched_policies.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {pd.matched_policies.map((mp, k) => (
                      <div key={k} className="flex items-center gap-2 text-gray-500">
                        <span className="font-mono text-[10px] text-gray-400">{mp.policy_id}</span>
                        <span className="text-gray-600">-</span>
                        <span>{mp.description}</span>
                        <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-medium ${effectBadgeClass(mp.effect)}`}>
                          {mp.effect}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PII Detections */}
      {entry.pii_detected && entry.pii_detected.length > 0 && (
        <div>
          <div className="text-gray-500 font-medium mb-2">PII Detected</div>
          <div className="flex flex-wrap gap-2">
            {entry.pii_detected.map((pii, i) => (
              <div key={i} className="bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-1.5 text-amber-400">
                <span className="font-medium">{pii.pii_type}</span>
                <span className="ml-2 text-amber-500/70 font-mono">{pii.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      {entry.metadata && Object.keys(entry.metadata).length > 0 && (
        <div>
          <div className="text-gray-500 font-medium mb-2">Metadata</div>
          <pre className="bg-[#111118] rounded-lg p-3 border border-gray-800 text-gray-400 overflow-x-auto text-[11px] leading-relaxed">
            {JSON.stringify(entry.metadata, null, 2)}
          </pre>
        </div>
      )}

      {/* Extra info row */}
      <div className="flex flex-wrap gap-4 text-gray-500 pt-1">
        <span>Conversation: <span className="font-mono text-gray-400">{entry.conversation_id}</span></span>
        <span>Client IP: <span className="font-mono text-gray-400">{entry.client_ip || "N/A"}</span></span>
        <span>Timestamp: <span className="text-gray-400">{formatTimestamp(entry.timestamp)}</span></span>
      </div>
    </div>
  );
}

/* ================================================================== */
/*  AUDIT TAB                                                          */
/* ================================================================== */

interface AuditTabProps {
  entries: AuditEntry[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function AuditTab({ entries, loading, error, refetch }: AuditTabProps) {
  const [riskFilter, setRiskFilter] = useState("all");
  const [agentFilter, setAgentFilter] = useState("all");
  const [eventFilter, setEventFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [displayCount, setDisplayCount] = useState(25);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    let result = entries;
    if (riskFilter !== "all") result = result.filter((e) => e.risk_level === riskFilter);
    if (agentFilter !== "all") result = result.filter((e) => e.agent === agentFilter);
    if (eventFilter !== "all") result = result.filter((e) => e.event_type === eventFilter);
    if (search.trim()) {
      const q = search.toLowerCase().trim();
      result = result.filter((e) =>
        e.conversation_id?.toLowerCase().includes(q) || e.action?.toLowerCase().includes(q)
      );
    }
    return result;
  }, [entries, riskFilter, agentFilter, eventFilter, search]);

  function exportJson() {
    const blob = new Blob([JSON.stringify(filtered, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `governance-audit-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) return (
    <div className="text-center py-12 text-gray-500">
      <IconSpinner className="mx-auto h-6 w-6 text-gray-400 mb-2" />
      Loading audit trail...
    </div>
  );
  if (error) return <ServiceError onRetry={refetch} context="audit data" />;

  const firstPolicy = (e: AuditEntry): string => {
    if (!e.policy_decisions || e.policy_decisions.length === 0) return "\u2014";
    const mp = e.policy_decisions[0]?.matched_policies;
    if (!mp || mp.length === 0) return "\u2014";
    return mp[0].policy_id;
  };

  const selectClass = "rounded-lg border border-gray-700 bg-[#111118] px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-gray-600";

  return (
    <div className="space-y-4">
      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3">
        <select value={riskFilter} onChange={(e) => { setRiskFilter(e.target.value); setDisplayCount(25); }} className={selectClass}>
          <option value="all">All Risk Levels</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select value={agentFilter} onChange={(e) => { setAgentFilter(e.target.value); setDisplayCount(25); }} className={selectClass}>
          <option value="all">All Agents</option>
          <option value="enrollment">enrollment</option>
          <option value="advisor">advisor</option>
          <option value="compliance">compliance</option>
          <option value="router">router</option>
        </select>
        <select value={eventFilter} onChange={(e) => { setEventFilter(e.target.value); setDisplayCount(25); }} className={selectClass}>
          <option value="all">All Event Types</option>
          <option value="pre_check">pre_check</option>
          <option value="post_review">post_review</option>
          <option value="guardrail_blocked">guardrail_blocked</option>
          <option value="tool_executed">tool_executed</option>
        </select>
        <div className="relative">
          <IconSearch className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-500" />
          <input
            type="text"
            placeholder="Search conversation or action..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setDisplayCount(25); }}
            className="rounded-lg border border-gray-700 bg-[#111118] pl-8 pr-3 py-1.5 text-xs text-gray-300 placeholder:text-gray-600 focus:outline-none focus:border-gray-600 w-64"
          />
        </div>
        <div className="ml-auto flex gap-2">
          <button
            onClick={exportJson}
            className="flex items-center gap-1.5 rounded-lg border border-gray-700 bg-[#111118] px-3 py-1.5 text-xs text-gray-400 hover:bg-gray-800 hover:text-gray-300 transition-colors"
          >
            <IconDownload className="h-3.5 w-3.5" />
            Export JSON
          </button>
          <button
            onClick={refetch}
            className="rounded-lg border border-gray-700 bg-[#111118] px-3 py-1.5 text-xs text-gray-400 hover:bg-gray-800 hover:text-gray-300 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Table */}
      {filtered.length === 0 ? (
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-8 text-center">
          <p className="text-gray-400">No audit entries match the current filters</p>
          <p className="mt-1 text-xs text-gray-600">Try adjusting filters or wait for new agent interactions.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-gray-800 bg-[#111118] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-left text-xs text-gray-500">
                  <th className="px-4 py-3 font-medium w-8"></th>
                  <th className="px-4 py-3 font-medium">Time</th>
                  <th className="px-4 py-3 font-medium">Event</th>
                  <th className="px-4 py-3 font-medium">Agent</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Risk</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium">Policy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {filtered.slice(0, displayCount).map((entry) => {
                  const isExpanded = expandedId === entry.id;
                  return (
                    <Fragment key={entry.id}>
                      <tr
                        onClick={() => setExpandedId(isExpanded ? null : entry.id)}
                        className="text-gray-300 hover:bg-gray-800/30 cursor-pointer"
                      >
                        <td className="pl-4 py-3">
                          <IconChevron open={isExpanded} className="h-3.5 w-3.5 text-gray-500" />
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">{relativeTime(entry.timestamp)}</td>
                        <td className="px-4 py-3 font-mono text-xs">{entry.event_type}</td>
                        <td className="px-4 py-3 text-xs">{entry.agent}</td>
                        <td className="px-4 py-3 text-xs max-w-[200px] truncate">{entry.action}</td>
                        <td className="px-4 py-3">
                          <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${riskBadgeClass(entry.risk_level)}`}>
                            {entry.risk_level}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs">{entry.risk_score?.toFixed(2)}</td>
                        <td className="px-4 py-3 text-xs text-gray-400 max-w-[160px] truncate">{firstPolicy(entry)}</td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={8} className="bg-[#0d0d14] px-6 py-4">
                            <AuditDetail entry={entry} />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
          {filtered.length > displayCount && (
            <button
              onClick={() => setDisplayCount((c) => c + 25)}
              className="w-full py-3 text-sm text-gray-400 hover:text-gray-200 border-t border-gray-800 transition-colors"
            >
              Load more ({filtered.length - displayCount} remaining)
            </button>
          )}
        </div>
      )}
    </div>
  );
}
