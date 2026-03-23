import re

from src.datasets.loader import EvalTestCase, OrchestrateResponse
from src.evaluators.base import BaseEvaluator, EvalResult

# Patterns for specific claims that need grounding
DOLLAR_AMOUNT_PATTERN = re.compile(r"\$[\d,]+(?:\.\d{2})?")
DATE_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2}(?:,?\s*\d{4})?\b"
    r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b"
)
PERCENTAGE_PATTERN = re.compile(r"\b\d+(?:\.\d+)?%\b")
SPECIFIC_NUMBER_PATTERN = re.compile(r"\b\d{3,}\b")


class FaithfulnessEvaluator(BaseEvaluator):
    """Evaluates RAG faithfulness by checking if responses are grounded in retrieved context."""

    name: str = "faithfulness"

    async def evaluate(
        self, test_case: TestCase, response: OrchestrateResponse
    ) -> EvalResult:
        # Extract RAG context from metadata if available
        rag_context = response.metadata.get("rag_context", "")
        retrieved_chunks = response.metadata.get("retrieved_chunks", [])

        # Build the full context string
        if isinstance(retrieved_chunks, list) and retrieved_chunks:
            full_context = " ".join(str(c) for c in retrieved_chunks)
        elif rag_context:
            full_context = str(rag_context)
        else:
            # No RAG context available -- check for hallucinated specifics only
            return await self._evaluate_without_context(test_case, response)

        response_text = response.response

        # Check grounding of specific claims
        grounded, total, ungrounded_claims = self._check_claim_grounding(
            response_text, full_context
        )

        if total == 0:
            score = 1.0
            details = "No specific claims to verify"
        else:
            score = grounded / total
            details = (
                f"Grounded claims: {grounded}/{total}. "
                f"Ungrounded: {ungrounded_claims}" if ungrounded_claims
                else f"All {total} claims grounded in context"
            )

        passed = score >= 0.7

        return EvalResult(
            evaluator=self.name,
            test_case_id=test_case.id,
            passed=passed,
            score=round(score, 4),
            details=details,
            metadata={
                "grounded_claims": grounded,
                "total_claims": total,
                "ungrounded_claims": ungrounded_claims,
                "has_rag_context": True,
            },
        )

    async def _evaluate_without_context(
        self, test_case: TestCase, response: OrchestrateResponse
    ) -> EvalResult:
        """When no RAG context is available, penalize hallucinated specifics."""
        response_text = response.response
        hallucination_indicators: list[str] = []

        # Check for specific dollar amounts (potentially hallucinated)
        dollar_amounts = DOLLAR_AMOUNT_PATTERN.findall(response_text)
        if dollar_amounts:
            hallucination_indicators.append(f"Dollar amounts: {dollar_amounts}")

        # Check for specific dates
        dates = DATE_PATTERN.findall(response_text)
        if dates:
            hallucination_indicators.append(f"Specific dates: {dates}")

        # Check for specific percentages
        percentages = PERCENTAGE_PATTERN.findall(response_text)
        if percentages:
            hallucination_indicators.append(f"Percentages: {percentages}")

        if not hallucination_indicators:
            score = 1.0
            details = "No RAG context available; no hallucinated specifics detected"
        else:
            # Penalize based on number of unverifiable specifics
            penalty = min(len(hallucination_indicators) * 0.25, 1.0)
            score = max(0.0, 1.0 - penalty)
            details = (
                f"No RAG context available; potential hallucinations: "
                f"{'; '.join(hallucination_indicators)}"
            )

        passed = score >= 0.7

        return EvalResult(
            evaluator=self.name,
            test_case_id=test_case.id,
            passed=passed,
            score=round(score, 4),
            details=details,
            metadata={
                "hallucination_indicators": hallucination_indicators,
                "has_rag_context": False,
            },
        )

    def _check_claim_grounding(
        self, response_text: str, context: str
    ) -> tuple[int, int, list[str]]:
        """Check if specific claims in the response are grounded in context.

        Returns:
            Tuple of (grounded_count, total_count, list_of_ungrounded_claims)
        """
        context_lower = context.lower()
        ungrounded: list[str] = []
        total = 0
        grounded = 0

        # Check dollar amounts
        for amount in DOLLAR_AMOUNT_PATTERN.findall(response_text):
            total += 1
            if amount.lower() in context_lower:
                grounded += 1
            else:
                ungrounded.append(f"${amount}")

        # Check dates
        for date in DATE_PATTERN.findall(response_text):
            total += 1
            if date.lower() in context_lower:
                grounded += 1
            else:
                ungrounded.append(date)

        # Check percentages
        for pct in PERCENTAGE_PATTERN.findall(response_text):
            total += 1
            if pct in context_lower:
                grounded += 1
            else:
                ungrounded.append(pct)

        return grounded, total, ungrounded
