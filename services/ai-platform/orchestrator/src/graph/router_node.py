"""Router node — classifies user intent and decides which agent(s) to invoke."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from config.settings import settings
from src.graph.state import AgentState
from src.models.decisions import IntentClassification, RoutingDecision
from src.models.state import AgentType
from src.providers.provider_factory import get_provider

logger = logging.getLogger(__name__)

# Keywords that strongly indicate which agent is needed
_ENROLLMENT_KEYWORDS = [
    "enroll", "enrollment", "submit", "status", "check my",
    "employee id", "my benefits", "my enrollment", "my plan",
    "sign up", "register", "cancel", "update enrollment",
]

_COMPLIANCE_KEYWORDS = [
    "compliance", "erisa", "hipaa", "aca", "cobra",
    "audit", "violation", "regulation", "legal",
    "section 125", "fiduciary",
]

_OFF_TOPIC_INDICATORS = [
    "recipe", "weather", "sports", "politics", "code", "programming",
    "joke", "poem", "story", "song", "movie", "game",
]

_CLASSIFICATION_PROMPT = """You are an intent classifier for an employee benefits platform.
Classify the user's message into exactly ONE category:

ENROLLMENT — user wants to submit, check, update, or look up enrollment data
ADVISOR — user asks about plan details, coverage, eligibility, deductibles, benefits policies
COMPLIANCE — user asks about regulations, legal requirements, ERISA, HIPAA, ACA, COBRA
OFF_TOPIC — question is not related to employee benefits
HARMFUL — request contains harmful, offensive, or manipulative content

Respond with ONLY a JSON object:
{{"category": "ENROLLMENT|ADVISOR|COMPLIANCE|OFF_TOPIC|HARMFUL", "confidence": 0.0-1.0, "needs_tools": true|false, "entities": {{}}, "reasoning": "brief explanation"}}

User message: {message}"""


_CATEGORY_TO_AGENT: dict[str, AgentType] = {
    "ENROLLMENT": AgentType.ENROLLMENT,
    "ADVISOR": AgentType.ADVISOR,
    "COMPLIANCE": AgentType.COMPLIANCE,
}


def _fast_classify(message: str) -> IntentClassification | None:
    """Fast deterministic classification using keyword matching.

    Returns None if no strong signal — falls through to LLM classification.
    """
    msg_lower = message.lower()

    # Off-topic check
    if any(kw in msg_lower for kw in _OFF_TOPIC_INDICATORS):
        benefits_signal = any(
            kw in msg_lower
            for kw in ["benefit", "plan", "coverage", "dental", "medical", "vision"]
        )
        if not benefits_signal:
            return IntentClassification(
                intent="OFF_TOPIC", is_off_topic=True, needs_tool_access=False
            )

    # Enrollment — strong keyword match
    enrollment_hits = sum(1 for kw in _ENROLLMENT_KEYWORDS if kw in msg_lower)
    if enrollment_hits >= 2:
        return IntentClassification(
            intent="ENROLLMENT", needs_tool_access=True, needs_rag=False
        )

    # Compliance — strong keyword match
    compliance_hits = sum(1 for kw in _COMPLIANCE_KEYWORDS if kw in msg_lower)
    if compliance_hits >= 1:
        return IntentClassification(
            intent="COMPLIANCE", needs_tool_access=False, needs_rag=True
        )

    return None


def _parse_llm_classification(raw: str) -> IntentClassification:
    """Parse LLM classification response into structured intent."""
    # Try to extract JSON from response
    json_match = re.search(r"\{[^}]+\}", raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            category = data.get("category", "ADVISOR").upper()
            return IntentClassification(
                intent=category,
                is_off_topic=category == "OFF_TOPIC",
                is_harmful=category == "HARMFUL",
                needs_tool_access=data.get("needs_tools", False),
                needs_rag=category in ("ADVISOR", "COMPLIANCE"),
                entities=data.get("entities", {}),
            )
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback: look for category keywords in raw text
    raw_upper = raw.upper()
    for cat in ("ENROLLMENT", "COMPLIANCE", "OFF_TOPIC", "HARMFUL"):
        if cat in raw_upper:
            return IntentClassification(
                intent=cat,
                is_off_topic=cat == "OFF_TOPIC",
                is_harmful=cat == "HARMFUL",
                needs_tool_access=cat == "ENROLLMENT",
                needs_rag=cat in ("ADVISOR", "COMPLIANCE"),
            )

    # Default to advisor
    return IntentClassification(intent="ADVISOR", needs_rag=True)


async def router_node(state: AgentState) -> dict[str, Any]:
    """Classify user intent and decide routing.

    Uses fast keyword matching first, falls back to LLM classification
    for ambiguous queries.
    """
    user_message = state["user_message"]
    logger.info(f"Router: classifying '{user_message[:80]}'")

    # Phase 1: Fast deterministic classification
    intent = _fast_classify(user_message)

    if intent is None:
        # Phase 2: LLM-based classification
        provider = get_provider()
        prompt = _CLASSIFICATION_PROMPT.format(message=user_message)
        raw = await provider.classify(prompt)
        intent = _parse_llm_classification(raw)
        logger.info(f"Router: LLM classified as {intent.intent} (raw: '{raw[:100]}')")
    else:
        logger.info(f"Router: fast-classified as {intent.intent}")

    # Build routing decision
    if intent.is_off_topic or intent.is_harmful:
        routing = RoutingDecision(
            primary_agent=AgentType.ADVISOR,  # Advisor handles off-topic deflection
            confidence=0.9,
            reasoning=f"Query classified as {intent.intent}",
        )
    else:
        primary = _CATEGORY_TO_AGENT.get(intent.intent, AgentType.ADVISOR)
        secondary = []

        # Enrollment actions also get a compliance pre-check
        if primary == AgentType.ENROLLMENT:
            routing = RoutingDecision(
                primary_agent=primary,
                secondary_agents=secondary,
                confidence=0.8,
                reasoning=f"Routed to {primary.value} agent",
                requires_compliance_check=True,
            )
        else:
            routing = RoutingDecision(
                primary_agent=primary,
                confidence=0.8,
                reasoning=f"Routed to {primary.value} agent",
            )

    # Low confidence → escalate
    if routing.confidence < settings.routing_confidence_threshold:
        routing = RoutingDecision(
            primary_agent=AgentType.ESCALATION,
            confidence=routing.confidence,
            reasoning="Low routing confidence — escalating",
        )

    return {"intent": intent, "routing": routing}
