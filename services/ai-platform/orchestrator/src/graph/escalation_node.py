"""Escalation node — handles cases requiring human review."""

from __future__ import annotations

import logging
from typing import Any

from src.graph.state import AgentState

logger = logging.getLogger(__name__)


async def escalation_node(state: AgentState) -> dict[str, Any]:
    """Handle escalation when the system cannot confidently resolve a request.

    Triggered by:
    - Low routing confidence
    - Compliance violations requiring human approval
    - Agent errors or max iteration limits
    """
    user_message = state["user_message"]
    agent_results = state.get("agent_results", [])
    compliance = state.get("compliance")
    conversation_id = state.get("conversation_id", "unknown")

    # Determine escalation reason
    reasons: list[str] = []

    routing = state.get("routing")
    if routing and routing.confidence < 0.3:
        reasons.append(f"Low routing confidence ({routing.confidence:.2f})")

    if compliance and compliance.requires_human_approval:
        reasons.append(f"Compliance: {compliance.explanation}")

    for ar in agent_results:
        if ar.error:
            reasons.append(f"Agent {ar.agent.value} error: {ar.error}")

    reason_str = "; ".join(reasons) if reasons else "Unspecified"
    logger.warning(
        f"Escalation: conversation={conversation_id}, "
        f"reasons=[{reason_str}], query='{user_message[:80]}'"
    )

    # In production, this would:
    # 1. Create a ticket in the internal system
    # 2. Send notification to benefits admin
    # 3. Store the full conversation context for review
    # For now, return a user-friendly message

    return {
        "final_response": (
            "I want to make sure you get the best help possible. Your request "
            "has been flagged for review by a benefits administrator who can "
            "provide more detailed assistance. They'll follow up with you "
            "shortly.\n\n"
            "In the meantime, feel free to ask me about plan comparisons, "
            "coverage details, or general enrollment questions!"
        ),
        "escalated": True,
    }
