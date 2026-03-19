"use client";

import { useState, useEffect } from "react";

interface ToolParameter {
  type: string;
  description?: string;
  enum?: string[];
  items?: { type: string; properties?: Record<string, ToolParameter>; required?: string[] };
}

interface ToolSchema {
  type: string;
  properties: Record<string, ToolParameter>;
  required: string[];
}

interface MCPTool {
  name: string;
  description: string;
  parameters: ToolSchema;
}

export default function MCPToolsPage() {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [resultError, setResultError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/ai/tools")
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load tools (${res.status})`);
        return res.json();
      })
      .then((data) => {
        setTools(data.tools || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load tools");
        setLoading(false);
      });
  }, []);

  function selectTool(tool: MCPTool) {
    setSelectedTool(tool);
    setFormValues({});
    setResult(null);
    setResultError(null);
  }

  function buildArguments(tool: MCPTool): Record<string, unknown> {
    const args: Record<string, unknown> = {};
    const props = tool.parameters.properties;

    for (const [key, schema] of Object.entries(props)) {
      const value = formValues[key];
      if (!value && value !== "") continue;
      if (!value) continue;

      if (schema.type === "array") {
        try {
          args[key] = JSON.parse(value);
        } catch {
          args[key] = value;
        }
      } else {
        args[key] = value;
      }
    }
    return args;
  }

  async function handleExecute(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTool) return;

    setExecuting(true);
    setResult(null);
    setResultError(null);

    try {
      const args = buildArguments(selectedTool);
      const res = await fetch("/api/ai/tools/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: selectedTool.name, arguments: args }),
      });

      const data = await res.json();
      if (!res.ok) {
        setResultError(data.error || `Request failed with status ${res.status}`);
      } else {
        // result comes back as a JSON string from the backend
        try {
          const parsed = JSON.parse(data.result);
          setResult(JSON.stringify(parsed, null, 2));
        } catch {
          setResult(data.result);
        }
      }
    } catch (err) {
      setResultError(err instanceof Error ? err.message : "Execution failed");
    } finally {
      setExecuting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <svg className="h-6 w-6 animate-spin text-gray-400" fill="none" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" opacity="0.25" />
          <path d="M12 3a9 9 0 0 1 9 9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        </svg>
        <span className="ml-3 text-gray-400">Loading MCP tools...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">MCP Tools</h1>
          <p className="mt-1 text-sm text-gray-400">
            Explore and test MCP tool definitions exposed by the AI Gateway.
          </p>
        </div>
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          {error}
        </div>
        <p className="text-sm text-gray-500">
          Make sure the AI Gateway is running on port 8200.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">MCP Tools</h1>
        <p className="mt-1 text-sm text-gray-400">
          Explore and test the {tools.length} MCP tool definitions exposed by the AI Gateway.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Tool list */}
        <div className="lg:col-span-2 space-y-2">
          {tools.map((tool) => (
            <button
              key={tool.name}
              onClick={() => selectTool(tool)}
              className={`w-full rounded-xl border p-4 text-left transition-colors ${
                selectedTool?.name === tool.name
                  ? "border-green-500/50 bg-green-500/10"
                  : "border-gray-800 bg-[#111118] hover:border-gray-700 hover:bg-[#16161f]"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/15 text-purple-400">
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17l-5.25-3.03a.75.75 0 010-1.28l5.25-3.03a.75.75 0 011.08.67v6.06a.75.75 0 01-1.08.67z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 12a8.25 8.25 0 11-16.5 0 8.25 8.25 0 0116.5 0z" />
                  </svg>
                </span>
                <span className="font-mono text-sm font-medium text-gray-200">
                  {tool.name}
                </span>
              </div>
              <p className="mt-2 text-xs text-gray-400 line-clamp-2">
                {tool.description}
              </p>
            </button>
          ))}
        </div>

        {/* Tool detail + execution panel */}
        <div className="lg:col-span-3 space-y-4">
          {!selectedTool ? (
            <div className="rounded-xl border border-gray-800 bg-[#111118] p-12 text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-purple-500/10">
                <svg className="h-6 w-6 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17l-5.25-3.03a.75.75 0 010-1.28l5.25-3.03a.75.75 0 011.08.67v6.06a.75.75 0 01-1.08.67zM20.25 12a8.25 8.25 0 11-16.5 0 8.25 8.25 0 0116.5 0z" />
                </svg>
              </div>
              <p className="text-sm text-gray-400">Select a tool to view its schema and test it.</p>
            </div>
          ) : (
            <>
              {/* Tool info */}
              <div className="rounded-xl border border-gray-800 bg-[#111118] p-6 space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-mono text-lg font-semibold text-gray-100">
                      {selectedTool.name}
                    </h2>
                    <p className="mt-1 text-sm text-gray-400">
                      {selectedTool.description}
                    </p>
                  </div>
                  <span className="shrink-0 rounded-md bg-purple-500/15 px-2 py-1 text-xs font-medium text-purple-400">
                    MCP Tool
                  </span>
                </div>

                {/* Parameters schema */}
                <div>
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Parameters</h3>
                  <div className="rounded-lg border border-gray-700/50 bg-[#0a0a0f] overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-700/50">
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Name</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Type</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Required</th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">Description</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-800/50">
                        {Object.entries(selectedTool.parameters.properties).map(([name, schema]) => (
                          <tr key={name}>
                            <td className="px-3 py-2 font-mono text-gray-200">{name}</td>
                            <td className="px-3 py-2">
                              <span className="rounded bg-gray-800 px-1.5 py-0.5 text-xs text-gray-300">
                                {schema.type}
                              </span>
                              {schema.enum && (
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {schema.enum.map((v) => (
                                    <span key={v} className="rounded bg-amber-500/10 px-1.5 py-0.5 text-xs text-amber-400">
                                      {v}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </td>
                            <td className="px-3 py-2">
                              {selectedTool.parameters.required?.includes(name) ? (
                                <span className="text-xs text-green-400">yes</span>
                              ) : (
                                <span className="text-xs text-gray-600">no</span>
                              )}
                            </td>
                            <td className="px-3 py-2 text-xs text-gray-400">
                              {schema.description || "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Execution form */}
              <div className="rounded-xl border border-gray-800 bg-[#111118] p-6 space-y-4">
                <h3 className="font-semibold text-gray-100">Test Tool</h3>
                <form onSubmit={handleExecute} className="space-y-3">
                  {Object.entries(selectedTool.parameters.properties).map(([name, schema]) => {
                    const isRequired = selectedTool.parameters.required?.includes(name);
                    return (
                      <div key={name}>
                        <label className="mb-1 flex items-center gap-2 text-sm font-medium text-gray-300">
                          <span className="font-mono">{name}</span>
                          {isRequired && <span className="text-red-400 text-xs">*</span>}
                          <span className="text-xs text-gray-600">({schema.type})</span>
                        </label>
                        {schema.enum ? (
                          <select
                            value={formValues[name] || ""}
                            onChange={(e) => setFormValues({ ...formValues, [name]: e.target.value })}
                            required={isRequired}
                            className="w-full rounded-lg border border-gray-700 bg-[#0a0a0f] px-3 py-2 text-sm text-gray-200 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
                          >
                            <option value="">Select {name}...</option>
                            {schema.enum.map((v) => (
                              <option key={v} value={v}>{v}</option>
                            ))}
                          </select>
                        ) : schema.type === "array" ? (
                          <textarea
                            value={formValues[name] || ""}
                            onChange={(e) => setFormValues({ ...formValues, [name]: e.target.value })}
                            required={isRequired}
                            rows={4}
                            placeholder={`JSON array, e.g. ${getArrayPlaceholder(schema)}`}
                            className="w-full rounded-lg border border-gray-700 bg-[#0a0a0f] px-3 py-2 font-mono text-sm text-gray-200 placeholder-gray-600 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
                          />
                        ) : (
                          <input
                            type="text"
                            value={formValues[name] || ""}
                            onChange={(e) => setFormValues({ ...formValues, [name]: e.target.value })}
                            required={isRequired}
                            placeholder={schema.description || `Enter ${name}...`}
                            className="w-full rounded-lg border border-gray-700 bg-[#0a0a0f] px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
                          />
                        )}
                      </div>
                    );
                  })}

                  <button
                    type="submit"
                    disabled={executing}
                    className="w-full rounded-lg bg-green-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-green-500 disabled:opacity-50"
                  >
                    {executing ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" opacity="0.25" />
                          <path d="M12 3a9 9 0 0 1 9 9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
                        </svg>
                        Executing...
                      </span>
                    ) : (
                      "Execute Tool"
                    )}
                  </button>
                </form>
              </div>

              {/* Result */}
              {resultError && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
                  {resultError}
                </div>
              )}

              {result && (
                <div className="rounded-xl border border-gray-800 bg-[#111118] p-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-gray-100">Result</h3>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(result);
                      }}
                      className="rounded-lg border border-gray-700 px-2.5 py-1 text-xs text-gray-400 hover:bg-gray-800 hover:text-gray-300"
                    >
                      Copy
                    </button>
                  </div>
                  <pre className="max-h-96 overflow-auto rounded-lg border border-gray-700/50 bg-[#0a0a0f] p-4 font-mono text-sm text-gray-300">
                    {result}
                  </pre>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function getArrayPlaceholder(schema: ToolParameter): string {
  if (schema.items?.properties) {
    const example: Record<string, string> = {};
    for (const [key, prop] of Object.entries(schema.items.properties)) {
      if (prop.enum) {
        example[key] = prop.enum[0];
      } else {
        example[key] = `<${prop.type || "string"}>`;
      }
    }
    return JSON.stringify([example]);
  }
  return "[]";
}
