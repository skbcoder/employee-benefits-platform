"""Risk scoring for agent actions.

Computes a numeric risk score (0.0 -- 1.0) based on several weighted
factors such as action type, PII presence, tool usage, and data
sensitivity.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from config.settings import get_settings


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskFactor(BaseModel):
    name: str
    weight: float
    value: float
    description: str = ""


class RiskScore(BaseModel):
    score: float = 0.0
    level: RiskLevel = RiskLevel.LOW
    factors: list[RiskFactor] = Field(default_factory=list)
    explanation: str = ""


# ---------------------------------------------------------------------------
# Internal weight tables
# ---------------------------------------------------------------------------

_ACTION_WEIGHTS: dict[str, float] = {
    "submit": 0.3,
    "submit_enrollment": 0.3,
    "read": 0.1,
    "get": 0.1,
    "list": 0.1,
    "delete": 0.8,
    "remove": 0.8,
    "update": 0.4,
    "modify": 0.4,
    "respond": 0.15,
}

_SENSITIVITY_WEIGHTS: dict[str, float] = {
    "medical": 0.2,
    "dental": 0.1,
    "vision": 0.05,
    "life": 0.1,
    "disability": 0.15,
}


def _action_factor(action: str) -> RiskFactor:
    action_lower = action.lower()
    weight = 0.15  # default
    for key, w in _ACTION_WEIGHTS.items():
        if key in action_lower:
            weight = w
            break
    return RiskFactor(
        name="action_type",
        weight=weight,
        value=weight,
        description=f"Action '{action}' has base risk weight {weight}",
    )


def _pii_factor(context: dict[str, Any]) -> RiskFactor:
    pii_present = context.get("pii_present", False)
    pii_count = context.get("pii_count", 0)
    if pii_present or pii_count > 0:
        value = 0.4
        return RiskFactor(
            name="pii_present",
            weight=value,
            value=value,
            description=f"PII detected in context (count={pii_count})",
        )
    return RiskFactor(name="pii_present", weight=0.0, value=0.0, description="No PII detected")


def _tool_count_factor(context: dict[str, Any]) -> RiskFactor:
    tools = context.get("tool_count", 0)
    value = min(tools * 0.1, 0.5)
    return RiskFactor(
        name="tool_count",
        weight=value,
        value=value,
        description=f"{tools} tool(s) involved, adding {value:.2f} risk",
    )


def _failed_tools_factor(context: dict[str, Any]) -> RiskFactor:
    failed = context.get("failed_tools", 0)
    value = 0.3 if failed > 0 else 0.0
    return RiskFactor(
        name="failed_tools",
        weight=value,
        value=value,
        description=f"{failed} failed tool(s)" if failed else "No failed tools",
    )


def _data_sensitivity_factor(context: dict[str, Any]) -> RiskFactor:
    selections = context.get("selections", [])
    data_type = context.get("data_type", "")
    max_weight = 0.0

    # Check selections list (enrollment benefit types).
    for sel in selections:
        btype = sel.get("type", "").lower() if isinstance(sel, dict) else str(sel).lower()
        max_weight = max(max_weight, _SENSITIVITY_WEIGHTS.get(btype, 0.0))

    # Check explicit data_type field.
    if data_type:
        max_weight = max(max_weight, _SENSITIVITY_WEIGHTS.get(data_type.lower(), 0.0))

    return RiskFactor(
        name="data_sensitivity",
        weight=max_weight,
        value=max_weight,
        description=f"Data sensitivity weight {max_weight:.2f}",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_action(
    agent: str,
    action: str,
    context: dict[str, Any] | None = None,
) -> RiskScore:
    """Compute a risk score for the given agent action and context."""
    context = context or {}
    settings = get_settings()

    factors = [
        _action_factor(action),
        _pii_factor(context),
        _tool_count_factor(context),
        _failed_tools_factor(context),
        _data_sensitivity_factor(context),
    ]

    total = sum(f.value for f in factors)
    score = min(total, 1.0)

    # Classify level based on configured thresholds.
    if score >= settings.risk_threshold_critical:
        level = RiskLevel.CRITICAL
    elif score >= settings.risk_threshold_high:
        level = RiskLevel.HIGH
    elif score >= 0.3:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW

    contributing = [f for f in factors if f.value > 0]
    explanation_parts = [f.description for f in contributing]
    explanation = "; ".join(explanation_parts) if explanation_parts else "No significant risk factors."

    return RiskScore(
        score=round(score, 3),
        level=level,
        factors=factors,
        explanation=explanation,
    )
