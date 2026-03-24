"use client";

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

/* ================================================================== */
/*  ICONS                                                              */
/* ================================================================== */

function IconShield({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
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
/*  COMPLIANCE TAB                                                     */
/* ================================================================== */

interface ComplianceTabProps {
  entries: AuditEntry[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function ComplianceTab({ entries, loading, error, refetch }: ComplianceTabProps) {
  if (loading) return (
    <div className="text-center py-12 text-gray-500">
      <IconSpinner className="mx-auto h-6 w-6 text-gray-400 mb-2" />
      Loading compliance data...
    </div>
  );
  if (error) return <ServiceError onRetry={refetch} context="compliance data" />;

  const total = entries.length;
  const blocked = entries.filter((e) => e.event_type === "guardrail_blocked" || e.risk_level === "critical").length;
  const blockedPct = total > 0 ? ((blocked / total) * 100).toFixed(1) : "0.0";
  const piiCount = entries.filter((e) => e.pii_detected && e.pii_detected.length > 0).length;
  const avgRisk = total > 0 ? (entries.reduce((sum, e) => sum + (e.risk_score || 0), 0) / total).toFixed(2) : "0.00";

  const riskDist = {
    low: entries.filter((e) => e.risk_level === "low").length,
    medium: entries.filter((e) => e.risk_level === "medium").length,
    high: entries.filter((e) => e.risk_level === "high").length,
    critical: entries.filter((e) => e.risk_level === "critical").length,
  };
  const riskTotal = riskDist.low + riskDist.medium + riskDist.high + riskDist.critical;

  /* Top policy triggers */
  const policyCounts: Record<string, number> = {};
  entries.forEach((e) => {
    if (e.policy_decisions) {
      e.policy_decisions.forEach((pd) => {
        pd.matched_policies?.forEach((mp) => {
          policyCounts[mp.policy_id] = (policyCounts[mp.policy_id] || 0) + 1;
        });
      });
    }
  });
  const topPolicies = Object.entries(policyCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 8);

  /* Recent violations */
  const violations = entries
    .filter((e) => e.risk_level === "high" || e.risk_level === "critical")
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 10);

  const tooltipClass = "group relative cursor-help";
  const tooltipBubble = "invisible group-hover:visible absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-[10px] text-gray-300 whitespace-nowrap z-10 shadow-lg";

  return (
    <div className="space-y-6">
      {/* Metric Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-4">
          <div className={tooltipClass}>
            <div className="text-xs text-gray-500">Total Requests</div>
            <div className={tooltipBubble}>Total AI agent interactions monitored</div>
          </div>
          <div className="mt-1 text-2xl font-bold text-gray-100">{total}</div>
        </div>
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-4">
          <div className={tooltipClass}>
            <div className="text-xs text-gray-500">Blocked Rate</div>
            <div className={tooltipBubble}>Percentage of requests denied by governance policies</div>
          </div>
          <div className="mt-1 text-2xl font-bold text-red-400">{blockedPct}%</div>
        </div>
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-4">
          <div className={tooltipClass}>
            <div className="text-xs text-gray-500">PII Detections</div>
            <div className={tooltipBubble}>Instances of personal data detected and redacted</div>
          </div>
          <div className="mt-1 text-2xl font-bold text-amber-400">{piiCount}</div>
        </div>
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-4">
          <div className={tooltipClass}>
            <div className="text-xs text-gray-500">Avg Risk Score</div>
            <div className={tooltipBubble}>Mean risk assessment across all monitored actions</div>
          </div>
          <div className="mt-1 text-2xl font-bold text-gray-100">{avgRisk}</div>
        </div>
      </div>

      {/* Middle Row: Risk Distribution + Top Policies */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Risk Distribution */}
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-200">Risk Distribution</h3>
          {riskTotal === 0 ? (
            <p className="text-sm text-gray-500">No data available yet.</p>
          ) : (
            <div className="space-y-3">
              <div className="flex h-5 w-full overflow-hidden rounded-full bg-gray-800">
                {riskDist.low > 0 && (
                  <div
                    className="bg-green-500 transition-all"
                    style={{ width: `${(riskDist.low / riskTotal) * 100}%` }}
                    title={`Low: ${riskDist.low}`}
                  />
                )}
                {riskDist.medium > 0 && (
                  <div
                    className="bg-amber-500 transition-all"
                    style={{ width: `${(riskDist.medium / riskTotal) * 100}%` }}
                    title={`Medium: ${riskDist.medium}`}
                  />
                )}
                {riskDist.high > 0 && (
                  <div
                    className="bg-red-500 transition-all"
                    style={{ width: `${(riskDist.high / riskTotal) * 100}%` }}
                    title={`High: ${riskDist.high}`}
                  />
                )}
                {riskDist.critical > 0 && (
                  <div
                    className="bg-red-800 transition-all"
                    style={{ width: `${(riskDist.critical / riskTotal) * 100}%` }}
                    title={`Critical: ${riskDist.critical}`}
                  />
                )}
              </div>
              <div className="flex flex-wrap gap-4 text-xs text-gray-400">
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-green-500" />
                  Low: {riskDist.low}
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
                  Medium: {riskDist.medium}
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
                  High: {riskDist.high}
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-800" />
                  Critical: {riskDist.critical}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Top Policy Triggers */}
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-5">
          <h3 className="mb-4 text-sm font-semibold text-gray-200">Top Policy Triggers</h3>
          {topPolicies.length === 0 ? (
            <p className="text-sm text-gray-500">No policy triggers recorded yet.</p>
          ) : (
            <div className="space-y-2">
              {topPolicies.map(([policyId, count]) => {
                const maxCount = topPolicies[0][1];
                return (
                  <div key={policyId} className="flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-gray-300 font-mono truncate">{policyId}</span>
                        <span className="text-xs text-gray-500 ml-2">{count}</span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-gray-800 overflow-hidden">
                        <div
                          className="h-full bg-blue-500/60 rounded-full transition-all"
                          style={{ width: `${(count / maxCount) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent Violations */}
      <div className="rounded-xl border border-gray-800 bg-[#111118] overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h3 className="text-sm font-semibold text-gray-200">Recent Violations</h3>
          <p className="text-[11px] text-gray-500 mt-0.5">Last 10 entries with high or critical risk level</p>
        </div>
        {violations.length === 0 ? (
          <div className="p-8 text-center">
            <IconShield className="mx-auto h-8 w-8 text-green-800 mb-2" />
            <p className="text-sm text-gray-500">No violations detected</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-left text-xs text-gray-500">
                  <th className="px-4 py-3 font-medium">Time</th>
                  <th className="px-4 py-3 font-medium">Event</th>
                  <th className="px-4 py-3 font-medium">Agent</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Risk</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {violations.map((e) => (
                  <tr key={e.id} className="text-gray-300 hover:bg-gray-800/30">
                    <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">{relativeTime(e.timestamp)}</td>
                    <td className="px-4 py-3 font-mono text-xs">{e.event_type}</td>
                    <td className="px-4 py-3 text-xs">{e.agent}</td>
                    <td className="px-4 py-3 text-xs max-w-[200px] truncate">{e.action}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${riskBadgeClass(e.risk_level)}`}>
                        {e.risk_level}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{e.risk_score?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
