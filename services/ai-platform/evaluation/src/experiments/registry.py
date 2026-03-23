from pydantic import BaseModel, Field

from config.settings import settings


class Experiment(BaseModel):
    """A named experiment definition."""

    name: str
    description: str
    dataset: str = Field(description="Filename of the YAML dataset (relative to datasets/)")
    evaluators: list[str] = Field(description="Evaluator names to use")
    target_url: str = ""

    def get_target_url(self) -> str:
        return self.target_url or settings.orchestrator_url


EXPERIMENTS: dict[str, Experiment] = {
    "enrollment_accuracy": Experiment(
        name="enrollment_accuracy",
        description="Test routing accuracy for enrollment operations",
        dataset="enrollment_queries.yaml",
        evaluators=["accuracy", "latency", "cost"],
    ),
    "knowledge_quality": Experiment(
        name="knowledge_quality",
        description="Test quality and faithfulness of policy knowledge responses",
        dataset="policy_questions.yaml",
        evaluators=["accuracy", "relevance", "faithfulness", "latency", "cost"],
    ),
    "security_audit": Experiment(
        name="security_audit",
        description="Test guardrails against adversarial inputs",
        dataset="adversarial.yaml",
        evaluators=["safety", "accuracy", "latency"],
    ),
    "full_suite": Experiment(
        name="full_suite",
        description="Run all evaluators across all datasets",
        dataset="all",
        evaluators=["accuracy", "relevance", "safety", "latency", "cost", "faithfulness"],
    ),
}


def get_experiment(name: str) -> Experiment:
    """Retrieve an experiment by name.

    Args:
        name: The experiment name.

    Returns:
        The Experiment definition.

    Raises:
        KeyError: If the experiment name is not found.
    """
    if name not in EXPERIMENTS:
        available = ", ".join(sorted(EXPERIMENTS.keys()))
        raise KeyError(f"Experiment '{name}' not found. Available: {available}")
    return EXPERIMENTS[name]


def list_experiments() -> list[Experiment]:
    """List all registered experiments."""
    return list(EXPERIMENTS.values())
