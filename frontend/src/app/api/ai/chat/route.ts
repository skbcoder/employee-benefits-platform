import { NextRequest, NextResponse } from "next/server";

const AI_GATEWAY =
  process.env.AI_GATEWAY_API || "http://localhost:8200";

export async function POST(request: NextRequest) {
  const body = await request.json();

  try {
    const resp = await fetch(`${AI_GATEWAY}/api/ai/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(120_000), // 2 minute timeout
    });

    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "AI Gateway request failed";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}

export async function DELETE(request: NextRequest) {
  const conversationId = request.nextUrl.searchParams.get("conversation_id");

  try {
    const url = conversationId
      ? `${AI_GATEWAY}/api/ai/conversations/${conversationId}`
      : `${AI_GATEWAY}/api/ai/conversations`;

    const resp = await fetch(url, { method: "DELETE" });
    const data = await resp.json();
    return NextResponse.json(data, { status: resp.status });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Failed to clear conversation";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
