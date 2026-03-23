"""Tests for the compliance node — risk assessment and PII detection."""

from src.graph.compliance_node import _assess_action_risk
from src.models.state import AgentResult, AgentType, RiskLevel, ToolCall


class TestActionRiskAssessment:
    """Test deterministic risk assessment logic."""

    def test_no_tool_calls_is_low_risk(self):
        results = [AgentResult(agent=AgentType.ADVISOR, response="Here are the plans.")]
        decision = _assess_action_risk(results)
        assert decision.risk_level == RiskLevel.LOW
        assert decision.approved is True
        assert len(decision.violations) == 0

    def test_submit_enrollment_is_medium_risk(self):
        results = [AgentResult(
            agent=AgentType.ENROLLMENT,
            response="Enrollment submitted.",
            tool_calls=[ToolCall(tool_name="submit_enrollment", tool_args={}, result='{"enrollmentId": "abc"}')],
        )]
        decision = _assess_action_risk(results)
        assert decision.risk_level == RiskLevel.MEDIUM

    def test_ssn_in_result_is_high_risk(self):
        results = [AgentResult(
            agent=AgentType.ENROLLMENT,
            response="Found employee",
            tool_calls=[ToolCall(
                tool_name="get_enrollment",
                tool_args={},
                result='{"ssn": "123-45-6789", "name": "Jane"}',
            )],
        )]
        decision = _assess_action_risk(results)
        assert decision.risk_level == RiskLevel.HIGH
        assert any("PII" in v for v in decision.violations)
        assert decision.requires_human_approval is True

    def test_email_in_response_is_high_risk(self):
        results = [AgentResult(
            agent=AgentType.ENROLLMENT,
            response="Contact jane.doe@example.com for details.",
        )]
        decision = _assess_action_risk(results)
        assert decision.risk_level == RiskLevel.HIGH
        assert any("PII" in v for v in decision.violations)

    def test_failed_tool_call_flagged(self):
        results = [AgentResult(
            agent=AgentType.ENROLLMENT,
            response="Something went wrong.",
            tool_calls=[ToolCall(
                tool_name="get_enrollment",
                tool_args={},
                result='{"error": "not found"}',
                success=False,
            )],
        )]
        decision = _assess_action_risk(results)
        assert any("failed" in v.lower() for v in decision.violations)
