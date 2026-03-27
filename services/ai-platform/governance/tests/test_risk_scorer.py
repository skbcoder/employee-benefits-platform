"""Tests for risk scoring."""


from src.risk.scorer import RiskLevel, score_action


class TestScoreAction:
    def test_read_action_low_risk(self):
        result = score_action("enrollment", "read", {})
        assert result.score < 0.3
        assert result.level == RiskLevel.LOW

    def test_submit_action_medium_risk(self):
        result = score_action("enrollment", "submit_enrollment", {})
        assert result.level == RiskLevel.MEDIUM
        assert 0.3 <= result.score < 0.7

    def test_delete_action_high_risk(self):
        result = score_action("enrollment", "delete", {})
        assert result.score >= 0.7
        assert result.level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_pii_present_increases_risk(self):
        base = score_action("enrollment", "read", {})
        with_pii = score_action("enrollment", "read", {"pii_present": True, "pii_count": 2})
        assert with_pii.score > base.score

    def test_tool_count_increases_risk(self):
        base = score_action("enrollment", "read", {})
        with_tools = score_action("enrollment", "read", {"tool_count": 5})
        assert with_tools.score > base.score

    def test_failed_tools_increases_risk(self):
        base = score_action("enrollment", "read", {})
        with_failures = score_action("enrollment", "read", {"failed_tools": 2})
        assert with_failures.score > base.score

    def test_medical_data_sensitivity(self):
        base = score_action("enrollment", "read", {})
        with_medical = score_action("enrollment", "read", {"selections": [{"type": "medical"}]})
        assert with_medical.score > base.score

    def test_multiple_factors_combine(self):
        result = score_action("enrollment", "delete", {
            "pii_present": True,
            "pii_count": 3,
            "tool_count": 3,
            "failed_tools": 1,
            "selections": [{"type": "medical"}],
        })
        assert result.level == RiskLevel.CRITICAL
        assert result.score >= 0.9

    def test_score_capped_at_one(self):
        result = score_action("enrollment", "delete", {
            "pii_present": True,
            "pii_count": 10,
            "tool_count": 10,
            "failed_tools": 5,
        })
        assert result.score <= 1.0

    def test_factors_list_populated(self):
        result = score_action("enrollment", "submit", {})
        assert len(result.factors) > 0
        names = [f.name for f in result.factors]
        assert "action_type" in names
        assert "pii_present" in names
