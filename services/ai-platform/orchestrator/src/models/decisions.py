"""Routing decisions and classification models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.models.state import AgentType


class RoutingDecision(BaseModel):
    """Router's decision on which agent(s) to invoke."""

    primary_agent: AgentType
    secondary_agents: list[AgentType] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""
    requires_compliance_check: bool = False

    @property
    def all_agents(self) -> list[AgentType]:
        """All agents to invoke, primary first."""
        return [self.primary_agent] + self.secondary_agents


class IntentClassification(BaseModel):
    """Structured intent extracted from user query."""

    intent: str = ""
    entities: dict[str, str] = Field(default_factory=dict)
    is_off_topic: bool = False
    is_harmful: bool = False
    needs_tool_access: bool = False
    needs_rag: bool = True
