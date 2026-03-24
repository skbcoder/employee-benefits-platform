"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { SERVICES, CONNECTIONS, FLOW_STEPS } from "../data/services";
import type { ServiceNode, ServiceStatus } from "../data/services";

const HEALTH_PATHS: Record<number, string> = {
  8080: "/actuator/health",
  8081: "/actuator/health",
  8100: "/health",
  8200: "/api/ai/health",
  8300: "/health",
  8400: "/health",
  8500: "/health",
  8600: "/health",
};

const GROUP_META: Record<string, { label: string; color: string; icon: string }> = {
  frontend: { label: "Frontend", color: "#3b82f6", icon: "M" },
  backend: { label: "Backend Services", color: "#22c55e", icon: "S" },
  ai: { label: "AI Platform", color: "#a855f7", icon: "A" },
  infra: { label: "Infrastructure", color: "#0ea5e9", icon: "I" },
};

const STATUS_COLORS: Record<ServiceStatus, string> = {
  healthy: "#22c55e",
  degraded: "#eab308",
  down: "#ef4444",
  idle: "#6b7280",
};

function center(s: ServiceNode) {
  return { x: s.x + s.w / 2, y: s.y + s.h / 2 };
}

function edgePoint(s: ServiceNode, target: { x: number; y: number }) {
  const c = center(s);
  const dx = target.x - c.x;
  const dy = target.y - c.y;
  const hw = s.w / 2;
  const hh = s.h / 2;

  if (dx === 0 && dy === 0) return c;

  const scaleX = hw / Math.abs(dx || 1);
  const scaleY = hh / Math.abs(dy || 1);
  const scale = Math.min(scaleX, scaleY);

  return { x: c.x + dx * scale, y: c.y + dy * scale };
}

function computePath(from: ServiceNode, to: ServiceNode): string {
  const fc = center(from);
  const tc = center(to);
  const a = edgePoint(from, tc);
  const b = edgePoint(to, fc);

  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2;
  const cx = mx + (b.y - a.y) * 0.08;
  const cy = my - (b.x - a.x) * 0.08;

  return `M${a.x},${a.y} Q${cx},${cy} ${b.x},${b.y}`;
}

