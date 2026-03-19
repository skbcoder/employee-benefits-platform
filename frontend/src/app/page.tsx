"use client";

import Link from "next/link";

export default function HomePage() {
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
            Enroll in benefits, track enrollment status, and explore AI-powered tools.
          </p>
        </div>
      </div>

      {/* Action cards — 3-column */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Link
          href="/enroll"
          className="group rounded-xl border border-gray-800 bg-[#111118] p-4 transition-all hover:border-green-500/40 hover:shadow-lg hover:shadow-green-500/5"
        >
          <div className="mb-2.5 flex h-9 w-9 items-center justify-center rounded-lg bg-green-500/15 text-green-400 transition-transform group-hover:scale-110">
            <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h2 className="text-sm font-semibold text-gray-100">New Enrollment</h2>
          <p className="mt-0.5 text-xs text-gray-500">
            Submit benefits enrollment with medical, dental, vision, and life selections.
          </p>
        </Link>

        <Link
          href="/status"
          className="group rounded-xl border border-gray-800 bg-[#111118] p-4 transition-all hover:border-blue-500/40 hover:shadow-lg hover:shadow-blue-500/5"
        >
          <div className="mb-2.5 flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/15 text-blue-400 transition-transform group-hover:scale-110">
            <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h2 className="text-sm font-semibold text-gray-100">Check Status</h2>
          <p className="mt-0.5 text-xs text-gray-500">
            Look up enrollments by ID, employee ID, or name to see processing status.
          </p>
        </Link>

        <Link
          href="/mcp-tools"
          className="group rounded-xl border border-gray-800 bg-[#111118] p-4 transition-all hover:border-purple-500/40 hover:shadow-lg hover:shadow-purple-500/5"
        >
          <div className="mb-2.5 flex h-9 w-9 items-center justify-center rounded-lg bg-purple-500/15 text-purple-400 transition-transform group-hover:scale-110">
            <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75a4.5 4.5 0 01-4.884 4.484c-1.076-.091-2.264.071-2.95.904l-7.152 8.684a2.548 2.548 0 11-3.586-3.586l8.684-7.152c.833-.686.995-1.874.904-2.95a4.5 4.5 0 016.336-4.486l-3.276 3.276a3.004 3.004 0 002.25 2.25l3.276-3.276c.256.565.398 1.192.398 1.852z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.867 19.125h.008v.008h-.008v-.008z" />
            </svg>
          </div>
          <h2 className="text-sm font-semibold text-gray-100">MCP Tools</h2>
          <p className="mt-0.5 text-xs text-gray-500">
            Explore and test the 8 MCP tool definitions exposed by the AI Gateway.
          </p>
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
                href={`/status?filter=${step.status}`}
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
                  <span className={`absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-[#0a0a0f] text-[9px] font-bold ${step.text} ring-1 ring-gray-800`}>
                    {i + 1}
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

      {/* API endpoints — two columns: Platform APIs + AI Platform */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-gray-800 bg-[#111118] p-4 space-y-2.5">
          <h2 className="text-sm font-semibold text-gray-100">Platform APIs</h2>
          <div>
            <h3 className="text-xs font-medium text-gray-400 mb-1">
              Enrollment Service <span className="text-gray-600">:8080</span>
            </h3>
            <ul className="space-y-0.5">
              {[
                ["POST", "/api/enrollments"],
                ["GET", "/api/enrollments/{id}"],
                ["GET", "/api/enrollments/by-employee/{id}"],
                ["GET", "/api/enrollments/by-name/{name}"],
              ].map(([method, path]) => (
                <li key={path} className="flex items-center gap-1.5">
                  <code className={`rounded px-1 py-px text-[10px] font-semibold border ${
                    method === "POST"
                      ? "bg-green-500/10 text-green-400 border-green-500/20"
                      : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                  }`}>
                    {method}
                  </code>
                  <span className="font-mono text-[11px] text-gray-400">{path}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-medium text-gray-400 mb-1">
              Processing Service <span className="text-gray-600">:8081</span>
            </h3>
            <ul className="space-y-0.5">
              {[
                ["GET", "/api/processed-enrollments/{id}"],
                ["GET", "/api/processed-enrollments/by-employee/{id}"],
              ].map(([method, path]) => (
                <li key={path} className="flex items-center gap-1.5">
                  <code className="rounded bg-blue-500/10 px-1 py-px text-[10px] font-semibold text-blue-400 border border-blue-500/20">
                    {method}
                  </code>
                  <span className="font-mono text-[11px] text-gray-400">{path}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="rounded-xl border border-gray-800 bg-[#111118] p-4 space-y-2.5">
          <h2 className="text-sm font-semibold text-gray-100">AI Platform</h2>
          <div>
            <h3 className="text-xs font-medium text-gray-400 mb-1">
              AI Gateway <span className="text-gray-600">:8200</span>
            </h3>
            <ul className="space-y-0.5">
              {[
                ["POST", "/api/ai/chat"],
                ["GET", "/api/ai/tools"],
                ["POST", "/api/ai/tools/execute"],
                ["GET", "/api/ai/health"],
              ].map(([method, path]) => (
                <li key={path} className="flex items-center gap-1.5">
                  <code className={`rounded px-1 py-px text-[10px] font-semibold border ${
                    method === "POST"
                      ? "bg-green-500/10 text-green-400 border-green-500/20"
                      : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                  }`}>
                    {method}
                  </code>
                  <span className="font-mono text-[11px] text-gray-400">{path}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-medium text-gray-400 mb-1">
              Knowledge Service <span className="text-gray-600">:8300</span>
            </h3>
            <ul className="space-y-0.5">
              {[
                ["POST", "/api/knowledge/search"],
                ["POST", "/api/knowledge/documents"],
                ["GET", "/api/knowledge/health"],
              ].map(([method, path]) => (
                <li key={path} className="flex items-center gap-1.5">
                  <code className={`rounded px-1 py-px text-[10px] font-semibold border ${
                    method === "POST"
                      ? "bg-green-500/10 text-green-400 border-green-500/20"
                      : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                  }`}>
                    {method}
                  </code>
                  <span className="font-mono text-[11px] text-gray-400">{path}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-medium text-gray-400 mb-1">
              MCP Server <span className="text-gray-600">:8100</span>
            </h3>
            <ul className="space-y-0.5">
              {[
                ["GET", "/mcp/sse"],
                ["POST", "/mcp/messages"],
              ].map(([method, path]) => (
                <li key={path} className="flex items-center gap-1.5">
                  <code className={`rounded px-1 py-px text-[10px] font-semibold border ${
                    method === "POST"
                      ? "bg-green-500/10 text-green-400 border-green-500/20"
                      : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                  }`}>
                    {method}
                  </code>
                  <span className="font-mono text-[11px] text-gray-400">{path}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
