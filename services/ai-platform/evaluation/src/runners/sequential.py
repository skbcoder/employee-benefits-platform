import time
import uuid
from datetime import datetime, timezone

import httpx
from pydantic import BaseModel, Field

from config.settings import settings
from src.datasets.loader import EvalTestCase, OrchestrateResponse
from src.evaluators.base import BaseEvaluator, EvalResult


class EvalRun(BaseModel):
    """Complete evaluation run result."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    dataset: str = ""
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    results: list[EvalResult] = Field(default_factory=list)
    duration_seconds: float = 0.0
    evaluators_used: list[str] = Field(default_factory=list)
    target_url: str = ""
    metadata: dict = Field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_cases if self.total_cases > 0 else 0.0

    @property
    def avg_score(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)

    def scores_by_evaluator(self) -> dict[str, float]:
        """Average score per evaluator."""
        evaluator_scores: dict[str, list[float]] = {}
        for r in self.results:
            evaluator_scores.setdefault(r.evaluator, []).append(r.score)
        return {
            name: sum(scores) / len(scores)
            for name, scores in evaluator_scores.items()
        }

    def pass_rate_by_evaluator(self) -> dict[str, float]:
        """Pass rate per evaluator."""
        evaluator_results: dict[str, list[bool]] = {}
        for r in self.results:
            evaluator_results.setdefault(r.evaluator, []).append(r.passed)
        return {
            name: sum(results) / len(results)
            for name, results in evaluator_results.items()
        }


async def call_orchestrator(
    test_case: TestCase, target_url: str, timeout: int
) -> OrchestrateResponse:
    """Send a test case to the orchestrator and return the parsed response."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            start = time.monotonic()
            resp = await client.post(
                f"{target_url}/api/orchestrate",
                json={
                    "message": test_case.input,
                    "conversation_id": "",
                    "history": [],
                },
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            resp.raise_for_status()
            data = resp.json()
            data["latency_ms"] = elapsed_ms
            return OrchestrateResponse(**data)
        except httpx.HTTPError as e:
            return OrchestrateResponse(
                response=f"ERROR: {e}",
                agent_used="error",
                latency_ms=0.0,
                metadata={"error": str(e)},
            )


async def run_sequential(
    test_cases: list[TestCase],
    evaluators: list[BaseEvaluator],
    target_url: str = "",
    dataset_name: str = "",
) -> EvalRun:
    """Run test cases sequentially against the orchestrator.

    Args:
        test_cases: List of test cases to evaluate.
        evaluators: List of evaluators to apply to each response.
        target_url: Orchestrator URL (defaults to settings).
        dataset_name: Name of the dataset being evaluated.

    Returns:
        Complete EvalRun with all results.
    """
    url = target_url or settings.orchestrator_url
    timeout = settings.eval_timeout_seconds

    run = EvalRun(
        dataset=dataset_name,
        total_cases=len(test_cases),
        evaluators_used=[e.name for e in evaluators],
        target_url=url,
    )

    start_time = time.monotonic()
    all_results: list[EvalResult] = []

    for test_case in test_cases:
        response = await call_orchestrator(test_case, url, timeout)

        for evaluator in evaluators:
            result = await evaluator.evaluate(test_case, response)
            all_results.append(result)

    run.duration_seconds = round(time.monotonic() - start_time, 2)
    run.results = all_results
    run.passed = sum(1 for r in all_results if r.passed)
    run.failed = sum(1 for r in all_results if not r.passed)

    return run
