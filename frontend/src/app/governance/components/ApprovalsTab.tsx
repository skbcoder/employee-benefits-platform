"use client";

import { useState } from "react";
import type { ApprovalRequest } from "../types";
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

function countdownTime(ts: string): string {
  try {
    const now = Date.now();
    const target = new Date(ts).getTime();
    const diff = target - now;
    if (diff <= 0) return "Expired";
    const minutes = Math.floor(diff / 60000);
    if (minutes < 60) return `${minutes}m remaining`;
    const hours = Math.floor(minutes / 60);
    const remainMins = minutes % 60;
    return `${hours}h ${remainMins}m remaining`;
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
/*  APPROVALS TAB                                                      */
/* ================================================================== */

interface ApprovalsTabProps {
  approvals: ApprovalRequest[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function ApprovalsTab({ approvals, loading, error, refetch }: ApprovalsTabProps) {
  const [feedback, setFeedback] = useState<{ id: string; type: "success" | "error"; message: string } | null>(null);
  const [confirmAction, setConfirmAction] = useState<{ id: string; action: "approve" | "deny" } | null>(null);

  const pending = approvals.filter((a) => a.status === "pending");
  const decided = approvals
    .filter((a) => a.status === "approved" || a.status === "denied")
    .sort((a, b) => new Date(b.reviewed_at || b.created_at).getTime() - new Date(a.reviewed_at || a.created_at).getTime())
    .slice(0, 10);

  async function handleAction(id: string, action: "approve" | "deny") {
    try {
      const res = await fetch(`/api/governance/approvals/${id}/${action}`, { method: "POST" });
      if (!res.ok) throw new Error(`Status ${res.status}`);
      setFeedback({ id, type: "success", message: `Request ${action === "approve" ? "approved" : "denied"} successfully` });
      setTimeout(() => setFeedback(null), 3000);
      refetch();
    } catch {
      setFeedback({ id, type: "error", message: `Failed to ${action} request` });
      setTimeout(() => setFeedback(null), 3000);
    }
    setConfirmAction(null);
  }

  if (loading) return (
    <div className="text-center py-12 text-gray-500">
      <IconSpinner className="mx-auto h-6 w-6 text-gray-400 mb-2" />
      Loading approvals...
    </div>
  );
  if (error) return <ServiceError onRetry={refetch} context="approval data" />;

  return (
    <div className="space-y-8">
      {/* Confirmation Dialog */}
      {confirmAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="rounded-xl border border-gray-700 bg-[#111118] p-6 max-w-sm w-full mx-4 shadow-2xl">
            <h3 className="text-sm font-semibold text-gray-200">
              Confirm {confirmAction.action === "approve" ? "Approval" : "Denial"}
            </h3>
            <p className="mt-2 text-xs text-gray-400">
              Are you sure you want to {confirmAction.action} this request? This action cannot be undone.
            </p>
            <div className="mt-4 flex gap-3 justify-end">
              <button
                onClick={() => setConfirmAction(null)}
                className="rounded-lg border border-gray-700 px-4 py-1.5 text-xs text-gray-400 hover:bg-gray-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleAction(confirmAction.id, confirmAction.action)}
                className={`rounded-lg px-4 py-1.5 text-xs font-medium text-white transition-colors ${
                  confirmAction.action === "approve" ? "bg-green-600 hover:bg-green-500" : "bg-red-600 hover:bg-red-500"
                }`}
              >
                {confirmAction.action === "approve" ? "Approve" : "Deny"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pending Approvals */}
      <div>
        <h2 className="text-sm font-semibold text-gray-300 mb-4">
          Pending Approvals {pending.length > 0 && <span className="ml-2 rounded-full bg-amber-500/15 text-amber-400 px-2 py-0.5 text-[10px] font-medium">{pending.length}</span>}
        </h2>
        {pending.length === 0 ? (
          <div className="rounded-xl border border-gray-800 bg-[#111118] p-8 text-center">
            <IconShield className="mx-auto h-8 w-8 text-gray-700 mb-2" />
            <p className="text-gray-400">No pending approvals</p>
            <p className="mt-1 text-xs text-gray-600">Approval requests will appear here when high-risk actions need review.</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {pending.map((a) => (
              <div key={a.id} className="rounded-xl border border-gray-800 bg-[#111118] p-5 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium bg-blue-500/15 text-blue-400 mb-1.5`}>
                      {a.agent}
                    </span>
                    <h3 className="text-sm font-semibold text-gray-200">{a.action}</h3>
                  </div>
                  <div className="text-right">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${riskBadgeClass(a.risk_level)}`}>
                      {a.risk_level}
                    </span>
                    <div className="mt-1 text-[11px] text-gray-500 font-mono">{a.risk_score?.toFixed(2)}</div>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-[11px] text-gray-500">
                  <span>Created {relativeTime(a.created_at)}</span>
                  <span className={`${new Date(a.expires_at).getTime() < Date.now() ? "text-red-400" : "text-amber-400"}`}>
                    {countdownTime(a.expires_at)}
                  </span>
                </div>

                {/* Context / Query */}
                {a.context && Object.keys(a.context).length > 0 ? (
                  <div className="bg-[#0d0d14] rounded-lg p-3 border border-gray-800">
                    {a.context.user_message ? (
                      <div>
                        <div className="text-[10px] text-gray-600 mb-1">Original Query</div>
                        <div className="text-xs text-gray-300">{String(a.context.user_message)}</div>
                      </div>
                    ) : (
                      <div className="text-xs text-gray-400">
                        {Object.entries(a.context).slice(0, 3).map(([k, v]) => (
                          <div key={k} className="flex gap-2">
                            <span className="text-gray-600">{k}:</span>
                            <span className="truncate">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : null}

                {/* Risk factors from context */}
                {a.context?.risk_factors && Array.isArray(a.context.risk_factors) ? (
                  <div className="text-[11px] text-gray-500">
                    <span className="text-gray-600">Risk factors: </span>
                    {(a.context.risk_factors as string[]).join(", ")}
                  </div>
                ) : null}

                {/* Feedback */}
                {feedback?.id === a.id ? (
                  <div className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
                    feedback.type === "success" ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
                  }`}>
                    {feedback.message}
                  </div>
                ) : null}

                {/* Action buttons */}
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => setConfirmAction({ id: a.id, action: "approve" })}
                    className="rounded-lg bg-green-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-green-500 transition-colors"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => setConfirmAction({ id: a.id, action: "deny" })}
                    className="rounded-lg bg-red-600 px-4 py-1.5 text-xs font-medium text-white hover:bg-red-500 transition-colors"
                  >
                    Deny
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Decisions */}
      {decided.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-300 mb-4">Recent Decisions</h2>
          <div className="rounded-xl border border-gray-800 bg-[#111118] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-left text-xs text-gray-500">
                  <th className="px-4 py-3 font-medium">Agent</th>
                  <th className="px-4 py-3 font-medium">Action</th>
                  <th className="px-4 py-3 font-medium">Risk</th>
                  <th className="px-4 py-3 font-medium">Decision</th>
                  <th className="px-4 py-3 font-medium">Reviewer</th>
                  <th className="px-4 py-3 font-medium">Reviewed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/50">
                {decided.map((a) => (
                  <tr key={a.id} className="text-gray-300 hover:bg-gray-800/30">
                    <td className="px-4 py-3 text-xs">{a.agent}</td>
                    <td className="px-4 py-3 text-xs">{a.action}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${riskBadgeClass(a.risk_level)}`}>
                        {a.risk_level}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                        a.status === "approved" ? "bg-green-500/15 text-green-400" : "bg-red-500/15 text-red-400"
                      }`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400">{a.reviewer || "\u2014"}</td>
                    <td className="px-4 py-3 text-xs text-gray-400">{a.reviewed_at ? relativeTime(a.reviewed_at) : "\u2014"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
