"""Policy engine — evaluates declarative YAML policies against agent actions."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_POLICIES_DIR = Path(__file__).parent.parent.parent / "config"


class PolicyCondition(BaseModel):
    """A single condition to evaluate."""

    field: str
    operator: str  # contains, not_contains, equals, count_gt, matches_pattern
    value: Any


class PolicyRule(BaseModel):
    """A single policy rule."""

    id: str
    description: str = ""
    trigger_agent: str = "*"
    trigger_action: str = "*"
    conditions: list[PolicyCondition] = Field(default_factory=list)
    effect: str = "allow"  # allow, deny, require_approval, redact, log


class PolicyDecision(BaseModel):
    """Result of evaluating all applicable policies."""

    allowed: bool = True
    effects: list[str] = Field(default_factory=list)
    matched_policies: list[str] = Field(default_factory=list)
    explanation: str = ""


class PolicyEngine:
    """Evaluates agent actions against declarative YAML policies."""

    def __init__(self) -> None:
        self._policies: list[PolicyRule] = []
        self._load_policies()

    def _load_policies(self) -> None:
        """Load all YAML policy files from config directory."""
        for yaml_file in _POLICIES_DIR.glob("*_policies.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f) or {}
                for policy_data in data.get("policies", []):
                    conditions = [
                        PolicyCondition(**c)
                        for c in policy_data.get("conditions", [])
                    ]
                    rule = PolicyRule(
                        id=policy_data["id"],
                        description=policy_data.get("description", ""),
                        trigger_agent=policy_data.get("trigger", {}).get("agent", "*"),
                        trigger_action=policy_data.get("trigger", {}).get("action", "*"),
                        conditions=conditions,
                        effect=policy_data.get("effect", "allow"),
                    )
                    self._policies.append(rule)
                logger.info(f"Loaded {len(data.get('policies', []))} policies from {yaml_file.name}")
            except Exception as e:
                logger.error(f"Failed to load policy file {yaml_file}: {e}")

    def evaluate(
        self,
        agent: str,
        action: str,
        context: dict[str, Any],
    ) -> PolicyDecision:
        """Evaluate all applicable policies for an agent action.

        Args:
            agent: Agent type (e.g., "enrollment", "advisor")
            action: Action being performed (e.g., "submit_enrollment", "respond")
            context: Dictionary of context values for condition evaluation
        """
        matched: list[str] = []
        effects: list[str] = []
        blocked = False

        for policy in self._policies:
            # Check trigger match
            if policy.trigger_agent != "*" and policy.trigger_agent != agent:
                continue
            if policy.trigger_action != "*" and policy.trigger_action != action:
                continue

            # Evaluate conditions
            all_conditions_met = True
            for condition in policy.conditions:
                if not self._evaluate_condition(condition, context):
                    all_conditions_met = False
                    break

            if all_conditions_met:
                matched.append(policy.id)
                effects.append(policy.effect)

                if policy.effect == "deny":
                    blocked = True
                elif policy.effect == "require_approval":
                    blocked = True

        return PolicyDecision(
            allowed=not blocked,
            effects=effects,
            matched_policies=matched,
            explanation=(
                f"Matched policies: {', '.join(matched)}" if matched else "No policies matched"
            ),
        )

    def _evaluate_condition(
        self, condition: PolicyCondition, context: dict[str, Any]
    ) -> bool:
        """Evaluate a single condition against the context."""
        value = context.get(condition.field)
        if value is None:
            return False

        if condition.operator == "contains":
            return condition.value in str(value)
        elif condition.operator == "not_contains":
            return condition.value not in str(value)
        elif condition.operator == "equals":
            return str(value) == str(condition.value)
        elif condition.operator == "count_gt":
            if isinstance(value, (list, tuple)):
                return len(value) > int(condition.value)
            return False
        elif condition.operator == "matches_pattern":
            return bool(re.search(str(condition.value), str(value)))
        else:
            logger.warning(f"Unknown condition operator: {condition.operator}")
            return False


# Singleton
policy_engine = PolicyEngine()
