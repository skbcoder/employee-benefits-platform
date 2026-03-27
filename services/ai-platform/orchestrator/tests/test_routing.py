"""Tests for the router node — intent classification and routing decisions."""


from src.graph.router_node import _fast_classify, _parse_llm_classification


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

    def test_context_continuity_enrollment_details(self):
        """When history shows enrollment context, follow-up with details stays in enrollment."""
        history = [
            {"role": "user", "content": "help me enroll in a medical plan"},
            {"role": "assistant", "content": "I need your Employee ID, name, and email."},
        ]
        result = _fast_classify("T12345, John Smith, john@company.com", history)
        assert result is not None
        assert result.intent == "ENROLLMENT"

    def test_context_continuity_plan_selection(self):
        """Plan name in follow-up with enrollment history routes to enrollment."""
        history = [
            {"role": "user", "content": "I want to submit enrollment"},
            {"role": "assistant", "content": "Which plan tier? basic, silver, gold, platinum"},
        ]
        result = _fast_classify("silver medical", history)
        assert result is not None
        assert result.intent == "ENROLLMENT"

    def test_context_continuity_question_breaks_out(self):
        """A question about plans should break out of enrollment context."""
        history = [
            {"role": "user", "content": "What enrollments are currently processing?"},
            {"role": "assistant", "content": "There are no enrollments in PROCESSING status."},
        ]
        result = _fast_classify("how many dental plans are there?", history)
        assert result is None  # Falls through to LLM classification

    def test_context_continuity_general_question_breaks_out(self):
        """Asking 'what are the dental options' should not stay in enrollment."""
        history = [
            {"role": "user", "content": "I want to enroll"},
            {"role": "assistant", "content": "I need your details."},
        ]
        result = _fast_classify("what are the dental plan options?", history)
        assert result is None

    def test_no_context_continuity_without_history(self):
        """Without enrollment history, ambiguous message falls through."""
        result = _fast_classify("silver medical", None)
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
