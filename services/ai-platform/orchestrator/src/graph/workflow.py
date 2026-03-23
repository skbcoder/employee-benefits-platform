"""LangGraph workflow — compiles the multi-agent orchestration graph."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from src.graph.state import AgentState
from src.graph.router_node import router_node
from src.graph.enrollment_node import enrollment_node
from src.graph.advisor_node import advisor_node
from src.graph.compliance_node import compliance_node
from src.graph.synthesis_node import synthesis_node
from src.graph.escalation_node import escalation_node
from src.models.state import AgentType

logger = logging.getLogger(__name__)


def _route_after_router(state: AgentState) -> str:
    """Conditional edge: decide which agent node to invoke after routing."""
    routing = state.get("routing")
    if not routing:
        return "advisor"

    agent_map = {
        AgentType.ENROLLMENT: "enrollment",
        AgentType.ADVISOR: "advisor",
        AgentType.COMPLIANCE: "compliance",
        AgentType.ESCALATION: "escalation",
    }
    return agent_map.get(routing.primary_agent, "advisor")


def _route_after_agent(state: AgentState) -> str:
    """Conditional edge: decide whether to run compliance check after agent."""
    routing = state.get("routing")

    # If routing says compliance check is needed, go to compliance
    if routing and routing.requires_compliance_check:
        return "compliance"

    # Otherwise go directly to synthesis
    return "synthesis"


def _route_after_compliance(state: AgentState) -> str:
    """Conditional edge: after compliance, go to escalation or synthesis."""
    compliance = state.get("compliance")

    if compliance and compliance.requires_human_approval:
        return "escalation"

    return "synthesis"


def build_graph() -> StateGraph:
    """Build and compile the multi-agent orchestration graph.

    Graph topology:
        router → [enrollment | advisor | compliance | escalation]
                      ↓
                 compliance (if required)
                      ↓
              [synthesis | escalation]
                      ↓
                     END
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("enrollment", enrollment_node)
    graph.add_node("advisor", advisor_node)
    graph.add_node("compliance", compliance_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("escalation", escalation_node)

    # Entry point
    graph.set_entry_point("router")

    # Router → specialist agent (conditional)
    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "enrollment": "enrollment",
            "advisor": "advisor",
            "compliance": "compliance",
            "escalation": "escalation",
        },
    )

    # Specialist agent → compliance check or synthesis (conditional)
    graph.add_conditional_edges(
        "enrollment",
        _route_after_agent,
        {
            "compliance": "compliance",
            "synthesis": "synthesis",
        },
    )

    # Advisor → synthesis (always — no compliance needed for read-only)
    graph.add_edge("advisor", "synthesis")

    # Compliance → escalation or synthesis (conditional)
    graph.add_conditional_edges(
        "compliance",
        _route_after_compliance,
        {
            "escalation": "escalation",
            "synthesis": "synthesis",
        },
    )

    # Terminal nodes
    graph.add_edge("synthesis", END)
    graph.add_edge("escalation", END)

    return graph


# Compiled graph — ready to invoke
orchestration_graph = build_graph().compile()
