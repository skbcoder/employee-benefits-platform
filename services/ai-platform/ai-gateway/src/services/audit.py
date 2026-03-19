"""Structured audit logging for AI Gateway security events."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from config.settings import settings

# Dedicated audit logger — writes structured JSON to a separate log file
_audit_logger = logging.getLogger("audit")
_audit_logger.setLevel(logging.INFO)
_audit_logger.propagate = False  # Don't pollute the main logger

_handler: logging.Handler | None = None


def _ensure_handler() -> None:
    """Lazily attach a file handler on first use."""
    global _handler
    if _handler is not None:
        return
    _handler = logging.FileHandler(settings.audit_log_file, encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(message)s"))  # raw JSON lines
    _audit_logger.addHandler(_handler)


def log_event(
    event_type: str,
    *,
    conversation_id: str | None = None,
    client_ip: str | None = None,
    message_preview: str | None = None,
    response_preview: str | None = None,
    blocked_reason: str | None = None,
    tool_calls: list[str] | None = None,
    output_filtered: bool = False,
    extra: dict[str, Any] | None = None,
) -> None:
    """Write a structured JSON audit event.

    Event types:
        chat_request     — every incoming chat message
        chat_response    — every outgoing response
        guardrail_blocked — input guardrail rejected the message
        rate_limited     — request rejected due to rate limit
        output_filtered  — LLM response was replaced by safe fallback
        tool_executed    — an MCP tool was invoked
        rag_sanitized    — RAG content had poisoned lines stripped
    """
    _ensure_handler()

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
    }

    if conversation_id:
        entry["conversation_id"] = conversation_id
    if client_ip:
        entry["client_ip"] = client_ip
    if message_preview:
        entry["message_preview"] = message_preview[:200]
    if response_preview:
        entry["response_preview"] = response_preview[:200]
    if blocked_reason:
        entry["blocked_reason"] = blocked_reason
    if tool_calls:
        entry["tool_calls"] = tool_calls
    if output_filtered:
        entry["output_filtered"] = True
    if extra:
        entry.update(extra)

    _audit_logger.info(json.dumps(entry, ensure_ascii=False))
