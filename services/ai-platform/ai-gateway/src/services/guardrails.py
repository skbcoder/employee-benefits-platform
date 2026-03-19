"""Guardrails — input validation, output filtering, and RAG sanitization."""

import logging
import re
import unicodedata
from typing import NamedTuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  Result type
# ---------------------------------------------------------------------------


class GuardrailResult(NamedTuple):
    blocked: bool
    response: str | None  # canned response when blocked
    reason: str | None  # machine-readable reason for audit


_PASS = GuardrailResult(blocked=False, response=None, reason=None)

_MAX_MESSAGE_LENGTH = 2000

# ---------------------------------------------------------------------------
#  Text normalization helpers
# ---------------------------------------------------------------------------

_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\u2060\ufeff\u00ad]")

_LEET_BASE = {
    "!": "i", "3": "e", "0": "o",
    "4": "a", "@": "a", "5": "s",
    "$": "s", "7": "t", "8": "b",
}


def _normalize(text: str) -> str:
    """Normalize text for robust pattern matching.

    - Unicode NFKC normalization (fullwidth -> ASCII, homoglyphs collapsed)
    - Strip zero-width characters
    - Collapse whitespace
    """
    text = unicodedata.normalize("NFKC", text)
    text = _ZERO_WIDTH_RE.sub("", text)
    text = " ".join(text.split())
    return text


def _deleet_variants(text: str) -> list[str]:
    """Decode common leet-speak — returns variants for ambiguous chars.

    '1' can be 'i' or 'l', so we replace each '1' with both and
    return all distinct results. Capped to avoid combinatorial explosion.
    """
    # First apply the unambiguous substitutions
    base = "".join(_LEET_BASE.get(ch, ch) for ch in text)

    # Handle ambiguous '1' → 'i' or 'l' by position
    ones = [i for i, ch in enumerate(base) if text[i] == "1"]
    if not ones or len(ones) > 8:
        # No ambiguity or too many — just return both simple maps
        return [base.replace("1", "i"), base.replace("1", "l")]

    results: set[str] = set()
    for mask in range(1 << len(ones)):
        chars = list(base)
        for bit, pos in enumerate(ones):
            chars[pos] = "l" if (mask >> bit) & 1 else "i"
        results.add("".join(chars))
    return list(results)


# ---------------------------------------------------------------------------
#  Prompt injection patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERN_STRINGS = [
    # Instruction override attempts
    r"ignore\s+(all\s+)?(your\s+)?(previous\s+)?(instructions?|prompts?|rules?)",
    r"ignore\s+your\s+(instructions?|rules?|guidelines?|programming)",
    r"disregard\s+(all\s+)?(previous|your|above|prior)",
    r"forget\s+(all\s+)?(your|previous|prior)\s+(instructions?|rules?|prompts?)",
    r"override\s+(your|all|the)\s+(instructions?|rules?|settings?|constraints?)",
    r"new\s+instructions?\s*:",
    # Persona / role-play hijacking
    r"you\s+are\s+now\s+(?!an?\s+employee\b|an?\s+enrollment\b|an?\s+HR\b|an?\s+benefits?\b)",
    r"pretend\s+(you\s+are|to\s+be|you'?re)",
    r"act\s+as\s+(if\s+you\s+are\s+|a\s+|an?\s+)(?!benefits?\b|enrollment\b|HR\b)",
    r"imagine\s+you\s+are",
    r"role\s*-?\s*play\s+as",
    r"switch\s+to\s+.{0,20}\s*mode",
    r"enter\s+.{0,20}\s*mode",
    r"new\s+persona",
    r"adopt\s+the\s+(role|persona|identity)",
    # Jailbreak / exploit keywords
    r"\bjailbreak\b",
    r"\bDAN\s*mode\b",
    r"\bdo\s+anything\s+now\b",
    r"\bdevil\s*'?s?\s+advocate\b",
    r"\bunfiltered\s+mode\b",
    r"\bno\s+restrictions?\s+mode\b",
    r"\bgod\s+mode\b",
    # System prompt / rules probing — "your" required for generic words
    # to avoid blocking legitimate queries like "what are the rules of dental"
    r"(what|show|reveal|repeat|print|display|tell|give|list|enumerate|describe|explain)"
    r"\s+(me\s+)?(all\s+)?(is\s+|are\s+)?your\s+"
    r"(system\s+prompt|instructions?|rules?|guidelines?|constraints?"
    r"|guardrails?|restrictions?|limitations?|boundaries|directives?"
    r"|programming|configuration|settings?)",
    r"(what|show|reveal|repeat|print|display|tell|give|list|enumerate|describe|explain)"
    r"\s+(me\s+)?(all\s+)?(is\s+|are\s+)?the\s+"
    r"(system\s+prompt|guardrails?|directives?|programming|configuration)",
    r"output\s+(your|the)\s+(system\s+)?(prompt|instructions?)",
    r"(read|dump|echo)\s+(back\s+)?(your|the)\s+(system|initial)"
    r"\s+(prompt|message)",
    r"system\s+prompt",
    r"(list|what\s+are|tell\s+me|describe|enumerate|show)"
    r"\s+(all\s+)?your\s+"
    r"(guardrails?|rules?|restrictions?|constraints?"
    r"|limitations?|boundaries|safety\s+measures?)",
    r"(what|how)\s+(do|can)\s+you\s+(not|refuse|won'?t|can'?t)\s+(do|answer|discuss|talk\s+about)",
    r"what\s+topics?\s+(can'?t|won'?t|don'?t)\s+you",
    r"what\s+(are|is)\s+you\s+(not\s+)?allowed\s+to",
    # Encoded / obfuscated attacks
    r"base64\s*[\(:]",
    r"decode\s+(this|the\s+following)",
    r"translate\s+from\s+(hex|binary|base64|rot13)",
    r"execute\s+(this|the\s+following)\s+(code|script|command)",
]

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERN_STRINGS
]

