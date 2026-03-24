"""Synthesis node — merges agent results and applies final governance checks."""

from __future__ import annotations

import logging
import re
from typing import Any

from src.graph.state import AgentState
from src.models.state import RiskLevel

logger = logging.getLogger(__name__)

# UUIDs should never appear in user-facing responses
_UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)

# Internal terms that should not leak
_INTERNAL_TERMS = [
    "outbox_event", "inbox_message", "enrollment_record",
    "processing_record", "system prompt", "my instructions",
]

# PII patterns to redact from final output
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


def _sanitize_response(text: str) -> str:
    """Remove UUIDs, internal terms, and PII from the final response."""
    # Strip UUIDs
    clean = _UUID_PATTERN.sub("[enrollment reference]", text)

    # Strip internal terms
    for term in _INTERNAL_TERMS:
        if term.lower() in clean.lower():
            clean = re.sub(re.escape(term), "[internal]", clean, flags=re.IGNORECASE)

    # Redact email addresses
    clean = _EMAIL_PATTERN.sub("[email redacted]", clean)

    return clean


async def synthesis_node(state: AgentState) -> dict[str, Any]:
    """Merge agent results into a final response.

    - Single agent: use its response directly
    - Multiple agents: merge intelligently
    - Apply compliance gating
    - Sanitize output (UUIDs, PII, internal terms)
    """
    agent_results = state.get("agent_results", [])
    compliance = state.get("compliance")

    if not agent_results:
        return {
            "final_response": (
                "I'm here to help with employee benefits! Would you like to "
                "check your enrollment status, compare plans, or learn about "
                "your coverage options?"
            )
        }

    # Compliance gating — if high risk and not approved, block the response
    if compliance and not compliance.approved:
        logger.warning(f"Synthesis: compliance blocked — {compliance.explanation}")
        return {
            "final_response": (
                "This request requires additional review before I can proceed. "
                "A benefits administrator has been notified and will follow up "
                "with you shortly."
            ),
            "escalated": True,
        }

    # If compliance requires human approval, flag but still return
    if compliance and compliance.requires_human_approval:
        logger.info("Synthesis: flagging for human review")

    # Single agent result — use directly
    if len(agent_results) == 1:
        response = agent_results[0].response
    else:
        # Multiple agents — take the primary agent's response
        # and append compliance notes if relevant
        primary = agent_results[0]
        response = primary.response

        # If compliance agent produced a result, append it
        for ar in agent_results[1:]:
            if ar.response and ar.agent.value == "compliance":
                response += f"\n\n**Compliance Note:**\n{ar.response}"

    # Sanitize before returning
    final = _sanitize_response(response)

    # Add compliance warning if violations exist
    if compliance and compliance.violations and compliance.risk_level == RiskLevel.MEDIUM:
        final += (
            "\n\n---\n*Note: This action has been flagged for compliance review.*"
        )

    return {"final_response": final}
