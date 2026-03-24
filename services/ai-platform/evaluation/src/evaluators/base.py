from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from src.datasets.loader import EvalTestCase, OrchestrateResponse


class EvalResult(BaseModel):
    """Result of a single evaluator run against a single test case."""

    evaluator: str
    test_case_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0, description="Score from 0.0 to 1.0")
    details: str = ""
    metadata: dict = Field(default_factory=dict)


class BaseEvaluator(ABC):
    """Abstract base class for all evaluators."""

    name: str = "base"

    @abstractmethod
    async def evaluate(
        self, test_case: TestCase, response: OrchestrateResponse
    ) -> EvalResult:
        """Evaluate a single test case against the orchestrator response.

        Args:
            test_case: The test case definition with expected values.
            response: The actual response from the orchestrator.

        Returns:
            An EvalResult with the evaluation outcome.
        """
        ...
