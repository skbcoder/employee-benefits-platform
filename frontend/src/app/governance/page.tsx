"use client";

import { useState, useEffect, useCallback } from "react";
import type { AuditEntry, ApprovalRequest, GovTab } from "./types";
import { AuditTab } from "./components/AuditTab";
import { ApprovalsTab } from "./components/ApprovalsTab";
import { ComplianceTab } from "./components/ComplianceTab";
import { PoliciesTab } from "./components/PoliciesTab";
import { CostTab } from "./components/CostTab";

/* ================================================================== */
/*  ICONS                                                              */
/* ================================================================== */

function IconActivity({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l2.25-3 2.25 3 3-6 3 6 2.25-3 2.25 3" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 17.25h16.5" />
    </svg>
  );
}

function IconShield({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
    </svg>
  );
}

function IconEye({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function IconChart({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
    </svg>
  );
}

/* ================================================================== */
/*  STAT CARD                                                          */
/* ================================================================== */

function StatCard({ icon, label, value, description }: { icon: React.ReactNode; label: string; value: string; description: string }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-[#111118] p-4">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-100">{value}</div>
      <div className="mt-1 text-[11px] text-gray-600">{description}</div>
    </div>
  );
}

/* ================================================================== */
/*  DATA HOOKS                                                         */
/* ================================================================== */

function useAuditEntries() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/governance/audit");
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();
      const list = data.entries ?? (Array.isArray(data) ? data : []);
      setEntries(list);
      setCount(data.count ?? list.length);
    } catch {
      setError("Governance service unavailable");
      setEntries([]);
      setCount(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch_(); }, [fetch_]);

  return { entries, count, loading, error, refetch: fetch_ };
}

function useApprovals() {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/governance/approvals");
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();
      setApprovals(Array.isArray(data) ? data : []);
    } catch {
      setError("Governance service unavailable");
      setApprovals([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch_(); }, [fetch_]);

  return { approvals, loading, error, refetch: fetch_ };
}

/* ================================================================== */
/*  MAIN PAGE COMPONENT                                                */
/* ================================================================== */

export default function GovernancePage() {
  const [activeTab, setActiveTab] = useState<GovTab>("audit");
  const audit = useAuditEntries();
  const approvals = useApprovals();

  /* Derived stats for header cards */
  const totalRequests = audit.count;
  const piiDetections = audit.entries.filter((e) => e.pii_detected && e.pii_detected.length > 0).length;
  const avgRisk = audit.entries.length > 0
    ? (audit.entries.reduce((sum, e) => sum + (e.risk_score || 0), 0) / audit.entries.length).toFixed(2)
    : "0.00";

  const tabs: { id: GovTab; label: string }[] = [
    { id: "audit", label: "Audit Trail" },
    { id: "approvals", label: "Approvals" },
    { id: "compliance", label: "Compliance" },
    { id: "policies", label: "Policies" },
    { id: "cost", label: "Usage & Cost" },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Governance Dashboard</h1>
        <p className="mt-1 text-sm text-gray-400">
          Real-time monitoring of AI agent actions, compliance policies, and security controls
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          icon={<IconActivity className="h-5 w-5 text-blue-400" />}
          label="Total Requests"
          value={String(totalRequests)}
          description="Total monitored agent interactions"
        />
        <StatCard
          icon={<IconShield className="h-5 w-5 text-green-400" />}
          label="Active Policies"
          value="10"
          description="Governance rules enforced"
        />
        <StatCard
          icon={<IconEye className="h-5 w-5 text-amber-400" />}
          label="PII Detections"
          value={String(piiDetections)}
          description="Personal data instances detected"
        />
        <StatCard
          icon={<IconChart className="h-5 w-5 text-purple-400" />}
          label="Avg Risk Score"
          value={avgRisk}
          description="Mean risk across all actions"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-gray-800">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`pb-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? "border-b-2 border-green-500 text-green-400"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "audit" && <AuditTab entries={audit.entries} loading={audit.loading} error={audit.error} refetch={audit.refetch} />}
      {activeTab === "approvals" && <ApprovalsTab approvals={approvals.approvals} loading={approvals.loading} error={approvals.error} refetch={approvals.refetch} />}
      {activeTab === "compliance" && <ComplianceTab entries={audit.entries} loading={audit.loading} error={audit.error} refetch={audit.refetch} />}
      {activeTab === "policies" && <PoliciesTab />}
      {activeTab === "cost" && <CostTab />}
    </div>
  );
}
