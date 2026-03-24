import { SCHEMA_TABLES } from "../data/schemas";

export default function DataTab() {
  return (
    <div className="space-y-6">
      {SCHEMA_TABLES.map((schema) => (
        <div key={schema.schema} className="rounded-xl border bg-[#0d0d14] p-5" style={{ borderColor: schema.color + "30" }}>
          <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold">
            <span className="inline-block h-3 w-3 rounded" style={{ backgroundColor: schema.color }} />
            <span style={{ color: schema.color }}>{schema.schema}</span>
            <span className="text-gray-500">schema</span>
          </h3>
          <div className="space-y-4">
            {schema.tables.map((table) => (
              <div key={table.name} className="rounded-lg border border-gray-800 bg-gray-900/20 p-4">
                <h4 className="mb-2 font-mono text-sm font-bold text-gray-200">{table.name}</h4>
                <div className="space-y-0.5">
                  {table.columns.map((col, i) => {
                    const isPK = col.includes("PK");
                    const isFK = col.includes("FK");
                    return (
                      <div key={i} className="flex items-center gap-2 font-mono text-xs">
                        {isPK && <span className="rounded bg-yellow-500/20 px-1 text-yellow-400">PK</span>}
                        {isFK && <span className="rounded bg-blue-500/20 px-1 text-blue-400">FK</span>}
                        <span className={isPK || isFK ? "text-gray-200" : "text-gray-400"}>{col}</span>
                      </div>
                    );
                  })}
                </div>
                {table.indices && (
                  <div className="mt-2 border-t border-gray-800 pt-2">
                    <span className="text-xs text-gray-500">Indices: </span>
                    {table.indices.map((idx, i) => (
                      <span key={i} className="ml-1 rounded bg-gray-800 px-1.5 py-0.5 font-mono text-xs text-gray-400">{idx}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
