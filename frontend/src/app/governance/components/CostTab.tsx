"use client";

import { useEffect, useState } from "react";

const GRAFANA_URL = "/grafana/d/benefits-ai-platform/ai-platform-benefits-orchestrator?orgId=1&kiosk&theme=dark";

function GrafanaEmbed() {
  const [grafanaUp, setGrafanaUp] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/grafana/api/health", { signal: AbortSignal.timeout(3000) })
      .then((r) => setGrafanaUp(r.ok))
      .catch(() => setGrafanaUp(false));
  }, []);

  if (grafanaUp === null) {
    return (
      <div className="flex items-center justify-center rounded-lg border border-gray-800 bg-[#0a0a0f] h-[500px]">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-700 border-t-green-400" />
      </div>
    );
  }

  if (!grafanaUp) {
    return (
      <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-8 text-center">
        <p className="text-amber-400 font-medium">Grafana Not Running</p>
        <p className="mt-1 text-sm text-gray-500">Start the monitoring stack to view live dashboards:</p>
        <code className="mt-2 block text-xs text-gray-400 bg-gray-900/50 rounded-lg px-4 py-2">
          docker compose -f infrastructure/docker-compose.yml --profile monitoring up -d
        </code>
        <p className="mt-2 text-xs text-gray-600">Grafana will be available at http://localhost:3001</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-800 overflow-hidden">
      <iframe
        src={GRAFANA_URL}
        width="100%"
        height="600"
        frameBorder="0"
        className="bg-[#0a0a0f]"
        title="Grafana Dashboard"
      />
    </div>
  );
}

interface MetricsSummary {
  totalRequests: number;
  totalTokens: number;
  avgDuration: string;
  toolCalls: number;
  guardrailTriggers: number;
  metricsAvailable: boolean;
}

function parsePrometheusValue(text: string, metricName: string, labels?: string): number {
  const pattern = labels
    ? new RegExp(`^${metricName}\\{${labels}\\}\\s+([\\d.e+]+)`, "m")
    : new RegExp(`^${metricName}\\s+([\\d.e+]+)`, "m");
  const match = text.match(pattern);
  return match ? parseFloat(match[1]) : 0;
}

function parsePrometheusTotal(text: string, metricName: string): number {
  const pattern = new RegExp(`^${metricName}\\{[^}]*\\}\\s+([\\d.e+]+)`, "gm");
  let total = 0;
  let match;
  while ((match = pattern.exec(text)) !== null) {
    total += parseFloat(match[1]);
  }
  return total;
}

