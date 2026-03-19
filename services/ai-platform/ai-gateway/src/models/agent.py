"""Agent workflow models."""

from enum import Enum

from pydantic import BaseModel, Field


class AgentVerdict(str, Enum):
    APPROVED = "APPROVED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REJECTED = "REJECTED"


class ValidationRequest(BaseModel):
    enrollment_id: str = Field(..., description="Enrollment ID to validate")


class ValidationResult(BaseModel):
    enrollment_id: str
    verdict: AgentVerdict
    reasoning: str
    policy_references: list[str] = Field(default_factory=list)


class AdvisorRequest(BaseModel):
    employee_id: str | None = Field(None, description="Employee ID for context")
    employee_context: str = Field("", description="Free-text employee context")


class AdvisorResponse(BaseModel):
    recommendations: str
    context_used: list[str] = Field(default_factory=list)
