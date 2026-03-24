import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from src.runners.sequential import EvalRun


def _get_git_sha() -> str:
    """Get the current git SHA, or 'unknown' if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def write_json_report(run: EvalRun, output_path: str | Path | None = None) -> Path:
    """Write an evaluation run to a JSON report file.

    Args:
        run: The completed evaluation run.
        output_path: Optional output file path. Defaults to reports/eval_{run_id}.json.

    Returns:
        Path to the written report file.
    """
    if output_path is None:
        reports_dir = Path(__file__).resolve().parent.parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        output_path = reports_dir / f"eval_{run.run_id}.json"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "run_id": run.run_id,
        "timestamp": run.timestamp,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": _get_git_sha(),
        "dataset": run.dataset,
        "target_url": run.target_url,
        "duration_seconds": run.duration_seconds,
        "evaluators_used": run.evaluators_used,
        "summary": {
            "total_cases": run.total_cases,
            "total_evaluations": len(run.results),
            "passed": run.passed,
            "failed": run.failed,
            "pass_rate": round(run.pass_rate, 4),
            "avg_score": round(run.avg_score, 4),
            "scores_by_evaluator": {
                k: round(v, 4) for k, v in run.scores_by_evaluator().items()
            },
            "pass_rate_by_evaluator": {
                k: round(v, 4) for k, v in run.pass_rate_by_evaluator().items()
            },
        },
        "results": [r.model_dump() for r in run.results],
        "metadata": run.metadata,
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    return output_path
