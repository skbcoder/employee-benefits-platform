from src.datasets.loader import EvalTestCase, OrchestrateResponse
from src.evaluators.base import BaseEvaluator, EvalResult


class AccuracyEvaluator(BaseEvaluator):
    """Evaluates whether the orchestrator routed to the correct agent and called expected tools."""

    name: str = "accuracy"

    async def evaluate(
        self, test_case: TestCase, response: OrchestrateResponse
    ) -> EvalResult:
        agent_match = (
            response.agent_used.lower().strip()
            == test_case.expected_agent.lower().strip()
        )

        # Tool matching: if expected_tools is None, skip tool check
        if test_case.expected_tools is None:
            tools_match = True
            tool_detail = "Tool check skipped (no expected tools specified)"
        else:
            expected_set = set(t.lower().strip() for t in test_case.expected_tools)
            actual_set = set(t.lower().strip() for t in response.tool_calls)
            tools_match = expected_set == actual_set
            tool_detail = (
                f"Expected tools: {sorted(expected_set)}, "
                f"Actual tools: {sorted(actual_set)}"
            )

        # Scoring
        if agent_match and tools_match:
            score = 1.0
            passed = True
            summary = "Agent and tools matched"
        elif agent_match and not tools_match:
            score = 0.5
            passed = False
            summary = "Agent matched but tools differed"
        else:
            score = 0.0
            passed = False
            summary = "Agent did not match"

        details = (
            f"{summary}. "
            f"Expected agent: {test_case.expected_agent}, "
            f"Actual agent: {response.agent_used}. "
            f"{tool_detail}"
        )

        return EvalResult(
            evaluator=self.name,
            test_case_id=test_case.id,
            passed=passed,
            score=score,
            details=details,
            metadata={
                "agent_match": agent_match,
                "tools_match": tools_match,
                "expected_agent": test_case.expected_agent,
                "actual_agent": response.agent_used,
            },
        )
