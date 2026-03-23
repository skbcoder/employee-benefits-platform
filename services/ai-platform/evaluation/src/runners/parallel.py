import asyncio
import time

from config.settings import settings
from src.datasets.loader import EvalTestCase
from src.evaluators.base import BaseEvaluator, EvalResult
from src.runners.sequential import EvalRun, call_orchestrator


async def _evaluate_single(
    test_case: TestCase,
    evaluators: list[BaseEvaluator],
    target_url: str,
    timeout: int,
    semaphore: asyncio.Semaphore,
) -> list[EvalResult]:
    """Evaluate a single test case under a concurrency semaphore."""
    async with semaphore:
        response = await call_orchestrator(test_case, target_url, timeout)
        results = []
        for evaluator in evaluators:
            result = await evaluator.evaluate(test_case, response)
            results.append(result)
        return results


async def run_parallel(
    test_cases: list[TestCase],
    evaluators: list[BaseEvaluator],
    target_url: str = "",
    dataset_name: str = "",
    max_workers: int = 0,
) -> EvalRun:
    """Run test cases in parallel against the orchestrator.

    Uses asyncio.Semaphore to limit concurrency to max_workers.

    Args:
        test_cases: List of test cases to evaluate.
        evaluators: List of evaluators to apply to each response.
        target_url: Orchestrator URL (defaults to settings).
        dataset_name: Name of the dataset being evaluated.
        max_workers: Max concurrent requests (defaults to settings.parallel_workers).

    Returns:
        Complete EvalRun with all results.
    """
    url = target_url or settings.orchestrator_url
    timeout = settings.eval_timeout_seconds
    workers = max_workers or settings.parallel_workers

    semaphore = asyncio.Semaphore(workers)

    run = EvalRun(
        dataset=dataset_name,
        total_cases=len(test_cases),
        evaluators_used=[e.name for e in evaluators],
        target_url=url,
    )

    start_time = time.monotonic()

    tasks = [
        _evaluate_single(tc, evaluators, url, timeout, semaphore)
        for tc in test_cases
    ]
    nested_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_results: list[EvalResult] = []
    for result_or_error in nested_results:
        if isinstance(result_or_error, Exception):
            # Create a failure result for each evaluator
            for evaluator in evaluators:
                all_results.append(
                    EvalResult(
                        evaluator=evaluator.name,
                        test_case_id="unknown",
                        passed=False,
                        score=0.0,
                        details=f"Exception during evaluation: {result_or_error}",
                    )
                )
        else:
            all_results.extend(result_or_error)

    run.duration_seconds = round(time.monotonic() - start_time, 2)
    run.results = all_results
    run.passed = sum(1 for r in all_results if r.passed)
    run.failed = sum(1 for r in all_results if not r.passed)

    return run