export function CostTab() {
  const [metrics, setMetrics] = useState<MetricsSummary>({
    totalRequests: 0,
    totalTokens: 0,
    avgDuration: "—",
    toolCalls: 0,
    guardrailTriggers: 0,
    metricsAvailable: false,
  });
  const [loading, setLoading] = useState(true);
  const [raw, setRaw] = useState("");

  useEffect(() => {
    async function fetchMetrics() {
      try {
        // Try orchestrator metrics first
        const res = await fetch("http://localhost:8400/metrics", {
          signal: AbortSignal.timeout(5000),
        });
        if (!res.ok) throw new Error("not ok");
        const text = await res.text();
        setRaw(text);

        const totalReqs = parsePrometheusTotal(text, "agent_request_total");
        const totalTokens = parsePrometheusTotal(text, "agent_token_usage_total");
        const durationSum = parsePrometheusTotal(text, "agent_request_duration_seconds_sum");
        const durationCount = parsePrometheusTotal(text, "agent_request_duration_seconds_count");
        const toolCalls = parsePrometheusTotal(text, "agent_tool_call_total");
        const guardrails = parsePrometheusTotal(text, "agent_guardrail_trigger_total");

        setMetrics({
          totalRequests: Math.round(totalReqs),
          totalTokens: Math.round(totalTokens),
          avgDuration: durationCount > 0 ? `${(durationSum / durationCount * 1000).toFixed(0)}ms` : "—",
          toolCalls: Math.round(toolCalls),
          guardrailTriggers: Math.round(guardrails),
          metricsAvailable: true,
        });
      } catch {
        setMetrics((prev) => ({ ...prev, metricsAvailable: false }));
      } finally {
        setLoading(false);
      }
    }
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-700 border-t-green-400" />
      </div>
    );
  }

  if (!metrics.metricsAvailable) {
    return (
      <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-6 text-center">
        <p className="text-amber-400 font-medium">Metrics Not Available</p>
        <p className="mt-1 text-sm text-gray-500">
          Start the Orchestrator service on port 8400 with observability enabled to view metrics.
        </p>
        <p className="mt-2 text-xs text-gray-600">
          Metrics endpoint: <code className="text-green-400">http://localhost:8400/metrics</code>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Live Metrics Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        {[
          { label: "Total Requests", value: String(metrics.totalRequests), color: "#3b82f6", desc: "Agent interactions processed" },
          { label: "Avg Latency", value: metrics.avgDuration, color: "#a855f7", desc: "Mean response time" },
          { label: "Token Usage", value: metrics.totalTokens > 0 ? metrics.totalTokens.toLocaleString() : "—", color: "#22c55e", desc: "LLM tokens consumed" },
          { label: "Tool Calls", value: String(metrics.toolCalls), color: "#eab308", desc: "API tool invocations" },
          { label: "Guardrail Triggers", value: String(metrics.guardrailTriggers), color: "#ef4444", desc: "Security blocks applied" },
        ].map((m) => (
          <div key={m.label} className="rounded-xl border border-gray-800 bg-[#111118] p-4">
            <div className="text-[10px] text-gray-600 uppercase tracking-wider">{m.label}</div>
            <div className="mt-1 text-2xl font-bold" style={{ color: m.color }}>{m.value}</div>
            <div className="mt-0.5 text-[10px] text-gray-600">{m.desc}</div>
          </div>
        ))}
      </div>

      {/* Cost Model */}
      <div className="rounded-xl border border-gray-800 bg-[#111118] p-5">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">LLM Cost Model</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left text-xs text-gray-500">
                <th className="px-4 py-2 font-medium">Model</th>
                <th className="px-4 py-2 font-medium">Provider</th>
                <th className="px-4 py-2 font-medium">Input (per 1K tokens)</th>
                <th className="px-4 py-2 font-medium">Output (per 1K tokens)</th>
                <th className="px-4 py-2 font-medium">Usage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/50">
              {[
                { model: "Claude 3.5 Haiku", provider: "AWS Bedrock", input: "$0.001", output: "$0.005", usage: "Router classification" },
                { model: "Claude Sonnet 4", provider: "AWS Bedrock", input: "$0.003", output: "$0.015", usage: "Agent execution" },
                { model: "llama3.1:8b", provider: "Ollama (local)", input: "Free", output: "Free", usage: "Local development" },
                { model: "nomic-embed-text", provider: "Ollama (local)", input: "Free", output: "—", usage: "RAG embeddings (768-dim)" },
              ].map((row) => (
                <tr key={row.model} className="text-gray-300">
                  <td className="px-4 py-2 font-mono text-xs">{row.model}</td>
                  <td className="px-4 py-2 text-xs text-gray-400">{row.provider}</td>
                  <td className="px-4 py-2 font-mono text-xs text-green-400">{row.input}</td>
                  <td className="px-4 py-2 font-mono text-xs text-green-400">{row.output}</td>
                  <td className="px-4 py-2 text-xs text-gray-500">{row.usage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Grafana Dashboard (embedded) */}
      <div className="rounded-xl border border-gray-800 bg-[#111118] p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-200">Live Grafana Dashboard</h3>
          <a
            href="http://localhost:3001/d/benefits-ai-platform"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg bg-gray-800 px-3 py-1.5 text-[11px] text-gray-400 hover:text-gray-200 hover:bg-gray-700 transition-colors"
          >
            Open in Grafana
          </a>
        </div>
        <GrafanaEmbed />
        <p className="mt-2 text-[10px] text-gray-600">
          Start monitoring: <code className="text-gray-400">docker compose -f infrastructure/docker-compose.yml --profile monitoring up -d</code>
        </p>
      </div>

      {/* Observability Endpoints */}
      <div className="rounded-xl border border-gray-800 bg-[#111118] p-5">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">Prometheus Endpoints</h3>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {[
            { service: "Orchestrator", port: 8400, metrics: ["agent_request_duration_seconds", "agent_request_total", "agent_tool_call_total", "agent_token_usage_total"] },
            { service: "AI Gateway", port: 8200, metrics: ["agent_request_duration_seconds", "agent_request_total", "agent_guardrail_trigger_total"] },
          ].map((svc) => (
            <div key={svc.port} className="rounded-lg border border-gray-800/50 bg-gray-900/20 p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-300">{svc.service}</span>
                <code className="rounded bg-green-500/10 px-1.5 py-0.5 text-[10px] text-green-400">:{svc.port}/metrics</code>
              </div>
              <div className="flex flex-wrap gap-1">
                {svc.metrics.map((m) => (
                  <span key={m} className="rounded bg-gray-800 px-1.5 py-0.5 text-[9px] font-mono text-gray-500">{m}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
