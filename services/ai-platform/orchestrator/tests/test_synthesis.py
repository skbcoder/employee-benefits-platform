"""Tests for the synthesis node — response merging and output sanitization."""

import pytest

from src.graph.synthesis_node import _fix_markdown_tables, _sanitize_response


class TestSanitizeResponse:
    """Test output sanitization before final response."""

    def test_strips_uuids(self):
        text = "Enrollment 550e8400-e29b-41d4-a716-446655440000 was created."
        result = _sanitize_response(text)
        assert "550e8400" not in result
        assert "[enrollment reference]" in result

    def test_strips_internal_terms(self):
        text = "The outbox_event was processed and inbox_message received."
        result = _sanitize_response(text)
        assert "outbox_event" not in result
        assert "inbox_message" not in result

    def test_redacts_emails(self):
        text = "Contact jane.doe@example.com for enrollment help."
        result = _sanitize_response(text)
        assert "jane.doe@example.com" not in result
        assert "[email redacted]" in result

    def test_preserves_clean_text(self):
        text = "Your Gold Medical plan has a $500 deductible."
        result = _sanitize_response(text)
        assert result == text

    def test_handles_multiple_issues(self):
        text = (
            "Enrollment 550e8400-e29b-41d4-a716-446655440000 for "
            "user@test.com via outbox_event is complete."
        )
        result = _sanitize_response(text)
        assert "550e8400" not in result
        assert "user@test.com" not in result
        assert "outbox_event" not in result


class TestFixMarkdownTables:
    """Test markdown table fixing for LLM output."""

    def test_adds_missing_separator(self):
        text = "Results:\n| Name | Status |\n| John | COMPLETED |\n| Jane | PROCESSING |"
        result = _fix_markdown_tables(text)
        assert "| --- | --- |" in result
        # Separator should appear exactly once
        assert result.count("| --- | --- |") == 1

    def test_preserves_existing_separator(self):
        text = "| Name | Status |\n| --- | --- |\n| John | COMPLETED |"
        result = _fix_markdown_tables(text)
        assert result.count("---") == 2  # Only the original separator

    def test_removes_code_fences_around_tables(self):
        text = "Results:\n```\n| Name | Count |\n| A | 1 |\n```"
        result = _fix_markdown_tables(text)
        assert "```" not in result
        assert "| Name | Count |" in result

    def test_removes_extra_separator_rows(self):
        text = "| Status | Count |\n| --- | --- |\n| A | 1 |\n| --- | --- |\n| B | 2 |"
        result = _fix_markdown_tables(text)
        assert result.count("| --- | --- |") == 1

    def test_preserves_non_table_text(self):
        text = "Hello world.\n\nNo tables here."
        result = _fix_markdown_tables(text)
        assert result == text
