import { NextResponse } from "next/server";

const AI_GATEWAY =
  process.env.AI_GATEWAY_API || "http://localhost:8200";

export async function GET() {
  try {
    const resp = await fetch(`${AI_GATEWAY}/api/ai/health`, {
      signal: AbortSignal.timeout(5_000),
    });

    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch {
    return NextResponse.json(
      { status: "unavailable" },
      { status: 503 }
    );
  }
}
