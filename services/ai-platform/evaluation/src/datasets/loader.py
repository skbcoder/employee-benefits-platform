from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class EvalTestCase(BaseModel):
    """A single evaluation test case."""

    id: str
    input: str = Field(description="User message to send to the orchestrator")
    expected_agent: str = Field(description="Which agent should handle this query")
    expected_tools: Optional[list[str]] = Field(
        default=None, description="Expected tool calls (optional)"
    )
    expected_behavior: str = Field(
        description="Human-readable description of expected behavior"
    )
    tags: list[str] = Field(default_factory=list)
    expected_blocked: bool = Field(
        default=False, description="Whether the request should be blocked (safety tests)"
    )


class OrchestrateResponse(BaseModel):
    """Response from the orchestrator service."""

    response: str = ""
    agent_used: str = ""
    tool_calls: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    escalated: bool = False
    compliance_risk: str = "low"
    latency_ms: float = 0.0
    metadata: dict = Field(default_factory=dict)


def load_test_cases(yaml_path: str | Path) -> list[EvalTestCase]:
    """Load test cases from a YAML file.

    Args:
        yaml_path: Path to the YAML file containing test cases.

    Returns:
        List of TestCase instances parsed from the YAML.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        ValueError: If the YAML content is not a valid list of test cases.
    """
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, list):
        raise ValueError(
            f"Expected a YAML list of test cases in {path}, got {type(raw).__name__}"
        )

    test_cases = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ValueError(f"Test case at index {i} is not a mapping: {entry}")
        test_cases.append(EvalTestCase(**entry))

    return test_cases


def load_all_datasets(dataset_dir: str | Path) -> dict[str, list[EvalTestCase]]:
    """Load all YAML datasets from a directory.

    Args:
        dataset_dir: Directory containing YAML dataset files.

    Returns:
        Dictionary mapping filename (without extension) to list of TestCase.
    """
    dir_path = Path(dataset_dir)
    if not dir_path.is_dir():
        raise FileNotFoundError(f"Dataset directory not found: {dir_path}")

    datasets: dict[str, list[EvalTestCase]] = {}
    for yaml_file in sorted(dir_path.glob("*.yaml")):
        name = yaml_file.stem
        datasets[name] = load_test_cases(yaml_file)

    return datasets
