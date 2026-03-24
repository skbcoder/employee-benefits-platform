from pydantic import BaseModel, Field

from src.datasets.loader import EvalTestCase
from src.evaluators.base import BaseEvaluator
from src.runners.parallel import run_parallel
from src.runners.sequential import EvalRun


class ABTestResult(BaseModel):
    """Result of an A/B comparison between two configurations."""

    config_a_name: str
    config_b_name: str
    run_a: EvalRun
    run_b: EvalRun
    winner: str = ""
    per_evaluator_comparison: dict[str, dict] = Field(default_factory=dict)
    summary: str = ""

    def model_post_init(self, __context: object) -> None:
        self._compute_comparison()

    def _compute_comparison(self) -> None:
        scores_a = self.run_a.scores_by_evaluator()
        scores_b = self.run_b.scores_by_evaluator()

        all_evaluators = set(scores_a.keys()) | set(scores_b.keys())

        a_wins = 0
        b_wins = 0
        ties = 0

        for evaluator in all_evaluators:
            sa = scores_a.get(evaluator, 0.0)
            sb = scores_b.get(evaluator, 0.0)
            diff = sa - sb

            if abs(diff) < 0.01:
                verdict = "tie"
                ties += 1
            elif diff > 0:
                verdict = self.config_a_name
                a_wins += 1
            else:
                verdict = self.config_b_name
                b_wins += 1

            self.per_evaluator_comparison[evaluator] = {
                "score_a": round(sa, 4),
                "score_b": round(sb, 4),
                "diff": round(diff, 4),
                "winner": verdict,
            }

        if a_wins > b_wins:
            self.winner = self.config_a_name
        elif b_wins > a_wins:
            self.winner = self.config_b_name
        else:
            self.winner = "tie"

        self.summary = (
            f"{self.config_a_name} avg: {self.run_a.avg_score:.4f}, "
            f"{self.config_b_name} avg: {self.run_b.avg_score:.4f}. "
            f"Winner: {self.winner} "
            f"({a_wins} wins / {b_wins} losses / {ties} ties across evaluators)"
        )


async def run_ab_test(
    test_cases: list[TestCase],
    evaluators: list[BaseEvaluator],
    config_a: dict,
    config_b: dict,
) -> ABTestResult:
    """Run an A/B test comparing two orchestrator configurations.

    Args:
        test_cases: Test cases to evaluate against both configurations.
        evaluators: Evaluators to apply.
        config_a: Dict with 'name' and 'target_url' for configuration A.
        config_b: Dict with 'name' and 'target_url' for configuration B.

    Returns:
        ABTestResult with per-evaluator comparison and overall winner.
    """
    name_a = config_a.get("name", "config_a")
    name_b = config_b.get("name", "config_b")
    url_a = config_a.get("target_url", "")
    url_b = config_b.get("target_url", "")

    run_a = await run_parallel(
        test_cases=test_cases,
        evaluators=evaluators,
        target_url=url_a,
        dataset_name=f"ab_test_{name_a}",
    )

    run_b = await run_parallel(
        test_cases=test_cases,
        evaluators=evaluators,
        target_url=url_b,
        dataset_name=f"ab_test_{name_b}",
    )

    return ABTestResult(
        config_a_name=name_a,
        config_b_name=name_b,
        run_a=run_a,
        run_b=run_b,
    )
