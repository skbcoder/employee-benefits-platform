"""Tests for the router node — intent classification and routing decisions."""

import pytest

from src.graph.router_node import _fast_classify, _parse_llm_classification
from src.models.state import AgentType


class TestFastClassify:
    """Test deterministic keyword-based classification."""

    def test_enrollment_keywords(self):
        result = _fast_classify("I want to enroll in the enrollment plan")
        assert result is not None
        assert result.intent == "ENROLLMENT"
        assert result.needs_tool_access is True

    def test_compliance_keywords(self):
        result = _fast_classify("What are the HIPAA requirements?")
        assert result is not None
        assert result.intent == "COMPLIANCE"
        assert result.needs_tool_access is False

    def test_off_topic_no_benefits_signal(self):
        result = _fast_classify("What's a good recipe for pasta?")
        assert result is not None
        assert result.is_off_topic is True

    def test_off_topic_with_benefits_signal(self):
        """Sports keyword but also mentions benefits — should NOT be off-topic."""
        result = _fast_classify("Does my sports injury coverage benefit include dental?")
        # Benefits signal present → should not classify as off-topic
        assert result is None or not result.is_off_topic

    def test_ambiguous_falls_through(self):
        """Ambiguous queries return None — delegate to LLM."""
        result = _fast_classify("Tell me about the gold plan")
        assert result is None

    def test_empty_message(self):
        result = _fast_classify("")
        assert result is None


class TestParseLlmClassification:
    """Test parsing of LLM classification responses."""

    def test_valid_json(self):
        raw = '{"category": "ENROLLMENT", "confidence": 0.9, "needs_tools": true, "entities": {}, "reasoning": "test"}'
        result = _parse_llm_classification(raw)
        assert result.intent == "ENROLLMENT"
        assert result.needs_tool_access is True

    def test_json_embedded_in_text(self):
        raw = 'Based on analysis: {"category": "ADVISOR", "confidence": 0.8, "needs_tools": false, "entities": {}, "reasoning": "policy question"} done.'
        result = _parse_llm_classification(raw)
        assert result.intent == "ADVISOR"

    def test_plain_text_category(self):
        raw = "This is clearly an ENROLLMENT request."
        result = _parse_llm_classification(raw)
        assert result.intent == "ENROLLMENT"

    def test_off_topic_detection(self):
        raw = '{"category": "OFF_TOPIC", "confidence": 0.95, "needs_tools": false, "entities": {}, "reasoning": "cooking"}'
        result = _parse_llm_classification(raw)
        assert result.is_off_topic is True

    def test_harmful_detection(self):
        raw = '{"category": "HARMFUL", "confidence": 0.99, "needs_tools": false, "entities": {}, "reasoning": "malicious"}'
        result = _parse_llm_classification(raw)
        assert result.is_harmful is True

    def test_garbage_input_defaults_to_advisor(self):
        result = _parse_llm_classification("alksjdflaksjdf")
        assert result.intent == "ADVISOR"
