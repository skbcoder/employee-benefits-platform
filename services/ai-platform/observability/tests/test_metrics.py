"""Tests for the observability metrics collector and cost tracker."""

import asyncio

import pytest

from src.metrics.collector import (
    agent_request_total,
    agent_tool_call_total,
    agent_token_usage_total,
    agent_guardrail_trigger_total,
    agent_governance_decision_total,
    pii_detection_total,
    metrics_endpoint,
    record_tool_call,
    record_token_usage,
    record_guardrail_trigger,
    record_governance_decision,
    record_pii_detection,
    observe_rag_search,
    set_cost,
)
from src.cost.tracker import CostTracker


def run(coro):
    return asyncio.run(coro)


class TestRecordToolCall:
    def test_increments_tool_counter(self):
        before = agent_tool_call_total.labels(tool_name="lookup_enrollment")._value.get()
        record_tool_call("lookup_enrollment")
        after = agent_tool_call_total.labels(tool_name="lookup_enrollment")._value.get()
        assert after == before + 1

    def test_different_tools_tracked_separately(self):
        record_tool_call("tool_a")
        record_tool_call("tool_b")
        record_tool_call("tool_a")
        val_a = agent_tool_call_total.labels(tool_name="tool_a")._value.get()
        val_b = agent_tool_call_total.labels(tool_name="tool_b")._value.get()
        assert val_a >= 2
        assert val_b >= 1


class TestRecordTokenUsage:
    def test_increments_token_counter(self):
        before = agent_token_usage_total.labels(model="test-model")._value.get()
        record_token_usage("test-model", 150)
        after = agent_token_usage_total.labels(model="test-model")._value.get()
        assert after == before + 150


class TestOtherHelpers:
    def test_record_guardrail_trigger(self):
        before = agent_guardrail_trigger_total.labels(guardrail_type="injection")._value.get()
        record_guardrail_trigger("injection")
        after = agent_guardrail_trigger_total.labels(guardrail_type="injection")._value.get()
        assert after == before + 1

    def test_record_governance_decision(self):
        before = agent_governance_decision_total.labels(decision="allow")._value.get()
        record_governance_decision("allow")
        after = agent_governance_decision_total.labels(decision="allow")._value.get()
        assert after == before + 1

    def test_record_pii_detection(self):
        before = pii_detection_total.labels(pii_type="ssn")._value.get()
        record_pii_detection("ssn")
        after = pii_detection_total.labels(pii_type="ssn")._value.get()
        assert after == before + 1

    def test_metrics_endpoint_returns_string(self):
        output = metrics_endpoint()
        assert isinstance(output, str)
        assert len(output) > 0

    def test_observe_rag_search(self):
        observe_rag_search("knowledge-service", 0.25)

    def test_set_cost(self):
        set_cost("claude-sonnet", "daily", 1.23)


class TestCostTracker:
    def test_get_request_cost_known_model(self):
        cost = CostTracker.get_request_cost(
            "us.anthropic.claude-3-5-haiku-20241022-v1:0",
            prompt_tokens=1000,
            completion_tokens=1000,
        )
        assert abs(cost - 0.006) < 1e-9

    def test_get_request_cost_unknown_model(self):
        cost = CostTracker.get_request_cost("unknown-model", 500, 500)
        assert cost == 0.0

    def test_get_request_cost_ollama_free(self):
        cost = CostTracker.get_request_cost("llama3.1:8b", 10000, 5000)
        assert cost == 0.0

    def test_record_and_daily_summary(self):
        tracker = CostTracker()
        cost = run(tracker.record(
            "us.anthropic.claude-3-5-haiku-20241022-v1:0", 1000, 1000
        ))
        assert abs(cost - 0.006) < 1e-9

        summary = run(tracker.get_daily_summary())
        assert summary["total_tokens"] == 2000
        assert summary["total_cost_usd"] == round(0.006, 6)

    def test_daily_summary_empty(self):
        tracker = CostTracker()
        summary = run(tracker.get_daily_summary())
        assert summary["total_tokens"] == 0
        assert summary["total_cost_usd"] == 0.0

    def test_multiple_records_accumulate(self):
        tracker = CostTracker()
        run(tracker.record("us.anthropic.claude-sonnet-4-20250514-v1:0", 1000, 1000))
        run(tracker.record("us.anthropic.claude-sonnet-4-20250514-v1:0", 2000, 500))
        summary = run(tracker.get_daily_summary())
        assert summary["total_tokens"] == 4500
        expected = round(0.018 + 0.0135, 6)
        assert summary["total_cost_usd"] == expected
