from src.datasets.loader import EvalTestCase, OrchestrateResponse
from src.evaluators.base import BaseEvaluator, EvalResult

# Default thresholds in milliseconds
TOOL_CALL_THRESHOLD_MS = 5000.0
KNOWLEDGE_THRESHOLD_MS = 3000.0


class LatencyEvaluator(BaseEvaluator):
    """Evaluates response latency against configurable thresholds."""

    name: str = "latency"

    def __init__(
        self,
        tool_call_threshold_ms: float = TOOL_CALL_THRESHOLD_MS,
        knowledge_threshold_ms: float = KNOWLEDGE_THRESHOLD_MS,
    ):
        self._tool_call_threshold = tool_call_threshold_ms
        self._knowledge_threshold = knowledge_threshold_ms

    async def evaluate(
        self, test_case: TestCase, response: OrchestrateResponse
    ) -> EvalResult:
        latency_ms = response.latency_ms

        # Select threshold based on whether tool calls were expected
        has_tools = (
            test_case.expected_tools is not None and len(test_case.expected_tools) > 0
        )
        threshold = self._tool_call_threshold if has_tools else self._knowledge_threshold

        # Score scales linearly: 1.0 at 0ms, 0.0 at 2x threshold
        max_latency = threshold * 2.0
        if latency_ms <= 0:
            score = 1.0
        elif latency_ms >= max_latency:
            score = 0.0
        else:
            score = 1.0 - (latency_ms / max_latency)

        passed = latency_ms <= threshold

        return EvalResult(
            evaluator=self.name,
            test_case_id=test_case.id,
            passed=passed,
            score=round(score, 4),
            details=(
                f"Latency: {latency_ms:.0f}ms "
                f"(threshold: {threshold:.0f}ms, "
                f"type: {'tool_call' if has_tools else 'knowledge'})"
            ),
            metadata={
                "latency_ms": latency_ms,
                "threshold_ms": threshold,
                "has_tools": has_tools,
            },
        )
