"""Benefits Advisor node — answers policy, plan, and coverage questions using RAG."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import settings
from src.graph.state import AgentState
from src.models.state import AgentResult, AgentType
from src.providers.provider_factory import get_provider

logger = logging.getLogger(__name__)

_ADVISOR_SYSTEM_PROMPT = (
    "You are the benefits advisor agent. You answer questions about employee "
    "benefit plans, coverage details, eligibility rules, deductibles, copays, "
    "premiums, enrollment periods, and HR policies.\n\n"
    "Use the provided context to give accurate, specific answers. Cite plan "
    "names, dollar amounts, dates, and coverage percentages when available.\n\n"
    "If the user asks something unrelated to employee benefits, respond with "
    "a single witty sentence acknowledging you can't help, then offer a "
    "benefits-related suggestion.\n\n"
    "Format responses in Markdown: use tables for comparisons, bold for "
    "emphasis, and bullet lists for options."
)


async def _search_knowledge(query: str, category: str | None = None) -> str | None:
    """Search the Knowledge Service for relevant context."""
    url = f"{settings.knowledge_service_url}/api/knowledge/search"
    params: dict[str, Any] = {"query": query, "top_k": 5}
    if category:
        params["category"] = category

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            chunks = resp.json()
            if not chunks:
                return None

            parts = []
            for chunk in chunks:
                title = chunk.get("document_title", "Unknown")
                content = chunk.get("content", "")
                parts.append(f"[{title}]\n{content}")

            return "\n\n---\n\n".join(parts)
        except Exception as e:
            logger.warning(f"Knowledge search failed: {e}")
            return None


async def advisor_node(state: AgentState) -> dict[str, Any]:
    """Run the benefits advisor agent — RAG-augmented Q&A."""
    user_message = state["user_message"]
    intent = state.get("intent")
    logger.info(f"Advisor agent: processing '{user_message[:80]}'")

    # Handle off-topic / harmful queries
    if intent and (intent.is_off_topic or intent.is_harmful):
        result = AgentResult(
            agent=AgentType.ADVISOR,
            response=(
                "I'd love to help, but my expertise starts and ends at "
                "deductibles! Can I help you compare medical plans or "
                "check your enrollment status instead?"
            ),
            confidence=0.95,
        )
        return {"agent_results": [result]}

    # Search knowledge base
    rag_context = await _search_knowledge(user_message)
    rag_chunks_used = 0

    # If no results, try expanded query
    if not rag_context:
        expanded = f"employee benefits {user_message}"
        rag_context = await _search_knowledge(expanded)

    if rag_context:
        rag_chunks_used = rag_context.count("---") + 1

    # Build LLM messages
    provider = get_provider()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _ADVISOR_SYSTEM_PROMPT},
    ]

    if rag_context:
        messages.append({
            "role": "system",
            "content": f"Answer using the following context:\n\n{rag_context}",
        })

    messages.append({"role": "user", "content": user_message})

    response = await provider.chat(messages=messages)
    confidence = 0.7 if rag_context else 0.4

    result = AgentResult(
        agent=AgentType.ADVISOR,
        response=response.content,
        confidence=confidence,
        rag_chunks_used=rag_chunks_used,
    )
    return {"agent_results": [result], "rag_context": rag_context or ""}
