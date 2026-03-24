"""Compliance node — checks agent actions against policies and regulations."""

from __future__ import annotations

import logging
import re
from typing import Any

from config.settings import settings
from src.graph.state import AgentState
from src.models.state import AgentResult, AgentType, ComplianceDecision, RiskLevel
from src.providers.provider_factory import get_provider

logger = logging.getLogger(__name__)

_COMPLIANCE_SYSTEM_PROMPT = (
    "You are the compliance specialist agent for an employee benefits platform. "
    "You ensure all enrollment actions and policy guidance comply with:\n"
    "- ERISA (Employee Retirement Income Security Act)\n"
    "- HIPAA (Health Insurance Portability and Accountability Act)\n"
    "- ACA (Affordable Care Act)\n"
    "- COBRA (Consolidated Omnibus Budget Reconciliation Act)\n"
    "- Section 125 Cafeteria Plan rules\n\n"
    "When reviewing an enrollment action, assess:\n"
    "1. Is the action compliant with applicable regulations?\n"
    "2. Are there any risks or special considerations?\n"
    "3. What risk level? (low / medium / high / critical)\n\n"
    "Format: Be concise. Cite specific regulations when applicable."
)

# PII patterns to detect and flag
_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # Email
    re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),  # Phone
]

# High-risk action patterns
_HIGH_RISK_ACTIONS = [
    "submit_enrollment",  # Creating data — moderate risk
    "cancel_enrollment",  # Destructive — high risk
]


def _assess_action_risk(agent_results: list[AgentResult]) -> ComplianceDecision:
    """Deterministic risk assessment based on tool calls and outputs."""
    violations: list[str] = []
    max_risk = RiskLevel.LOW

    for result in agent_results:
        for tc in result.tool_calls:
            # Check for high-risk actions
            if tc.tool_name in _HIGH_RISK_ACTIONS:
                max_risk = RiskLevel.MEDIUM

            # Check for PII in tool results
            for pattern in _PII_PATTERNS:
                if pattern.search(tc.result):
                    violations.append(
                        f"PII detected in {tc.tool_name} result — "
                        "ensure HIPAA-compliant handling"
                    )
                    max_risk = RiskLevel.HIGH

            # Check for failed tool calls
            if not tc.success:
                violations.append(
                    f"Tool {tc.tool_name} failed — review error before proceeding"
                )

        # Check response for PII leaks
        for pattern in _PII_PATTERNS:
            if pattern.search(result.response):
                violations.append("PII detected in agent response — redaction required")
                max_risk = RiskLevel.HIGH

    requires_approval = max_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    return ComplianceDecision(
        approved=len(violations) == 0 or max_risk in (RiskLevel.LOW, RiskLevel.MEDIUM),
        risk_level=max_risk,
        violations=violations,
        requires_human_approval=requires_approval,
        explanation=(
            f"Risk: {max_risk.value}. "
            + (f"Violations: {'; '.join(violations)}" if violations else "No violations detected.")
        ),
    )


async def compliance_node(state: AgentState) -> dict[str, Any]:
    """Run compliance checks on agent results.

    Two modes:
    1. Pre-action check (routing says compliance check needed)
    2. Post-action review (after agent has produced results)
    """
    agent_results = state.get("agent_results", [])
    user_message = state["user_message"]
    routing = state.get("routing")

    logger.info(f"Compliance node: checking {len(agent_results)} agent results")

    # Phase 1: Deterministic risk assessment
    decision = _assess_action_risk(agent_results)

    # Phase 2: If user explicitly asked a compliance question, answer it via LLM
    if routing and routing.primary_agent == AgentType.COMPLIANCE:
        provider = get_provider()
        messages = [
            {"role": "system", "content": _COMPLIANCE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
        response = await provider.chat(messages=messages)

        result = AgentResult(
            agent=AgentType.COMPLIANCE,
            response=response.content,
            confidence=0.7,
        )
        return {"agent_results": [result], "compliance": decision}

    # Phase 2b: Post-action compliance check only (no user-facing response)
    if decision.violations:
        logger.warning(
            f"Compliance: {len(decision.violations)} violation(s) found — "
            f"risk={decision.risk_level.value}"
        )

    return {"compliance": decision}
