"""Tests for the YAML-based policy engine."""

from src.guardrails.policy_engine import PolicyCondition, PolicyEngine, PolicyRule


class TestPolicyConditions:
    """Test individual condition evaluation."""

    def _engine(self) -> PolicyEngine:
        engine = PolicyEngine.__new__(PolicyEngine)
        engine._policies = []
        return engine

    def test_contains(self):
        engine = self._engine()
        cond = PolicyCondition(field="response", operator="contains", value="secret")
        assert engine._evaluate_condition(cond, {"response": "this is a secret word"})
        assert not engine._evaluate_condition(cond, {"response": "nothing here"})

    def test_not_contains(self):
        engine = self._engine()
        cond = PolicyCondition(field="response", operator="not_contains", value="bad")
        assert engine._evaluate_condition(cond, {"response": "all good"})
        assert not engine._evaluate_condition(cond, {"response": "this is bad"})

    def test_equals(self):
        engine = self._engine()
        cond = PolicyCondition(field="status", operator="equals", value="COMPLETED")
        assert engine._evaluate_condition(cond, {"status": "COMPLETED"})
        assert not engine._evaluate_condition(cond, {"status": "PROCESSING"})

    def test_count_gt(self):
        engine = self._engine()
        cond = PolicyCondition(field="selections", operator="count_gt", value=3)
        assert engine._evaluate_condition(cond, {"selections": [1, 2, 3, 4]})
        assert not engine._evaluate_condition(cond, {"selections": [1, 2]})

    def test_matches_pattern(self):
        engine = self._engine()
        cond = PolicyCondition(
            field="response",
            operator="matches_pattern",
            value=r"\d{3}-\d{2}-\d{4}",
        )
        assert engine._evaluate_condition(cond, {"response": "SSN is 123-45-6789"})
        assert not engine._evaluate_condition(cond, {"response": "No SSN here"})

    def test_missing_field(self):
        engine = self._engine()
        cond = PolicyCondition(field="missing", operator="equals", value="x")
        assert not engine._evaluate_condition(cond, {"other": "value"})


class TestPolicyEvaluation:
    """Test full policy evaluation with rules."""

    def test_deny_policy(self):
        engine = PolicyEngine.__new__(PolicyEngine)
        engine._policies = [
            PolicyRule(
                id="test_deny",
                trigger_agent="*",
                trigger_action="respond",
                conditions=[
                    PolicyCondition(
                        field="response",
                        operator="contains",
                        value="[HARMFUL]",
                    )
                ],
                effect="deny",
            )
        ]
        decision = engine.evaluate("enrollment", "respond", {"response": "This is [HARMFUL]"})
        assert not decision.allowed
        assert "test_deny" in decision.matched_policies

    def test_allow_when_no_match(self):
        engine = PolicyEngine.__new__(PolicyEngine)
        engine._policies = [
            PolicyRule(
                id="test_deny",
                trigger_agent="enrollment",
                trigger_action="submit",
                conditions=[
                    PolicyCondition(field="selections", operator="count_gt", value=10)
                ],
                effect="deny",
            )
        ]
        decision = engine.evaluate("enrollment", "submit", {"selections": [1, 2]})
        assert decision.allowed

    def test_wildcard_agent_matches_all(self):
        engine = PolicyEngine.__new__(PolicyEngine)
        engine._policies = [
            PolicyRule(
                id="global_rule",
                trigger_agent="*",
                trigger_action="*",
                conditions=[],
                effect="log",
            )
        ]
        decision = engine.evaluate("advisor", "respond", {})
        assert "global_rule" in decision.matched_policies
