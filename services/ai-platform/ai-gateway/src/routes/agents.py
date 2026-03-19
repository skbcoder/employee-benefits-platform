"""Agent workflow endpoints."""

from fastapi import APIRouter

from src.models.agent import (
    AdvisorRequest,
    AdvisorResponse,
    ValidationRequest,
    ValidationResult,
)
from src.services.agent_loop import run_agent_loop, get_rag_context

router = APIRouter(prefix="/api/ai/agents", tags=["agents"])


@router.post("/validate", response_model=ValidationResult)
async def validate_enrollment(request: ValidationRequest):
    """Run the enrollment validation agent.

    Retrieves enrollment details, checks against knowledge base policies,
    and returns a validation verdict with reasoning.
    """
    # Get policy context from RAG
    rag_context = await get_rag_context(
        query=f"eligibility rules enrollment validation policy",
        category="policy",
    )

    validation_prompt = (
        f"Validate enrollment {request.enrollment_id}.\n\n"
        "Steps:\n"
        "1. Use check_enrollment_status to get the enrollment details.\n"
        "2. Review the benefit selections against the eligibility policies provided in context.\n"
        "3. Return your verdict as one of: APPROVED, NEEDS_REVIEW, or REJECTED.\n"
        "4. Provide clear reasoning for your decision.\n"
        "5. List any policy references that informed your decision.\n\n"
        "Format your response as:\n"
        "VERDICT: [APPROVED|NEEDS_REVIEW|REJECTED]\n"
        "REASONING: [Your reasoning]\n"
        "POLICIES: [Comma-separated policy references]"
    )

    response_text, _ = await run_agent_loop(
        messages=[],
        user_message=validation_prompt,
        rag_context=rag_context,
    )

    # Parse the structured response
    verdict, reasoning, policies = _parse_validation_response(response_text)

    return ValidationResult(
        enrollment_id=request.enrollment_id,
        verdict=verdict,
        reasoning=reasoning,
        policy_references=policies,
    )


@router.post("/advise", response_model=AdvisorResponse)
async def advise_benefits(request: AdvisorRequest):
    """Run the benefits advisor agent.

    Provides personalized benefit plan recommendations based on
    employee context and knowledge base information.
    """
    # Get plan details from RAG
    rag_context = await get_rag_context(
        query=f"benefit plan options coverage tiers {request.employee_context}",
        category="plan",
    )

    advisor_prompt = (
        "Provide personalized benefit plan recommendations.\n\n"
        f"Employee context: {request.employee_context or 'No specific context provided.'}\n"
    )

    if request.employee_id:
        advisor_prompt += (
            f"\nEmployee ID: {request.employee_id}\n"
            "Use get_enrollment_by_employee to check if they have existing enrollments.\n"
        )

    advisor_prompt += (
        "\nConsider:\n"
        "- Available benefit types: medical, dental, vision, life\n"
        "- Different plan tiers and their coverage levels\n"
        "- Cost vs. coverage tradeoffs\n"
        "- The employee's stated context and needs\n\n"
        "Provide clear, actionable recommendations with reasoning."
    )

    response_text, _ = await run_agent_loop(
        messages=[],
        user_message=advisor_prompt,
        rag_context=rag_context,
    )

    # Extract context sources
    context_sources = []
    if rag_context:
        for line in rag_context.split("\n"):
            if line.startswith("[") and line.endswith("]"):
                context_sources.append(line.strip("[]"))

    return AdvisorResponse(
        recommendations=response_text,
        context_used=context_sources,
    )


def _parse_validation_response(
    text: str,
) -> tuple[str, str, list[str]]:
    """Parse structured validation response from LLM."""
    from src.models.agent import AgentVerdict

    verdict = AgentVerdict.NEEDS_REVIEW  # Default to needs_review
    reasoning = text
    policies: list[str] = []

    for line in text.split("\n"):
        line_upper = line.strip().upper()
        if line_upper.startswith("VERDICT:"):
            raw = line.split(":", 1)[1].strip().upper()
            if "APPROVED" in raw:
                verdict = AgentVerdict.APPROVED
            elif "REJECTED" in raw:
                verdict = AgentVerdict.REJECTED
            else:
                verdict = AgentVerdict.NEEDS_REVIEW
        elif line.strip().upper().startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
        elif line.strip().upper().startswith("POLICIES:"):
            raw_policies = line.split(":", 1)[1].strip()
            policies = [p.strip() for p in raw_policies.split(",") if p.strip()]

    return verdict, reasoning, policies
