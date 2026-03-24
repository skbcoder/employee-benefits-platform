"""PII detection and redaction in text.

Uses regex patterns to identify common PII types (SSN, email, phone,
credit card, date of birth, address) and provides redaction utilities.
"""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel


class PIIType(str, Enum):
    SSN = "SSN"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CREDIT_CARD = "CREDIT_CARD"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    ADDRESS = "ADDRESS"


class PIIDetection(BaseModel):
    pii_type: PIIType
    value: str
    start_pos: int
    end_pos: int


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_PII_PATTERNS: list[tuple[PIIType, re.Pattern]] = [
    # SSN: 123-45-6789 or 123456789
    (PIIType.SSN, re.compile(r"\b(\d{3}-\d{2}-\d{4})\b")),
    (PIIType.SSN, re.compile(r"\b(\d{9})\b(?![\d-])")),
    # Credit card: 16 digits with optional dashes/spaces
    (PIIType.CREDIT_CARD, re.compile(r"\b(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})\b")),
    # Email
    (PIIType.EMAIL, re.compile(r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b")),
    # Phone: various US formats
    (PIIType.PHONE, re.compile(r"\b(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b")),
    # Date of birth: MM/DD/YYYY or MM-DD-YYYY
    (PIIType.DATE_OF_BIRTH, re.compile(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b")),
    # Street address (basic pattern: number + street name + type)
    (PIIType.ADDRESS, re.compile(
        r"\b(\d{1,5}\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+"
        r"(?:St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Ln|Lane|Rd|Road|Ct|Court|Way|Pl|Place)\.?)\b"
    )),
]

# Risk weights by PII type.
_PII_RISK: dict[PIIType, float] = {
    PIIType.SSN: 1.0,
    PIIType.CREDIT_CARD: 0.9,
    PIIType.DATE_OF_BIRTH: 0.5,
    PIIType.PHONE: 0.3,
    PIIType.EMAIL: 0.3,
    PIIType.ADDRESS: 0.4,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_pii(text: str) -> list[PIIDetection]:
    """Scan *text* and return all PII detections."""
    detections: list[PIIDetection] = []
    seen_spans: set[tuple[int, int]] = set()

    for pii_type, pattern in _PII_PATTERNS:
        for match in pattern.finditer(text):
            span = (match.start(1), match.end(1))
            if span in seen_spans:
                continue
            seen_spans.add(span)
            detections.append(
                PIIDetection(
                    pii_type=pii_type,
                    value=match.group(1),
                    start_pos=span[0],
                    end_pos=span[1],
                )
            )

    # Sort by position for stable output.
    detections.sort(key=lambda d: d.start_pos)
    return detections


def redact_pii(text: str) -> str:
    """Return *text* with all detected PII replaced by ``[TYPE REDACTED]``."""
    detections = detect_pii(text)
    if not detections:
        return text

    # Process from end to start so positions stay valid.
    result = text
    for det in reversed(detections):
        placeholder = f"[{det.pii_type.value} REDACTED]"
        result = result[:det.start_pos] + placeholder + result[det.end_pos:]

    return result


def score_pii_risk(detections: list[PIIDetection]) -> float:
    """Return a 0.0 -- 1.0 risk score based on PII detections.

    0.0 means no PII; 1.0 means critical PII (e.g., SSN) is present.
    """
    if not detections:
        return 0.0

    max_risk = max(_PII_RISK.get(d.pii_type, 0.2) for d in detections)
    return min(max_risk, 1.0)
