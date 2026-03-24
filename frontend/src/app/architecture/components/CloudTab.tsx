import { CLOUD_STAGES } from "../data/cloud";

export default function CloudTab() {
  return (
    <div className="space-y-6">
      {/* Evolution timeline */}
      <div className="space-y-4">
        {CLOUD_STAGES.map((stage, i) => (
          <div key={stage.stage} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold" style={{ backgroundColor: stage.color + "20", color: stage.color, border: `2px solid ${stage.color}40` }}>
                {i + 1}
              </div>
              {i < CLOUD_STAGES.length - 1 && <div className="mt-1 h-full w-px" style={{ backgroundColor: stage.color + "30" }} />}
            </div>
            <div className="flex-1 rounded-xl border bg-[#0d0d14] p-4" style={{ borderColor: stage.color + "25" }}>
              <h3 className="font-semibold" style={{ color: stage.color }}>{stage.stage}</h3>
              <ul className="mt-2 space-y-1">
                {stage.items.map((item, j) => (
                  <li key={j} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="mt-1.5 inline-block h-1.5 w-1.5 rounded-full" style={{ backgroundColor: stage.color + "60" }} />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      {/* Cloud architecture diagram */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-4 text-sm font-semibold text-gray-200">Target Cloud Architecture</h3>
        <div className="overflow-x-auto">
          <svg viewBox="0 0 800 300" className="w-full" style={{ minWidth: 600 }}>
            {/* Nodes */}
            {[
              { x: 20, y: 120, w: 100, h: 44, label: "UI / Client", color: "#3b82f6" },
              { x: 160, y: 60, w: 130, h: 44, label: "Enrollment Service", color: "#22c55e" },
              { x: 160, y: 180, w: 130, h: 44, label: "AI Gateway", color: "#a855f7" },
              { x: 340, y: 60, w: 120, h: 44, label: "EventBridge", color: "#f97316" },
              { x: 340, y: 180, w: 120, h: 44, label: "Knowledge Svc", color: "#a855f7" },
              { x: 510, y: 60, w: 100, h: 44, label: "SQS Queue", color: "#f97316" },
              { x: 510, y: 180, w: 120, h: 44, label: "LLM (Bedrock)", color: "#f97316" },
              { x: 660, y: 60, w: 120, h: 44, label: "Processing Svc", color: "#22c55e" },
              { x: 660, y: 180, w: 120, h: 44, label: "RDS PostgreSQL", color: "#0ea5e9" },
            ].map((n, i) => (
              <g key={i}>
                <rect x={n.x} y={n.y} width={n.w} height={n.h} rx={8} fill="#111118" stroke={n.color + "50"} strokeWidth={1} />
                <rect x={n.x} y={n.y} width={n.w} height={3} rx={1.5} fill={n.color} opacity={0.7} />
                <text x={n.x + n.w / 2} y={n.y + 27} textAnchor="middle" fill="#d1d5db" fontSize="10" fontWeight="600" fontFamily="system-ui">{n.label}</text>
              </g>
            ))}
            {/* Arrows */}
            {[
              "M120,142 L160,82", "M120,142 L160,202",
              "M290,82 L340,82", "M460,82 L510,82", "M610,82 L660,82",
              "M290,82 L290,240 Q290,250 300,250 L650,250 Q660,250 660,240 L660,215",
              "M720,104 L720,180",
              "M290,202 L340,202", "M460,202 L510,202",
              "M160,202 Q140,202 140,180 L140,100 Q140,82 160,82",
            ].map((d, i) => (
              <path key={i} d={d} fill="none" stroke="#374151" strokeWidth={1.2} markerEnd="url(#arr)" />
            ))}
          </svg>
        </div>
      </div>

      {/* Key migration decisions */}
      <div className="rounded-xl border border-gray-800 bg-[#0d0d14] p-5">
        <h3 className="mb-3 text-sm font-semibold text-gray-200">Key Migration Decisions</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            { title: "Publisher Adapter Pattern", desc: "HTTP → EventBridge swap requires only a new adapter implementation + config change. No API or schema changes needed.", color: "#22c55e" },
            { title: "Schema-per-Service", desc: "Physical DB split is possible later — each service already respects schema boundaries with no cross-schema joins.", color: "#3b82f6" },
            { title: "LLM Portability", desc: "Ollama → Bedrock is a client configuration change. AI Gateway abstracts the LLM provider behind a unified interface.", color: "#a855f7" },
            { title: "Saga Orchestration", desc: "orchestration schema is pre-created. Saga tables exist in V1 migration, ready for long-running workflow coordination.", color: "#f97316" },
          ].map((d) => (
            <div key={d.title} className="rounded-lg border border-gray-800 bg-gray-900/20 p-3">
              <h4 className="text-sm font-semibold" style={{ color: d.color }}>{d.title}</h4>
              <p className="mt-1 text-xs text-gray-400">{d.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