export default function DeploymentTab() {
  const [selected, setSelected] = useState<string | null>(null);
  const [flowStep, setFlowStep] = useState<number | null>(null);
  const [activeGroup, setActiveGroup] = useState<string | null>(null);
  const [liveHealth, setLiveHealth] = useState<Record<number, ServiceStatus>>({});

  // Fetch real health status for each service on mount
  useEffect(() => {
    async function checkHealth() {
      for (const [portStr, path] of Object.entries(HEALTH_PATHS)) {
        const port = Number(portStr);
        try {
          const res = await fetch(`http://localhost:${port}${path}`, {
            signal: AbortSignal.timeout(3000),
          });
          setLiveHealth((prev) => ({ ...prev, [port]: res.ok ? "healthy" : "down" }));
        } catch {
          setLiveHealth((prev) => ({ ...prev, [port]: "down" }));
        }
      }
    }
    checkHealth();
  }, []);

  // Resolve live health status for a service (falls back to hardcoded)
  const getStatus = (svc: ServiceNode): ServiceStatus => {
    const port = typeof svc.port === "number" ? svc.port : parseInt(String(svc.port), 10);
    return liveHealth[port] || svc.status;
  };
  const detailRef = useRef<HTMLDivElement>(null);

  const selectedService = SERVICES.find((s) => s.id === selected) ?? null;
  const currentFlow = flowStep !== null ? FLOW_STEPS[flowStep] : null;

  const isNodeHighlighted = useCallback(
    (id: string) => {
      if (currentFlow) return currentFlow.active.includes(id);
      if (activeGroup) return SERVICES.find((s) => s.id === id)?.group === activeGroup;
      return true;
    },
    [currentFlow, activeGroup]
  );

  const isConnHighlighted = useCallback(
    (idx: number) => {
      if (currentFlow) return currentFlow.activeConns.includes(idx);
      if (activeGroup) {
        const conn = CONNECTIONS[idx];
        const fromG = SERVICES.find((s) => s.id === conn.from)?.group;
        const toG = SERVICES.find((s) => s.id === conn.to)?.group;
        return fromG === activeGroup || toG === activeGroup;
      }
      return true;
    },
    [currentFlow, activeGroup]
  );

  const handleNodeClick = (id: string) => {
    setSelected(selected === id ? null : id);
    if (selected !== id) {
      setTimeout(() => detailRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 100);
    }
  };

  return (
    <div className="space-y-5">
      {/* Group filters */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => { setActiveGroup(null); setFlowStep(null); }}
          className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${activeGroup === null && flowStep === null ? "bg-gray-700 text-gray-100" : "bg-gray-800/50 text-gray-500 hover:text-gray-300"}`}
        >
          All Services
        </button>
        {Object.entries(GROUP_META).map(([key, { label, color }]) => (
          <button
            key={key}
            onClick={() => { setActiveGroup(activeGroup === key ? null : key); setFlowStep(null); setSelected(null); }}
            className="rounded-full px-3 py-1.5 text-xs font-medium transition"
            style={{
              backgroundColor: activeGroup === key ? color + "20" : "rgba(255,255,255,0.04)",
              color: activeGroup === key ? color : "#9ca3af",
              border: `1px solid ${activeGroup === key ? color + "40" : "transparent"}`,
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Flow stepper */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-4">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Request Flow Trace</span>
          <div className="flex gap-2">
            {currentFlow && (
              <span className="rounded-md bg-green-500/10 px-2 py-0.5 text-xs font-mono text-green-400">
                {currentFlow.status}
              </span>
            )}
            {flowStep !== null && (
              <button onClick={() => { setFlowStep(null); setSelected(null); }} className="text-xs text-gray-500 hover:text-gray-300">Clear</button>
            )}
          </div>
        </div>
        <div className="grid grid-cols-5 gap-2">
          {FLOW_STEPS.map((step, i) => (
            <button
              key={i}
              onClick={() => { setFlowStep(flowStep === i ? null : i); setActiveGroup(null); setSelected(null); }}
              className="rounded-lg px-2 py-2.5 text-left text-xs transition"
              style={{
                backgroundColor: flowStep === i ? "#22c55e12" : "rgba(255,255,255,0.02)",
                border: `1px solid ${flowStep === i ? "#22c55e40" : "#1f2937"}`,
                color: flowStep === i ? "#4ade80" : "#9ca3af",
              }}
            >
              <span className="font-bold">{step.title}</span>
            </button>
          ))}
        </div>
        {currentFlow && (
          <p className="mt-3 text-sm leading-relaxed text-gray-300">{currentFlow.desc}</p>
        )}
      </div>

      {/* SVG Diagram */}
      <div className="overflow-x-auto rounded-xl border border-gray-800 bg-[#080810] p-2">
        <svg viewBox="0 0 1020 700" className="w-full" style={{ minWidth: 800 }}>
          <defs>
            <marker id="arr" viewBox="0 0 10 6" refX="9" refY="3" markerWidth="7" markerHeight="5" orient="auto-start-reverse">
              <path d="M0,0 L10,3 L0,6Z" fill="#4b5563" />
            </marker>
            <marker id="arr-g" viewBox="0 0 10 6" refX="9" refY="3" markerWidth="7" markerHeight="5" orient="auto-start-reverse">
              <path d="M0,0 L10,3 L0,6Z" fill="#4ade80" />
            </marker>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          {/* Group backgrounds */}
          <rect x="350" y="6" width="290" height="170" rx="16" fill="#3b82f608" stroke="#3b82f615" strokeWidth="1" />
          <text x="365" y="168" fill="#3b82f640" fontSize="9" fontFamily="monospace">FRONTEND</text>
          <rect x="120" y="220" width="760" height="100" rx="16" fill="#22c55e06" stroke="#22c55e12" strokeWidth="1" />
          <text x="135" y="310" fill="#22c55e35" fontSize="9" fontFamily="monospace">BACKEND SERVICES</text>
          <rect x="80" y="378" width="910" height="170" rx="16" fill="#a855f706" stroke="#a855f712" strokeWidth="1" />
          <text x="95" y="540" fill="#a855f735" fontSize="9" fontFamily="monospace">AI PLATFORM</text>
          <rect x="350" y="580" width="290" height="110" rx="16" fill="#0ea5e906" stroke="#0ea5e912" strokeWidth="1" />
          <text x="365" y="682" fill="#0ea5e935" fontSize="9" fontFamily="monospace">INFRASTRUCTURE</text>

          {/* Connections */}
          {CONNECTIONS.map((conn, i) => {
            const from = SERVICES.find((s) => s.id === conn.from)!;
            const to = SERVICES.find((s) => s.id === conn.to)!;
            const path = computePath(from, to);
            const hl = isConnHighlighted(i);
            const dimmed = (currentFlow || activeGroup) && !hl;

            return (
              <g key={i} style={{ opacity: dimmed ? 0.07 : 1, transition: "opacity 0.3s" }}>
                <path
                  d={path}
                  fill="none"
                  stroke={hl && currentFlow ? "#4ade80" : "#374151"}
                  strokeWidth={hl && currentFlow ? 2.5 : 1.2}
                  strokeDasharray={conn.style === "dashed" ? "6,4" : undefined}
                  markerEnd={hl && currentFlow ? "url(#arr-g)" : "url(#arr)"}
                />
              </g>
            );
          })}

          {/* Service nodes */}
          {SERVICES.map((svc) => {
            const hl = isNodeHighlighted(svc.id);
            const dimmed = (currentFlow || activeGroup) && !hl;
            const isSel = selected === svc.id;

            return (
              <g
                key={svc.id}
                onClick={() => handleNodeClick(svc.id)}
                style={{ cursor: "pointer", opacity: dimmed ? 0.1 : 1, transition: "opacity 0.3s" }}
              >
                {isSel && (
                  <rect x={svc.x - 3} y={svc.y - 3} width={svc.w + 6} height={svc.h + 6} rx={12} fill="none" stroke={svc.color} strokeWidth={2} opacity={0.6} filter="url(#glow)" />
                )}
                <rect x={svc.x} y={svc.y} width={svc.w} height={svc.h} rx={10} fill="#111118" stroke={isSel ? svc.color : "#1e293b"} strokeWidth={isSel ? 1.5 : 0.8} />
                <rect x={svc.x} y={svc.y} width={svc.w} height={3} rx={1.5} fill={svc.color} opacity={0.8} />
                <circle cx={svc.x + svc.w - 12} cy={svc.y + 14} r={3.5} fill={STATUS_COLORS[getStatus(svc)]} />
                <text x={svc.x + 12} y={svc.y + 22} fill="#e5e7eb" fontSize="11" fontWeight="600" fontFamily="system-ui, sans-serif">{svc.label}</text>
                <text x={svc.x + 12} y={svc.y + 37} fill="#6b7280" fontSize="9" fontFamily="monospace">
                  {svc.port ? `:${svc.port}` : ""}{svc.port && svc.subtitle ? " · " : ""}{svc.subtitle}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Detail panel */}
      <div ref={detailRef}>
        {selectedService && (
          <div className="rounded-xl border p-5 transition-all" style={{ borderColor: selectedService.color + "30", backgroundColor: selectedService.color + "06" }}>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-bold text-gray-100">{selectedService.label}</h2>
                <div className="mt-1 flex items-center gap-2">
                  <span className="rounded-full px-2 py-0.5 text-xs font-medium" style={{ backgroundColor: selectedService.color + "18", color: selectedService.color }}>{selectedService.group}</span>
                  <span className="flex items-center gap-1.5 text-xs text-gray-400">
                    <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: STATUS_COLORS[getStatus(selectedService)] }} />
                    {getStatus(selectedService)}
                  </span>
                  {selectedService.port && <code className="rounded bg-gray-800 px-1.5 py-0.5 text-xs text-gray-300">:{selectedService.port}</code>}
                </div>
              </div>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-gray-300">{selectedService.description}</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">Technology</h3>
                <p className="text-sm text-gray-300">{selectedService.tech}</p>
              </div>
              {selectedService.schemas && (
                <div>
                  <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">DB Schemas</h3>
                  {selectedService.schemas.map((s, i) => <p key={i} className="font-mono text-xs text-gray-400">{s}</p>)}
                </div>
              )}
            </div>
            {selectedService.endpoints && (
              <div className="mt-4">
                <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">Endpoints</h3>
                <div className="grid gap-0.5 sm:grid-cols-2">
                  {selectedService.endpoints.map((ep, i) => <span key={i} className="font-mono text-xs text-gray-400">{ep}</span>)}
                </div>
              </div>
            )}
            {selectedService.config && (
              <div className="mt-4">
                <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">Configuration</h3>
                <div className="grid gap-1 sm:grid-cols-2">
                  {Object.entries(selectedService.config).map(([k, v]) => (
                    <div key={k} className="flex gap-2 text-xs">
                      <span className="text-gray-500">{k}:</span>
                      <span className="font-mono text-gray-300">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="mt-4">
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">Connections</h3>
              <div className="flex flex-wrap gap-1.5">
                {CONNECTIONS.filter((c) => c.from === selectedService.id || c.to === selectedService.id).map((c, i) => {
                  const other = c.from === selectedService.id ? c.to : c.from;
                  const otherSvc = SERVICES.find((s) => s.id === other);
                  const dir = c.from === selectedService.id ? "\u2192" : "\u2190";
                  return (
                    <span key={i} className="rounded-md bg-gray-800/60 px-2 py-1 text-xs text-gray-300">
                      {dir} {otherSvc?.label} <span className="text-gray-500">({c.protocol})</span>
                    </span>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-5 rounded-lg border border-gray-800/50 bg-[#0d0d14] px-4 py-2.5 text-xs text-gray-500">
        {Object.entries(STATUS_COLORS).map(([s, c]) => (
          <span key={s} className="flex items-center gap-1.5"><span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: c }} />{s}</span>
        ))}
        <span className="ml-2 border-l border-gray-800 pl-3">Click nodes for details</span>
        <span>Use flow stepper to trace requests</span>
      </div>
    </div>
  );
}
