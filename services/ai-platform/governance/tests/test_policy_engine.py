"""Tests for the policy engine."""

import pytest

from src.policies.engine import (
    ConditionOperator,
    PolicyCondition,
    PolicyDecision,
    PolicyEffect,
    PolicyEngine,
    PolicyRule,
)


@pytest.fixture
def engine() -> PolicyEngine:
    return PolicyEngine()


def _make_rule(
    rule_id: str = "test",
    agent: str = "*",
    action: str = "*",
    effect: PolicyEffect = PolicyEffect.ALLOW,
    priority: int = 1,
    enabled: bool = True,
    conditions: list | None = None,
) -> PolicyRule:
    return PolicyRule(
        id=rule_id,
        description=f"Test rule {rule_id}",
        trigger_agent=agent,
        trigger_action=action,
        conditions=conditions or [],
        effect=effect,
        priority=priority,
        enabled=enabled,
    )


class TestPolicyEvaluation:
    def test_no_policies_allows(self, engine: PolicyEngine):
        decision = engine.evaluate("enrollment", "read", {})
        assert decision.allowed is True
        assert len(decision.matched_policies) == 0

    def test_allow_effect(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(effect=PolicyEffect.ALLOW))
        decision = engine.evaluate("enrollment", "read", {})
        assert decision.allowed is True

    def test_deny_effect_blocks(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(effect=PolicyEffect.DENY))
        decision = engine.evaluate("enrollment", "submit", {})
        assert decision.allowed is False
        assert PolicyEffect.DENY in decision.effects

    def test_require_approval_blocks(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(effect=PolicyEffect.REQUIRE_APPROVAL))
        decision = engine.evaluate("enrollment", "submit", {})
        assert decision.allowed is False
        assert PolicyEffect.REQUIRE_APPROVAL in decision.effects

    def test_log_effect_allows(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(effect=PolicyEffect.LOG))
        decision = engine.evaluate("enrollment", "submit", {})
        assert decision.allowed is True
        assert PolicyEffect.LOG in decision.effects

    def test_wildcard_agent_matching(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(agent="*", action="submit", effect=PolicyEffect.DENY))
        decision = engine.evaluate("any_agent", "submit", {})
        assert decision.allowed is False

    def test_specific_agent_no_match(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(agent="enrollment", action="submit", effect=PolicyEffect.DENY))
        decision = engine.evaluate("processing", "submit", {})
        assert decision.allowed is True
        assert len(decision.matched_policies) == 0

    def test_priority_ordering(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(rule_id="low", effect=PolicyEffect.ALLOW, priority=1))
        engine.add_policy(_make_rule(rule_id="high", effect=PolicyEffect.DENY, priority=10))
        decision = engine.evaluate("enrollment", "submit", {})
        assert decision.allowed is False
        # Highest priority policy should appear first in matched list.
        assert decision.matched_policies[0].policy_id == "high"

    def test_disabled_policy_ignored(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(effect=PolicyEffect.DENY, enabled=False))
        decision = engine.evaluate("enrollment", "submit", {})
        assert decision.allowed is True
        assert len(decision.matched_policies) == 0

    def test_condition_equals_match(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(
            effect=PolicyEffect.DENY,
            conditions=[PolicyCondition(field="status", operator=ConditionOperator.EQUALS, value="blocked")],
        ))
        decision = engine.evaluate("enrollment", "submit", {"status": "blocked"})
        assert decision.allowed is False

    def test_condition_equals_no_match(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(
            effect=PolicyEffect.DENY,
            conditions=[PolicyCondition(field="status", operator=ConditionOperator.EQUALS, value="blocked")],
        ))
        decision = engine.evaluate("enrollment", "submit", {"status": "active"})
        assert decision.allowed is True

    def test_condition_contains(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(
            effect=PolicyEffect.REDACT,
            conditions=[PolicyCondition(field="response", operator=ConditionOperator.CONTAINS, value="SSN")],
        ))
        decision = engine.evaluate("enrollment", "respond", {"response": "Your SSN is on file"})
        assert PolicyEffect.REDACT in decision.effects

    def test_condition_count_gt(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(
            effect=PolicyEffect.REQUIRE_APPROVAL,
            conditions=[PolicyCondition(field="selection_count", operator=ConditionOperator.COUNT_GT, value=3)],
        ))
        decision = engine.evaluate("enrollment", "submit", {"selection_count": 5})
        assert PolicyEffect.REQUIRE_APPROVAL in decision.effects

    def test_condition_matches_pattern(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(
            effect=PolicyEffect.REDACT,
            conditions=[PolicyCondition(
                field="response",
                operator=ConditionOperator.MATCHES_PATTERN,
                value=r"\d{3}-\d{2}-\d{4}",
            )],
        ))
        decision = engine.evaluate("enrollment", "respond", {"response": "SSN: 123-45-6789"})
        assert PolicyEffect.REDACT in decision.effects

    def test_risk_contribution_from_deny(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(effect=PolicyEffect.DENY))
        decision = engine.evaluate("enrollment", "submit", {})
        assert decision.risk_contribution > 0.0

    def test_multiple_effects_accumulate(self, engine: PolicyEngine):
        engine.add_policy(_make_rule(rule_id="log", effect=PolicyEffect.LOG, priority=1))
        engine.add_policy(_make_rule(rule_id="redact", effect=PolicyEffect.REDACT, priority=2))
        decision = engine.evaluate("enrollment", "submit", {})
        assert PolicyEffect.LOG in decision.effects
        assert PolicyEffect.REDACT in decision.effects
        assert decision.allowed is True  # Neither log nor redact blocks.
