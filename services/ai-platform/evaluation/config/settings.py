from pathlib import Path

from pydantic_settings import BaseSettings


class EvalSettings(BaseSettings):
    """Configuration for the evaluation framework."""

    orchestrator_url: str = "http://localhost:8400"
    ai_gateway_url: str = "http://localhost:8200"
    eval_timeout_seconds: int = 30
    eval_port: int = 8600
    parallel_workers: int = 4
    default_dataset_dir: str = str(
        Path(__file__).resolve().parent.parent / "datasets"
    )

    model_config = {
        "env_prefix": "EVAL_",
        "env_file": ".env",
        "extra": "ignore",
    }


settings = EvalSettings()
