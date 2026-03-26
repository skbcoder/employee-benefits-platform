"""Chat endpoints for the AI Gateway."""

import importlib.util
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from config.settings import settings
from src.models.conversation import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Conversation,
    MessageRole,
)
from src.services.agent_loop import get_rag_context, run_agent_loop
from src.services.audit import log_event
from src.services.guardrails import check_input, check_output
from src.services.orchestrator_client import orchestrate as orchestrator_call
from src.services.rate_limiter import RateLimiter

try:
    _obs_base = Path(__file__).parent.parent.parent.parent / "observability"
    _spec = importlib.util.spec_from_file_location(
        "obs_metrics", _obs_base / "src" / "metrics" / "collector.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _record_token_usage = _mod.record_token_usage
except Exception:
    def _record_token_usage(model: str, tokens: int) -> None:
        pass

router = APIRouter(prefix="/api/ai", tags=["chat"])

# In-memory conversation store (replace with persistent store in production)
_conversations: dict[str, Conversation] = {}

# Rate limiter instance
_rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_rpm,
    window_seconds=settings.rate_limit_window_seconds,
)


def _client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, raw_request: Request):
    """Send a message and get an AI response with tool-augmented reasoning."""
    ip = _client_ip(raw_request)

    # ── Rate limit ──────────────────────────────────────────────────
    if not await _rate_limiter.check(ip):
        log_event("rate_limited", client_ip=ip, message_preview=request.message)
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests. Please wait a moment and try again."},
            headers={"Retry-After": str(_rate_limiter.window_seconds)},
        )

    # ── Get or create conversation ──────────────────────────────────
    if request.conversation_id and request.conversation_id in _conversations:
        conversation = _conversations[request.conversation_id]
    else:
        conv_id = request.conversation_id or str(uuid.uuid4())
        conversation = Conversation(conversation_id=conv_id)
        _conversations[conv_id] = conversation

    conv_id = conversation.conversation_id

    # ── Audit: log incoming request ─────────────────────────────────
    log_event("chat_request", conversation_id=conv_id, client_ip=ip, message_preview=request.message)

    # ── Input guardrail check ───────────────────────────────────────
    guardrail = check_input(request.message)
    if guardrail.blocked:
        log_event(
            "guardrail_blocked",
            conversation_id=conv_id,
            client_ip=ip,
            message_preview=request.message,
            blocked_reason=guardrail.reason,
        )
        conversation.messages.append(ChatMessage(role=MessageRole.USER, content=request.message))
        conversation.messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=guardrail.response))
        conversation.updated_at = datetime.utcnow()
        return ChatResponse(
            conversation_id=conv_id,
            message=guardrail.response,
            tool_calls_made=[],
        )

    # ── Conversation history ────────────────────────────────────────
    history = [
        {"role": msg.role.value, "content": msg.content}
        for msg in conversation.messages
        if msg.role in (MessageRole.USER, MessageRole.ASSISTANT)
    ]

    # ── Orchestrator (Phase 2) or local agent loop ───────────────
    response_text = None
    tool_calls = []
    agent_used = ""
    confidence = 0.0
    compliance_risk = "low"
    latency_ms = 0

    if settings.use_orchestrator:
        result = await orchestrator_call(
            message=request.message,
            conversation_id=conv_id,
            history=history,
        )
        if result is not None:
            response_text = result["response"]
            tool_calls = result["tool_calls"]
            agent_used = result.get("agent_used", "")
            confidence = result.get("confidence", 0.0)
            compliance_risk = result.get("compliance_risk", "low")
            latency_ms = result.get("latency_ms", 0)
            token_usage = result.get("token_usage", {})
            if token_usage:
                model = token_usage.get("model", agent_used or "unknown")
                tokens = token_usage.get("total_tokens", 0)
                if tokens:
                    _record_token_usage(model, tokens)

    # Fallback to local agent loop if orchestrator unavailable
    if response_text is None:
        rag_context = await get_rag_context(request.message)
        response_text, tool_calls = await run_agent_loop(
            messages=history,
            user_message=request.message,
            rag_context=rag_context,
        )

    # ── Output filtering ────────────────────────────────────────────
    filtered_response = check_output(response_text)
    output_was_filtered = filtered_response != response_text
    if output_was_filtered:
        log_event(
            "output_filtered",
            conversation_id=conv_id,
            client_ip=ip,
            response_preview=response_text,
        )

    # ── Store messages ──────────────────────────────────────────────
    conversation.messages.append(ChatMessage(role=MessageRole.USER, content=request.message))
    conversation.messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=filtered_response))
    conversation.updated_at = datetime.utcnow()

    # ── Audit: log outgoing response ────────────────────────────────
    log_event(
        "chat_response",
        conversation_id=conv_id,
        client_ip=ip,
        response_preview=filtered_response,
        tool_calls=tool_calls if tool_calls else None,
        output_filtered=output_was_filtered,
    )

    return ChatResponse(
        conversation_id=conv_id,
        message=filtered_response,
        tool_calls_made=tool_calls,
        agent_used=agent_used,
        confidence=confidence,
        compliance_risk=compliance_risk,
        latency_ms=latency_ms,
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Retrieve conversation history."""
    if conversation_id not in _conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _conversations[conversation_id]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id in _conversations:
        del _conversations[conversation_id]
    return {"status": "deleted"}
