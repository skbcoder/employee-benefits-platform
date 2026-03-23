"""LangGraph AgentState — the typed state that flows through the graph."""

from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph import add_messages
from typing_extensions import TypedDict

from src.models.decisions import IntentClassification, RoutingDecision
from src.models.state import AgentResult, ComplianceDecision, TokenUsage


def _merge_results(
    existing: list[AgentResult], new: list[AgentResult]
) -> list[AgentResult]:
    """Merge agent results — append new results to existing."""
    return existing + new


class AgentState(TypedDict):
    """State flowing through the multi-agent orchestration graph.

    Each node reads what it needs and writes its outputs. LangGraph handles
    state immutability and checkpointing automatically.
    """

    # ── Input ─────────────────────────────────────────────────────────
    # The raw user message that triggered this graph run
    user_message: str

    # Conversation history (LangGraph message format)
    messages: Annotated[list[dict[str, Any]], add_messages]

    # Session / conversation ID for tracking
    conversation_id: str

    # Client IP for rate limiting and audit
    client_ip: str

    # ── Router outputs ────────────────────────────────────────────────
    # Intent classification from the router
    intent: IntentClassification

    # Routing decision — which agent(s) to invoke
    routing: RoutingDecision

    # ── Agent outputs ─────────────────────────────────────────────────
    # Results from each specialist agent that ran
    agent_results: Annotated[list[AgentResult], _merge_results]

    # RAG context retrieved for the query
    rag_context: str

    # ── Compliance ────────────────────────────────────────────────────
    # Compliance check result (pre-action and post-response)
    compliance: ComplianceDecision

    # ── Synthesis ─────────────────────────────────────────────────────
    # Final merged response after synthesis
    final_response: str

    # Whether the request was escalated to a human
    escalated: bool

    # ── Observability ─────────────────────────────────────────────────
    # Token usage tracking for cost management
    token_usage: TokenUsage

    # Error message if the graph encountered a fatal error
    error: str
