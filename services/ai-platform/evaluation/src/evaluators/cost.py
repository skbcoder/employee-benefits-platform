from src.datasets.loader import EvalTestCase, OrchestrateResponse
from src.evaluators.base import BaseEvaluator, EvalResult

# Default cost budget per query in USD
DEFAULT_COST_BUDGET_USD = 0.05

# Approximate token costs (USD per 1K tokens)
INPUT_COST_PER_1K = 0.003
OUTPUT_COST_PER_1K = 0.015


class CostEvaluator(BaseEvaluator):
    """Evaluates cost efficiency of orchestrator responses based on token usage."""

    name: str = "cost"

    def __init__(self, cost_budget_usd: float = DEFAULT_COST_BUDGET_USD):
        self._cost_budget = cost_budget_usd

    async def evaluate(
        self, test_case: TestCase, response: OrchestrateResponse
    ) -> EvalResult:
        metadata = response.metadata

        # Extract token counts from metadata if available
        input_tokens = metadata.get("input_tokens", 0)
        output_tokens = metadata.get("output_tokens", 0)
        total_tokens = metadata.get("total_tokens", input_tokens + output_tokens)

        # If no token data is available, estimate from response length
        if total_tokens == 0 and response.response:
            estimated_output_tokens = len(response.response.split()) * 1.3
            estimated_input_tokens = estimated_output_tokens * 0.5
            input_tokens = int(estimated_input_tokens)
            output_tokens = int(estimated_output_tokens)
            total_tokens = input_tokens + output_tokens
            estimation_method = "estimated_from_response"
        elif total_tokens > 0:
            estimation_method = "from_metadata"
        else:
            estimation_method = "no_data"

        # Calculate cost estimate
        cost_usd = (
            (input_tokens / 1000.0) * INPUT_COST_PER_1K
            + (output_tokens / 1000.0) * OUTPUT_COST_PER_1K
        )

        # Score: 1.0 if under budget, linear decay up to 2x budget, 0.0 beyond
        if cost_usd <= 0:
            score = 1.0
        elif cost_usd <= self._cost_budget:
            score = 1.0
        elif cost_usd >= self._cost_budget * 2:
            score = 0.0
        else:
            score = 1.0 - ((cost_usd - self._cost_budget) / self._cost_budget)

        passed = cost_usd <= self._cost_budget

        return EvalResult(
            evaluator=self.name,
            test_case_id=test_case.id,
            passed=passed,
            score=round(score, 4),
            details=(
                f"Estimated cost: ${cost_usd:.4f} "
                f"(budget: ${self._cost_budget:.4f}, "
                f"tokens: {total_tokens}, method: {estimation_method})"
            ),
            metadata={
                "cost_usd": round(cost_usd, 6),
                "budget_usd": self._cost_budget,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "estimation_method": estimation_method,
            },
        )
