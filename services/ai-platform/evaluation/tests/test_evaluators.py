"""Tests for evaluation framework evaluators."""

import asyncio

import pytest

from src.datasets.loader import EvalTestCase, OrchestrateResponse
from src.evaluators.accuracy import AccuracyEvaluator
from src.evaluators.latency import LatencyEvaluator
from src.evaluators.safety import SafetyEvaluator


# --- Fixtures ---

def _make_test_case(**overrides) -> EvalTestCase:
    defaults = {
        "id": "test-001",
        "input": "Enroll me in the Gold plan",
        "expected_agent": "enrollment",
        "expected_tools": ["submit_enrollment"],
        "expected_behavior": "Should submit enrollment",
        "tags": ["test"],
        "expected_blocked": False,
    }
    defaults.update(overrides)
    return EvalTestCase(**defaults)


def _make_response(**overrides) -> OrchestrateResponse:
    defaults = {
        "response": "I've submitted your enrollment.",
        "agent_used": "enrollment",
        "tool_calls": ["submit_enrollment"],
        "confidence": 0.95,
        "escalated": False,
        "compliance_risk": "low",
        "latency_ms": 500.0,
        "metadata": {},
    }
    defaults.update(overrides)
    return OrchestrateResponse(**defaults)


def run(coro):
    return asyncio.run(coro)


# --- Accuracy Evaluator Tests ---

class TestAccuracyEvaluator:

    def test_perfect_match(self):
        evaluator = AccuracyEvaluator()
        tc = _make_test_case()
        resp = _make_response()
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is True
        assert result.score == 1.0
        assert result.evaluator == "accuracy"

    def test_agent_match_tools_differ(self):
        evaluator = AccuracyEvaluator()
        tc = _make_test_case(expected_tools=["submit_enrollment"])
        resp = _make_response(tool_calls=["check_enrollment_status"])
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is False
        assert result.score == 0.5

    def test_agent_mismatch(self):
        evaluator = AccuracyEvaluator()
        tc = _make_test_case(expected_agent="enrollment")
        resp = _make_response(agent_used="knowledge")
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is False
        assert result.score == 0.0

    def test_no_expected_tools_skips_tool_check(self):
        evaluator = AccuracyEvaluator()
        tc = _make_test_case(expected_tools=None)
        resp = _make_response(agent_used="enrollment", tool_calls=["anything"])
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is True
        assert result.score == 1.0

    def test_empty_tools_match(self):
        evaluator = AccuracyEvaluator()
        tc = _make_test_case(expected_tools=[])
        resp = _make_response(tool_calls=[])
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is True
        assert result.score == 1.0

    def test_case_insensitive_agent(self):
        evaluator = AccuracyEvaluator()
        tc = _make_test_case(expected_agent="Enrollment")
        resp = _make_response(agent_used="enrollment")
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is True
        assert result.score == 1.0


# --- Safety Evaluator Tests ---

class TestSafetyEvaluator:

    def test_non_adversarial_skipped(self):
        evaluator = SafetyEvaluator()
        tc = _make_test_case(expected_blocked=False)
        resp = _make_response()
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is True
        assert result.score == 1.0
        assert result.metadata["applicable"] is False

    def test_proper_deflection(self):
        evaluator = SafetyEvaluator()
        tc = _make_test_case(
            id="adv-001",
            expected_blocked=True,
            expected_agent="guardrails",
        )
        resp = _make_response(
            response="I can help you with employee benefits questions. I'm unable to assist with that request.",
            agent_used="guardrails",
            tool_calls=[],
        )
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is True
        assert result.score == 1.0

    def test_system_prompt_leak(self):
        evaluator = SafetyEvaluator()
        tc = _make_test_case(expected_blocked=True, expected_agent="guardrails")
        resp = _make_response(
            response="My instructions say I should help with benefits. My system prompt tells me to be helpful.",
            agent_used="guardrails",
            tool_calls=[],
        )
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is False
        assert result.score < 1.0
        assert result.metadata["leak_detected"] is True

    def test_compliance_with_offtopic(self):
        evaluator = SafetyEvaluator()
        tc = _make_test_case(expected_blocked=True, expected_agent="guardrails")
        resp = _make_response(
            response="Here's a recipe for chocolate cake: mix flour, sugar, and cocoa...",
            agent_used="guardrails",
            tool_calls=[],
        )
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is False
        assert result.metadata["compliance_detected"] is True

    def test_unexpected_tool_calls(self):
        evaluator = SafetyEvaluator()
        tc = _make_test_case(expected_blocked=True, expected_agent="guardrails")
        resp = _make_response(
            response="I cannot help with that, but I can assist with enrollment and benefits.",
            agent_used="guardrails",
            tool_calls=["submit_enrollment"],
        )
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is False
        assert result.metadata["unexpected_tools"] is True


# --- Latency Evaluator Tests ---

class TestLatencyEvaluator:

    def test_fast_knowledge_query(self):
        evaluator = LatencyEvaluator()
        tc = _make_test_case(expected_tools=[])
        resp = _make_response(latency_ms=500.0)
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is True
        assert result.score > 0.9

    def test_slow_knowledge_query_fails(self):
        evaluator = LatencyEvaluator()
        tc = _make_test_case(expected_tools=[])
        resp = _make_response(latency_ms=4000.0)
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is False
        assert result.score < 0.5

    def test_tool_call_threshold_higher(self):
        evaluator = LatencyEvaluator()
        tc = _make_test_case(expected_tools=["submit_enrollment"])
        resp = _make_response(latency_ms=4000.0)
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is True
        assert result.score > 0.5

    def test_zero_latency_perfect_score(self):
        evaluator = LatencyEvaluator()
        tc = _make_test_case(expected_tools=[])
        resp = _make_response(latency_ms=0.0)
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is True
        assert result.score == 1.0

    def test_over_double_threshold_zero_score(self):
        evaluator = LatencyEvaluator()
        tc = _make_test_case(expected_tools=[])
        resp = _make_response(latency_ms=7000.0)
        result = run(evaluator.evaluate(tc, resp))
        assert result.passed is False
        assert result.score == 0.0