_INJECTION_RESPONSE = (
    "I'm here to help with employee benefits! "
    "Would you like to check your enrollment status, compare plans, "
    "or learn about your coverage options?"
)

# ---------------------------------------------------------------------------
#  Harmful / disallowed content patterns
# ---------------------------------------------------------------------------

_HARMFUL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"how\s+to\s+(make|build|create|assemble)\s+.{0,20}(bomb|weapon|explosive|gun|firearm)",
        r"how\s+to\s+(hack|break\s+into|exploit|crack)",
        r"how\s+to\s+(steal|forge|counterfeit|launder)",
        r"how\s+to\s+(poison|drug|harm|hurt|kill|attack)\s+(someone|a\s+person|people)",
        r"(write|generate|create)\s+(malware|virus|ransomware|trojan|exploit)",
        r"(child|minor)\s+(abuse|exploitation|pornograph)",
        r"(make|synthesize|produce)\s+.{0,20}(drugs?|meth|cocaine|fentanyl)",
        r"(illegal|illicit)\s+(substance|drug|weapon|activity).*how",
    ]
]

_HARMFUL_RESPONSE = (
    "I'm only able to assist with employee benefits topics. "
    "Can I help you with medical, dental, vision, or life plan details?"
)

_LENGTH_RESPONSE = (
    "Could you shorten your question a bit? "
    "I work best with concise benefits-related questions."
)

# ---------------------------------------------------------------------------
#  Output leak detection patterns
# ---------------------------------------------------------------------------

_OUTPUT_LEAK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        # System prompt / instruction leaks
        r"my\s+(system\s+)?prompt\s+(is|says|states|includes|contains)",
        r"my\s+(instructions?|rules?|guidelines?|guardrails?)\s+(are|include|say|state)",
        r"i\s+(was|am)\s+(told|instructed|configured|programmed)\s+to",
        r"(here\s+are|these\s+are|the\s+following\s+are)\s+my\s+"
        r"(rules?|instructions?|guardrails?|guidelines?"
        r"|constraints?|restrictions?)",
        r"my\s+configuration\s+(is|includes|states)",
        r"(as\s+per|according\s+to)\s+my\s+(instructions?|programming|rules?)",
        # Self-description / identity leaks — LLM talking about itself as a system
        r"i'?m\s+a\s+(fixed|permanent|programmed|configured)\s+(and\s+\w+\s+)?entity",
        r"my\s+(purpose|role|function)\s+is\s+to\s+(assist|help)",
        r"(compliance|rules?|guardrails?)\s+(areas?\s+)?(relevant|related)"
        r"\s+to\s+my\s+role",
        r"(for|about)\s+(the\s+)?(employee\s+benefits?\s+)?"
        r"(enrollment\s+)?assistant\s*\(me\)",
        r"no\s+ability\s+to\s+(change|adapt|modify)",
        r"i\s+(cannot|can'?t)\s+(change|adapt|modify)\s+(based\s+on|my)",
        # Internal system terms that should never appear in user-facing responses
        r"\boutbox_event\b",
        r"\binbox_message\b",
        r"\benrollment_record\b",
        r"\bprocessing_record\b",
        r"\bclaimed_at\b",
        r"\bclaimed_by\b",
        r"\bdelivery_status\b",
        r"\baggregate_type\b",
        r"\bcorrelation_id\b",
    ]
]

# UUID pattern — enrollment UUIDs should never be in user responses
_UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

_OUTPUT_SAFE_FALLBACK = (
    "I can help you with employee benefits — enrollment, plan details, "
    "status checks, and more. What would you like to know?"
)

