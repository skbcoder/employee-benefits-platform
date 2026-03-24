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
) -> tuple[str, list[str]] | None:
    """Delegate to the orchestrator service.

    Returns (response_text, tool_calls_list) on success, or None if the
    orchestrator is unavailable (caller should fall back to local agent_loop).
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
            return data.get("response", ""), data.get("tool_calls", [])
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
