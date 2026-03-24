"""Tests for PII detection and redaction."""

from src.compliance.pii_detector import (
    PIIType,
    detect_pii,
    redact_pii,
    score_pii_risk,
)


class TestDetectPII:
    def test_detect_ssn_dashed(self):
        detections = detect_pii("My SSN is 123-45-6789.")
        assert len(detections) >= 1
        ssn = [d for d in detections if d.pii_type == PIIType.SSN]
        assert len(ssn) == 1
        assert ssn[0].value == "123-45-6789"

    def test_detect_email(self):
        detections = detect_pii("Contact me at jane.doe@example.com please.")
        emails = [d for d in detections if d.pii_type == PIIType.EMAIL]
        assert len(emails) == 1
        assert emails[0].value == "jane.doe@example.com"

    def test_detect_phone_dashed(self):
        detections = detect_pii("Call 555-123-4567 for info.")
        phones = [d for d in detections if d.pii_type == PIIType.PHONE]
        assert len(phones) == 1
        assert phones[0].value == "555-123-4567"

    def test_detect_phone_parentheses(self):
        detections = detect_pii("Phone: (555) 123-4567")
        phones = [d for d in detections if d.pii_type == PIIType.PHONE]
        assert len(phones) == 1
        assert "555" in phones[0].value
        assert "4567" in phones[0].value

    def test_detect_credit_card(self):
        detections = detect_pii("Card number: 4111-1111-1111-1111")
        cards = [d for d in detections if d.pii_type == PIIType.CREDIT_CARD]
        assert len(cards) == 1

    def test_detect_credit_card_no_dashes(self):
        detections = detect_pii("Card: 4111111111111111")
        cards = [d for d in detections if d.pii_type == PIIType.CREDIT_CARD]
        assert len(cards) >= 1

    def test_detect_date_of_birth(self):
        detections = detect_pii("DOB: 01/15/1990")
        dobs = [d for d in detections if d.pii_type == PIIType.DATE_OF_BIRTH]
        assert len(dobs) == 1
        assert dobs[0].value == "01/15/1990"

    def test_detect_multiple_pii_types(self):
        text = "SSN 123-45-6789, email test@mail.com, phone 555-111-2222"
        detections = detect_pii(text)
        types_found = {d.pii_type for d in detections}
        assert PIIType.SSN in types_found
        assert PIIType.EMAIL in types_found
        assert PIIType.PHONE in types_found

    def test_no_pii_in_clean_text(self):
        detections = detect_pii("This is a normal sentence with no personal data.")
        assert len(detections) == 0

    def test_positions_are_correct(self):
        text = "SSN: 123-45-6789"
        detections = detect_pii(text)
        ssn = [d for d in detections if d.pii_type == PIIType.SSN][0]
        assert text[ssn.start_pos : ssn.end_pos] == "123-45-6789"


class TestRedactPII:
    def test_redact_ssn(self):
        result = redact_pii("SSN is 123-45-6789")
        assert "123-45-6789" not in result
        assert "[SSN REDACTED]" in result

    def test_redact_email(self):
        result = redact_pii("Email: user@example.com")
        assert "user@example.com" not in result
        assert "[EMAIL REDACTED]" in result

    def test_redact_preserves_clean_text(self):
        text = "No PII here."
        assert redact_pii(text) == text

    def test_redact_multiple_types(self):
        text = "SSN 123-45-6789 email a@b.com"
        result = redact_pii(text)
        assert "[SSN REDACTED]" in result
        assert "[EMAIL REDACTED]" in result


class TestScorePIIRisk:
    def test_no_detections_zero_risk(self):
        assert score_pii_risk([]) == 0.0

    def test_ssn_max_risk(self):
        detections = detect_pii("SSN: 123-45-6789")
        score = score_pii_risk(detections)
        assert score == 1.0

    def test_email_lower_risk(self):
        detections = detect_pii("email: a@b.com")
        score = score_pii_risk(detections)
        assert 0.0 < score < 1.0

    def test_mixed_pii_uses_max(self):
        detections = detect_pii("SSN 123-45-6789 email a@b.com")
        score = score_pii_risk(detections)
        assert score == 1.0  # SSN dominates
