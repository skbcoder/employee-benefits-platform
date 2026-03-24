"""Client for the multi-agent Orchestrator service.

Delegates to the LangGraph orchestrator when available, falls back to
the local agent_loop for backward compatibility.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

# Orchestrator URL — configurable via env
_ORCHESTRATOR_URL = getattr(settings, "orchestrator_url", "http://localhost:8400")


async def orchestrate(
    message: str,
    conversation_id: str = "",
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Delegate to the orchestrator service.

    Returns a dict with response text, tool calls, and agent metadata on success.
    Returns None if the orchestrator is unavailable (caller falls back to local agent_loop).
    """
    url = f"{_ORCHESTRATOR_URL}/api/orchestrate"

    payload = {
        "message": message,
        "conversation_id": conversation_id,
        "history": history or [],
    }

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return {
                "response": data.get("response", ""),
                "tool_calls": data.get("tool_calls", []),
                "agent_used": data.get("agent_used", ""),
                "confidence": data.get("confidence", 0.0),
                "compliance_risk": data.get("compliance_risk", "low"),
                "latency_ms": data.get("latency_ms", 0),
            }
        except httpx.ConnectError:
            logger.debug("Orchestrator not available — falling back to local agent loop")
            return None
        except Exception as e:
            logger.warning(f"Orchestrator call failed: {e} — falling back")
            return None


async def is_available() -> bool:
    """Check if the orchestrator service is running."""
    url = f"{_ORCHESTRATOR_URL}/health"
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            resp = await client.get(url)
            return resp.status_code == 200
        except Exception:
            return False
