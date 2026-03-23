"""Orchestrator service — multi-agent LangGraph orchestration engine."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.settings import settings
from src.graph.workflow import orchestration_graph
from src.models.decisions import IntentClassification, RoutingDecision
from src.models.state import AgentResult, ComplianceDecision, TokenUsage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Orchestrator starting on :{settings.orchestrator_port}")
    logger.info(f"LLM provider: {settings.llm_provider}")
    yield
    logger.info("Orchestrator shutting down")


app = FastAPI(
    title="Benefits AI Orchestrator",
    description="Multi-agent LangGraph orchestration engine for employee benefits",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────


class OrchestrateRequest(BaseModel):
    """Request to run the orchestration graph."""

    message: str
    conversation_id: str = ""
    history: list[dict[str, Any]] = Field(default_factory=list)


class OrchestrateResponse(BaseModel):
    """Response from the orchestration graph."""

    response: str
    agent_used: str = ""
    tool_calls: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    escalated: bool = False
    compliance_risk: str = "low"
    token_usage: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int = 0


# ── Routes ────────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "orchestrator", "version": "2.0.0"}


@app.post("/api/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(request: OrchestrateRequest, req: Request):
    """Run the multi-agent orchestration graph."""
    start = time.monotonic()
    client_ip = req.client.host if req.client else "unknown"

    logger.info(
        f"Orchestrate: conversation={request.conversation_id}, "
        f"message='{request.message[:80]}'"
    )

    # Build initial state
    initial_state = {
        "user_message": request.message,
        "messages": request.history,
        "conversation_id": request.conversation_id,
        "client_ip": client_ip,
        "intent": IntentClassification(),
        "routing": RoutingDecision(primary_agent="advisor"),
        "agent_results": [],
        "rag_context": "",
        "compliance": ComplianceDecision(),
        "final_response": "",
        "escalated": False,
        "token_usage": TokenUsage(),
        "error": "",
    }

    try:
        # Invoke the LangGraph
        result = await orchestration_graph.ainvoke(initial_state)

        # Extract results
        agent_results: list[AgentResult] = result.get("agent_results", [])
        primary_agent = agent_results[0].agent.value if agent_results else "unknown"
        tool_calls = []
        for ar in agent_results:
            tool_calls.extend(tc.tool_name for tc in ar.tool_calls)

        confidence = agent_results[0].confidence if agent_results else 0.0
        compliance = result.get("compliance", ComplianceDecision())

        latency = int((time.monotonic() - start) * 1000)

        return OrchestrateResponse(
            response=result.get("final_response", ""),
            agent_used=primary_agent,
            tool_calls=tool_calls,
            confidence=confidence,
            escalated=result.get("escalated", False),
            compliance_risk=compliance.risk_level.value if compliance else "low",
            latency_ms=latency,
        )

    except Exception as e:
        logger.error(f"Orchestration failed: {e}", exc_info=True)
        latency = int((time.monotonic() - start) * 1000)
        return OrchestrateResponse(
            response=(
                "I apologize, but I'm having trouble processing your request. "
                "Please try again or contact your benefits administrator."
            ),
            agent_used="error",
            escalated=True,
            latency_ms=latency,
        )


@app.get("/api/orchestrate/graph")
async def get_graph_info():
    """Return information about the orchestration graph topology."""
    return {
        "nodes": ["router", "enrollment", "advisor", "compliance", "synthesis", "escalation"],
        "entry_point": "router",
        "edges": {
            "router": ["enrollment", "advisor", "compliance", "escalation"],
            "enrollment": ["compliance", "synthesis"],
            "advisor": ["synthesis"],
            "compliance": ["escalation", "synthesis"],
            "synthesis": ["END"],
            "escalation": ["END"],
        },
        "agents": {
            "router": "Intent classification and routing",
            "enrollment": "Enrollment CRUD via MCP tools",
            "advisor": "Benefits Q&A via RAG",
            "compliance": "Policy compliance checks",
            "synthesis": "Response merging and output sanitization",
            "escalation": "Human-in-the-loop escalation",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.orchestrator_host, port=settings.orchestrator_port)
