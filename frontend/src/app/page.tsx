"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const STATUSES = ["SUBMITTED", "PROCESSING", "COMPLETED"] as const;

export default function HomePage() {
  const [counts, setCounts] = useState<Record<string, number>>({
    SUBMITTED: 0,
    PROCESSING: 0,
    COMPLETED: 0,
  });

  useEffect(() => {
    async function fetchCounts() {
      for (const status of STATUSES) {
        try {
          const res = await fetch(`/api/enrollments/by-status?status=${status}`);
          if (res.ok) {
            const data = await res.json();
            setCounts((prev) => ({ ...prev, [status]: Array.isArray(data) ? data.length : 0 }));
          }
        } catch {
          // Service unavailable — keep count at 0
        }
      }
    }
    fetchCounts();
  }, []);

  return (
    <div className="space-y-5">
      {/* Compact hero */}
      <div className="flex items-center gap-4 pt-1">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-green-500/15">
          <svg viewBox="0 0 32 32" fill="none" className="h-6 w-6">
            <path
              d="M16 3L5 8v7c0 7.73 4.66 14.96 11 17 6.34-2.04 11-9.27 11-17V8L16 3z"
              fill="#22c55e" opacity="0.3" stroke="#4ade80" strokeWidth="1.5" strokeLinejoin="round"
            />
            <path
              d="M16 22l-1.1-1C11.1 17.7 9 15.8 9 13.5 9 11.6 10.6 10 12.5 10c1.1 0 2.1.5 2.8 1.3L16 12l.7-.7c.7-.8 1.7-1.3 2.8-1.3C21.4 10 23 11.6 23 13.5c0 2.3-2.1 4.2-5.9 7.5L16 22z"
              fill="#4ade80"
            />
          </svg>
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-100">
            Employee Benefits Platform
          </h1>
          <p className="text-sm text-gray-400">
            Enterprise AI-powered enrollment with multi-agent orchestration, governance, and evaluation.
          </p>
        </div>
      </div>

      {/* Quick Actions — 4-column */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Link
          href="/enrollment"
          className="group rounded-xl border border-gray-800 bg-[#111118] p-4 transition-all hover:border-green-500/40 hover:shadow-lg hover:shadow-green-500/5"
        >
          <div className="mb-2.5 flex h-9 w-9 items-center justify-center rounded-lg bg-green-500/15 text-green-400 transition-transform group-hover:scale-110">
            <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h2 className="text-sm font-semibold text-gray-100">New Enrollment</h2>
          <p className="mt-0.5 text-xs text-gray-500">Submit benefits enrollment</p>
        </Link>

        <Link
          href="/enrollment?tab=status"
          className="group rounded-xl border border-gray-800 bg-[#111118] p-4 transition-all hover:border-blue-500/40 hover:shadow-lg hover:shadow-blue-500/5"
        >
          <div className="mb-2.5 flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/15 text-blue-400 transition-transform group-hover:scale-110">
            <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h2 className="text-sm font-semibold text-gray-100">Check Status</h2>
          <p className="mt-0.5 text-xs text-gray-500">Track enrollment status</p>
        </Link>

        <Link
          href="/governance"
          className="group rounded-xl border border-gray-800 bg-[#111118] p-4 transition-all hover:border-amber-500/40 hover:shadow-lg hover:shadow-amber-500/5"
        >
          <div className="mb-2.5 flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/15 text-amber-400 transition-transform group-hover:scale-110">
            <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <h2 className="text-sm font-semibold text-gray-100">Governance</h2>
          <p className="mt-0.5 text-xs text-gray-500">Audit trail & compliance</p>
        </Link>

        <Link
          href="/architecture"
          className="group rounded-xl border border-gray-800 bg-[#111118] p-4 transition-all hover:border-purple-500/40 hover:shadow-lg hover:shadow-purple-500/5"
        >
          <div className="mb-2.5 flex h-9 w-9 items-center justify-center rounded-lg bg-purple-500/15 text-purple-400 transition-transform group-hover:scale-110">
            <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 7.125C2.25 6.504 2.754 6 3.375 6h6c.621 0 1.125.504 1.125 1.125v3.75c0 .621-.504 1.125-1.125 1.125h-6a1.125 1.125 0 01-1.125-1.125v-3.75zM14.25 8.625c0-.621.504-1.125 1.125-1.125h5.25c.621 0 1.125.504 1.125 1.125v8.25c0 .621-.504 1.125-1.125 1.125h-5.25a1.125 1.125 0 01-1.125-1.125v-8.25zM3.75 16.125c0-.621.504-1.125 1.125-1.125h5.25c.621 0 1.125.504 1.125 1.125v2.25c0 .621-.504 1.125-1.125 1.125h-5.25a1.125 1.125 0 01-1.125-1.125v-2.25z" />
            </svg>
          </div>
          <h2 className="text-sm font-semibold text-gray-100">Architecture</h2>
          <p className="mt-0.5 text-xs text-gray-500">System design & diagrams</p>
        </Link>
      </div>

      {/* Enrollment lifecycle — compact */}
      <div className="rounded-xl border border-gray-800 bg-[#111118] px-5 py-4">
        <h2 className="mb-3 text-sm font-semibold text-gray-100">
          Enrollment Lifecycle
        </h2>
        <div className="flex items-center justify-center gap-0">
          {[
            {
              label: "Submitted",
              status: "SUBMITTED",
              desc: "Received & persisted",
              icon: (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              ),
              bg: "bg-blue-500/15",
              text: "text-blue-400",
              glow: "shadow-blue-500/20",
              delay: "0s",
            },
            {
              label: "Processing",
              status: "PROCESSING",
              desc: "Dispatched downstream",
              icon: (
                <svg className="h-4 w-4 animate-spin" style={{ animationDuration: "3s" }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              ),
              bg: "bg-amber-500/15",
              text: "text-amber-400",
              glow: "shadow-amber-500/20",
              delay: "1s",
            },
            {
              label: "Completed",
              status: "COMPLETED",
              desc: "Enrollment finalized",
              icon: (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ),
              bg: "bg-green-500/15",
              text: "text-green-400",
              glow: "shadow-green-500/20",
              delay: "2s",
            },
          ].map((step, i) => (
            <div key={step.label} className="flex items-center">
              {i > 0 && (
                <div className="relative mx-1 flex items-center">
                  <div className="h-0.5 w-12 bg-gray-700/50 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-gray-500 to-gray-400 animate-connector-fill"
                      style={{ animationDelay: `${i * 0.4}s`, animationDuration: "0.8s" }}
                    />
                  </div>
                </div>
              )}
              <Link
                href={`/enrollment?tab=status&filter=${step.status}`}
                className="flex flex-col items-center text-center w-28 animate-step-enter group cursor-pointer"
                style={{ animationDelay: `${i * 0.2}s` }}
              >
                <div
                  className={`relative mb-1.5 flex h-10 w-10 items-center justify-center rounded-xl ${step.bg} ${step.text} shadow-lg ${step.glow} transition-transform group-hover:scale-110`}
                >
                  <div
                    className={`absolute inset-0 rounded-xl ${step.bg} animate-lifecycle-glow`}
                    style={{ animationDelay: step.delay }}
                  />
                  <div className="relative z-10">{step.icon}</div>
                  <span className={`absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-[#0a0a0f] text-[10px] font-bold ${step.text} ring-1 ring-gray-800`}>
                    {counts[step.status] ?? 0}
                  </span>
                </div>
                <span className="text-xs font-medium text-gray-200 group-hover:text-white transition-colors">
                  {step.label}
                </span>
                <span className="text-[10px] text-gray-500">{step.desc}</span>
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* Service Overview — 3-column grid */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {/* Core Services */}
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-100">Core Services</h2>
          {[
            { name: "Enrollment Service", port: 8080, desc: "Enrollment submission & outbox dispatch", color: "#22c55e" },
            { name: "Processing Service", port: 8081, desc: "Event consumption & async processing", color: "#22c55e" },
          ].map((svc) => (
            <div key={svc.port} className="rounded-lg border border-gray-800 bg-gray-900/30 p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-200">{svc.name}</span>
                <code className="rounded px-1.5 py-0.5 text-xs font-bold" style={{ backgroundColor: svc.color + "18", color: svc.color }}>
                  :{svc.port}
                </code>
              </div>
              <p className="mt-1 text-xs text-gray-500">{svc.desc}</p>
            </div>
          ))}
        </div>

        {/* AI Platform */}
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-100">AI Platform</h2>
          {[
            { name: "AI Gateway", port: 8200, desc: "Agent loop & RAG orchestration", color: "#a855f7" },
            { name: "Orchestrator", port: 8400, desc: "Multi-agent routing & quality gates", color: "#a855f7" },
            { name: "MCP Server", port: 8100, desc: "Tool definitions & SSE transport", color: "#a855f7" },
            { name: "Knowledge Service", port: 8300, desc: "RAG search & embeddings", color: "#a855f7" },
          ].map((svc) => (
            <div key={svc.port} className="rounded-lg border border-gray-800 bg-gray-900/30 p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-200">{svc.name}</span>
                <code className="rounded px-1.5 py-0.5 text-xs font-bold" style={{ backgroundColor: svc.color + "18", color: svc.color }}>
                  :{svc.port}
                </code>
              </div>
              <p className="mt-1 text-xs text-gray-500">{svc.desc}</p>
            </div>
          ))}
        </div>

        {/* Governance & Eval */}
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-100">Governance & Eval</h2>
          {[
            { name: "Governance Service", port: 8500, desc: "Audit trail & policy enforcement", color: "#eab308" },
            { name: "Evaluation Service", port: 8600, desc: "Quality scoring & benchmarks", color: "#eab308" },
          ].map((svc) => (
            <div key={svc.port} className="rounded-lg border border-gray-800 bg-gray-900/30 p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-200">{svc.name}</span>
                <code className="rounded px-1.5 py-0.5 text-xs font-bold" style={{ backgroundColor: svc.color + "18", color: svc.color }}>
                  :{svc.port}
                </code>
              </div>
              <p className="mt-1 text-xs text-gray-500">{svc.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