# ---------------------------------------------------------------------------
#  Non-Latin script detection
# ---------------------------------------------------------------------------


def _non_latin_ratio(text: str) -> float:
    """Return the ratio of non-Latin, non-common characters in the text."""
    if not text:
        return 0.0
    non_latin = 0
    total = 0
    for ch in text:
        cat = unicodedata.category(ch)
        if cat.startswith("L"):  # Letter category
            total += 1
            script = unicodedata.name(ch, "").split()[0] if unicodedata.name(ch, "") else ""
            if script not in ("LATIN", "DIGIT"):
                non_latin += 1
    return non_latin / total if total > 0 else 0.0


_NON_LATIN_RESPONSE = (
    "I work best in English. Feel free to ask me about medical, dental, "
    "vision, or life benefits and I'll be happy to help!"
)

# ---------------------------------------------------------------------------
#  Public API — Input checking
# ---------------------------------------------------------------------------


def check_input(message: str) -> GuardrailResult:
    """Check user input against guardrail patterns.

    Applies: length limit, unicode normalization, leet-speak decoding,
    non-Latin detection, injection patterns, harmful content patterns.
    """
    # Length check (before normalization to catch padding attacks)
    if len(message) > _MAX_MESSAGE_LENGTH:
        logger.warning(f"Guardrail blocked (length): {len(message)} chars")
        return GuardrailResult(blocked=True, response=_LENGTH_RESPONSE, reason="message_too_long")

    # Normalize for pattern matching
    normalized = _normalize(message)

    # Non-Latin script check — >80% non-Latin letters likely an obfuscation attempt
    if _non_latin_ratio(normalized) > 0.8 and len(normalized) > 10:
        logger.warning(f"Guardrail blocked (non-latin): '{message[:100]}...'")
        return GuardrailResult(blocked=True, response=_NON_LATIN_RESPONSE, reason="non_latin_script")

    # Check both the normalized text and leet-decoded variants
    variants = [normalized] + _deleet_variants(normalized)

    for variant in variants:
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(variant):
                logger.warning(f"Guardrail blocked (injection): '{message[:100]}...'")
                return GuardrailResult(blocked=True, response=_INJECTION_RESPONSE, reason="prompt_injection")

        for pattern in _HARMFUL_PATTERNS:
            if pattern.search(variant):
                logger.warning(f"Guardrail blocked (harmful): '{message[:100]}...'")
                return GuardrailResult(blocked=True, response=_HARMFUL_RESPONSE, reason="harmful_content")

    return _PASS


# ---------------------------------------------------------------------------
#  Public API — Output filtering
# ---------------------------------------------------------------------------


def check_output(response: str) -> str:
    """Scan LLM response for leaked system info, UUIDs, or internal data.

    Returns the original response if clean, or a safe fallback if leaks detected.
    """
    # Check for system prompt / instruction leaks
    for pattern in _OUTPUT_LEAK_PATTERNS:
        if pattern.search(response):
            logger.warning(f"Output filter triggered (leak): pattern={pattern.pattern!r}")
            return _OUTPUT_SAFE_FALLBACK

    # Check for UUID leaks
    if _UUID_PATTERN.search(response):
        logger.warning("Output filter triggered (UUID leak)")
        return _OUTPUT_SAFE_FALLBACK

    # Check for harmful content in response
    for pattern in _HARMFUL_PATTERNS:
        if pattern.search(response):
            logger.warning(f"Output filter triggered (harmful): pattern={pattern.pattern!r}")
            return _OUTPUT_SAFE_FALLBACK

    return response


# ---------------------------------------------------------------------------
#  Public API — RAG content sanitization
# ---------------------------------------------------------------------------


def sanitize_rag_context(context: str) -> str:
    """Strip prompt injection patterns from RAG context to prevent indirect attacks.

    Removes lines that contain injection-like patterns while preserving
    legitimate knowledge base content.
    """
    if not context:
        return context

    clean_lines = []
    stripped_count = 0

    for line in context.split("\n"):
        normalized_line = _normalize(line)
        is_poisoned = False

        for pattern in _INJECTION_PATTERNS:
            if pattern.search(normalized_line):
                is_poisoned = True
                break

        if not is_poisoned:
            for pattern in _HARMFUL_PATTERNS:
                if pattern.search(normalized_line):
                    is_poisoned = True
                    break

        if is_poisoned:
            stripped_count += 1
            logger.warning(f"RAG sanitizer stripped line: '{line[:100]}...'")
        else:
            clean_lines.append(line)

    if stripped_count > 0:
        logger.warning(f"RAG sanitizer stripped {stripped_count} poisoned lines")

    return "\n".join(clean_lines)
