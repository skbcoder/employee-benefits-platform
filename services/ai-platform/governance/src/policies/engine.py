"""Policy engine for evaluating governance rules against agent actions.

Loads policies from YAML files and (future) database. Evaluates each
incoming action against all enabled policies, returning a consolidated
decision with matched rules, effects, and risk contribution.
"""

from __future__ import annotations

import fnmatch
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PolicyEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    REDACT = "redact"
    LOG = "log"


class ConditionOperator(str, Enum):
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    EQUALS = "equals"
    COUNT_GT = "count_gt"
    MATCHES_PATTERN = "matches_pattern"
    IN_LIST = "in_list"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class PolicyCondition(BaseModel):
    field: str
    operator: ConditionOperator
    value: Any


class PolicyRule(BaseModel):
    id: str
    description: str = ""
    trigger_agent: str = "*"
    trigger_action: str = "*"
    conditions: list[PolicyCondition] = Field(default_factory=list)
    effect: PolicyEffect = PolicyEffect.LOG
    priority: int = 0
    enabled: bool = True


class MatchedPolicy(BaseModel):
    policy_id: str
    description: str
    effect: PolicyEffect
    priority: int


class PolicyDecision(BaseModel):
    allowed: bool = True
    effects: list[PolicyEffect] = Field(default_factory=list)
    matched_policies: list[MatchedPolicy] = Field(default_factory=list)
    explanation: str = ""
    risk_contribution: float = 0.0


# ---------------------------------------------------------------------------
# Condition evaluation helpers
# ---------------------------------------------------------------------------

def _resolve_field(context: dict[str, Any], field: str) -> Any:
    """Resolve a dotted field path from context."""
    parts = field.split(".")
    current: Any = context
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
    return current


def _evaluate_condition(condition: PolicyCondition, context: dict[str, Any]) -> bool:
    """Return True if *condition* is satisfied by *context*."""
    value = _resolve_field(context, condition.field)

    match condition.operator:
        case ConditionOperator.CONTAINS:
            if isinstance(value, str):
                return str(condition.value) in value
            if isinstance(value, (list, tuple)):
                return condition.value in value
            return False

        case ConditionOperator.NOT_CONTAINS:
            if isinstance(value, str):
                return str(condition.value) not in value
            if isinstance(value, (list, tuple)):
                return condition.value not in value
            return True

        case ConditionOperator.EQUALS:
            return value == condition.value

        case ConditionOperator.COUNT_GT:
            try:
                if isinstance(value, (list, tuple)):
                    return len(value) > int(condition.value)
                return int(value) > int(condition.value)
            except (TypeError, ValueError):
                return False

        case ConditionOperator.MATCHES_PATTERN:
            if not isinstance(value, str):
                return False
            try:
                return bool(re.search(str(condition.value), value))
            except re.error:
                return False

        case ConditionOperator.IN_LIST:
            expected = condition.value if isinstance(condition.value, list) else [condition.value]
            return value in expected

    return False


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class PolicyEngine:
    """Evaluates agent actions against a set of policy rules."""

    def __init__(self) -> None:
        self._policies: list[PolicyRule] = []

    # -- Policy management ---------------------------------------------------

    def add_policy(self, policy: PolicyRule) -> None:
        self._policies.append(policy)

    def add_policies(self, policies: list[PolicyRule]) -> None:
        self._policies.extend(policies)

    def clear(self) -> None:
        self._policies.clear()

    @property
    def policies(self) -> list[PolicyRule]:
        return list(self._policies)

    # -- Evaluation ----------------------------------------------------------

    def evaluate(
        self,
        agent: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        """Evaluate all enabled policies for the given agent action.

        Policies are evaluated in *priority* order (highest priority number
        wins).  A ``deny`` effect anywhere blocks the action.  Other effects
        accumulate.
        """
        context = context or {}
        matched: list[MatchedPolicy] = []
        effects: list[PolicyEffect] = []
        risk: float = 0.0

        # Sort by priority descending so highest-priority rules are first.
        active = sorted(
            (p for p in self._policies if p.enabled),
            key=lambda p: p.priority,
            reverse=True,
        )

        for policy in active:
            if not self._trigger_matches(policy, agent, action):
                continue

            if policy.conditions and not all(
                _evaluate_condition(c, context) for c in policy.conditions
            ):
                continue

            matched.append(
                MatchedPolicy(
                    policy_id=policy.id,
                    description=policy.description,
                    effect=policy.effect,
                    priority=policy.priority,
                )
            )
            if policy.effect not in effects:
                effects.append(policy.effect)

            # Risk contribution heuristic.
            risk += self._effect_risk(policy.effect)

        # Build decision.
        allowed = PolicyEffect.DENY not in effects
        requires_approval = PolicyEffect.REQUIRE_APPROVAL in effects

        if not allowed:
            explanation = "Blocked by policy: " + ", ".join(
                m.policy_id for m in matched if m.effect == PolicyEffect.DENY
            )
        elif requires_approval:
            explanation = "Approval required by policy: " + ", ".join(
                m.policy_id for m in matched if m.effect == PolicyEffect.REQUIRE_APPROVAL
            )
            allowed = False  # Not allowed until approved.
        elif matched:
            explanation = f"Matched {len(matched)} policies; action allowed."
        else:
            explanation = "No policies matched; action allowed by default."

        return PolicyDecision(
            allowed=allowed,
            effects=effects,
            matched_policies=matched,
            explanation=explanation,
            risk_contribution=min(risk, 1.0),
        )

    # -- Helpers -------------------------------------------------------------

    @staticmethod
    def _trigger_matches(policy: PolicyRule, agent: str, action: str) -> bool:
        return fnmatch.fnmatch(agent, policy.trigger_agent) and fnmatch.fnmatch(
            action, policy.trigger_action
        )

    @staticmethod
    def _effect_risk(effect: PolicyEffect) -> float:
        return {
            PolicyEffect.ALLOW: 0.0,
            PolicyEffect.LOG: 0.05,
            PolicyEffect.REDACT: 0.15,
            PolicyEffect.REQUIRE_APPROVAL: 0.25,
            PolicyEffect.DENY: 0.4,
        }.get(effect, 0.0)
