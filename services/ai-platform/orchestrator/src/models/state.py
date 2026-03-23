"""Typed state models for the LangGraph agent orchestration graph."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Specialist agent types the router can delegate to."""

    ENROLLMENT = "enrollment"
    ADVISOR = "advisor"
    COMPLIANCE = "compliance"
    ESCALATION = "escalation"


class RiskLevel(str, Enum):
    """Risk classification for agent actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolCall(BaseModel):
    """Record of a single tool invocation."""

    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    result: str = ""
    success: bool = True


class AgentResult(BaseModel):
    """Output produced by a specialist agent node."""

    agent: AgentType
    response: str = ""
    confidence: float = 0.0
    tool_calls: list[ToolCall] = Field(default_factory=list)
    rag_chunks_used: int = 0
    error: str | None = None


class ComplianceDecision(BaseModel):
    """Result of a compliance check on an agent action."""

    approved: bool = True
    risk_level: RiskLevel = RiskLevel.LOW
    violations: list[str] = Field(default_factory=list)
    requires_human_approval: bool = False
    explanation: str = ""


class TokenUsage(BaseModel):
    """Track token consumption per request for cost management."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    estimated_cost_usd: float = 0.0

    def add(self, prompt: int, completion: int, model: str = "") -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += prompt + completion
        if model:
            self.model = model
