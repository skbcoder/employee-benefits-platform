import { NextRequest, NextResponse } from "next/server";

const AI_GATEWAY = process.env.AI_GATEWAY_API || "http://localhost:8200";

export async function POST(request: NextRequest) {
  const body = await request.json();
  try {
    const resp = await fetch(`${AI_GATEWAY}/api/ai/tools/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30_000),
    });
    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Tool execution failed";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
