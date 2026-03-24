import argparse
import asyncio
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config.settings import settings
from src.datasets.loader import load_all_datasets, load_test_cases
from src.evaluators.accuracy import AccuracyEvaluator
from src.evaluators.base import BaseEvaluator
from src.evaluators.cost import CostEvaluator
from src.evaluators.faithfulness import FaithfulnessEvaluator
from src.evaluators.latency import LatencyEvaluator
from src.evaluators.relevance import RelevanceEvaluator
from src.evaluators.safety import SafetyEvaluator
from src.experiments.registry import EXPERIMENTS, get_experiment, list_experiments
from src.reporters.console import print_eval_report
from src.reporters.html_report import write_html_report
from src.reporters.json_report import write_json_report
from src.runners.parallel import run_parallel
from src.runners.sequential import EvalRun, run_sequential

app = FastAPI(
    title="AI Platform Evaluation Service",
    description="Evaluation framework for the multi-agent AI system",
    version="1.0.0",
)

# In-memory store of eval results
_eval_results: dict[str, EvalRun] = {}

# Evaluator registry
EVALUATOR_REGISTRY: dict[str, type[BaseEvaluator]] = {
    "accuracy": AccuracyEvaluator,
    "relevance": RelevanceEvaluator,
    "safety": SafetyEvaluator,
    "latency": LatencyEvaluator,
    "cost": CostEvaluator,
    "faithfulness": FaithfulnessEvaluator,
}


def build_evaluators(names: list[str]) -> list[BaseEvaluator]:
    """Instantiate evaluators by name."""
    evaluators = []
    for name in names:
        cls = EVALUATOR_REGISTRY.get(name)
        if cls is None:
            raise ValueError(
                f"Unknown evaluator: {name}. Available: {list(EVALUATOR_REGISTRY.keys())}"
            )
        evaluators.append(cls())
    return evaluators


# --- API Models ---

class EvalRunRequest(BaseModel):
    dataset: str = Field(
        default="",
        description="Dataset filename (e.g. 'enrollment_queries.yaml') or experiment name",
    )
    experiment: str = Field(
        default="",
        description="Named experiment to run (overrides dataset if set)",
    )
    evaluators: list[str] = Field(
        default_factory=list,
        description="Evaluator names to use (ignored if experiment is set)",
    )
    parallel: bool = Field(default=True, description="Run in parallel mode")
    target_url: str = Field(default="", description="Override orchestrator URL")


class EvalRunResponse(BaseModel):
    run_id: str
    dataset: str
    total_cases: int
    passed: int
    failed: int
    pass_rate: float
    avg_score: float
    duration_seconds: float
    scores_by_evaluator: dict[str, float]


class ExperimentInfo(BaseModel):
    name: str
    description: str
    dataset: str
    evaluators: list[str]


# --- Endpoints ---

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "evaluation", "port": settings.eval_port}


@app.post("/api/eval/run", response_model=EvalRunResponse)
async def trigger_eval_run(request: EvalRunRequest):
    """Trigger an evaluation run."""
    dataset_dir = Path(settings.default_dataset_dir)

    try:
        if request.experiment:
            exp = get_experiment(request.experiment)
            evaluator_names = exp.evaluators
            target_url = request.target_url or exp.get_target_url()

            if exp.dataset == "all":
                # Load all datasets
                all_datasets = load_all_datasets(dataset_dir)
                test_cases = []
                for cases in all_datasets.values():
                    test_cases.extend(cases)
                dataset_name = "all"
            else:
                dataset_path = dataset_dir / exp.dataset
                test_cases = load_test_cases(dataset_path)
                dataset_name = exp.dataset
        elif request.dataset:
            dataset_path = dataset_dir / request.dataset
            test_cases = load_test_cases(dataset_path)
            dataset_name = request.dataset
            evaluator_names = request.evaluators or list(EVALUATOR_REGISTRY.keys())
            target_url = request.target_url or settings.orchestrator_url
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'dataset' or 'experiment' must be provided",
            )

        evaluators = build_evaluators(evaluator_names)

        if request.parallel:
            run = await run_parallel(
                test_cases=test_cases,
                evaluators=evaluators,
                target_url=target_url,
                dataset_name=dataset_name,
            )
        else:
            run = await run_sequential(
                test_cases=test_cases,
                evaluators=evaluators,
                target_url=target_url,
                dataset_name=dataset_name,
            )

        _eval_results[run.run_id] = run

        return EvalRunResponse(
            run_id=run.run_id,
            dataset=run.dataset,
            total_cases=run.total_cases,
            passed=run.passed,
            failed=run.failed,
            pass_rate=round(run.pass_rate, 4),
            avg_score=round(run.avg_score, 4),
            duration_seconds=run.duration_seconds,
            scores_by_evaluator={
                k: round(v, 4) for k, v in run.scores_by_evaluator().items()
            },
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/eval/experiments", response_model=list[ExperimentInfo])
async def get_experiments():
    """List all available experiments."""
    return [
        ExperimentInfo(
            name=exp.name,
            description=exp.description,
            dataset=exp.dataset,
            evaluators=exp.evaluators,
        )
        for exp in list_experiments()
    ]


@app.get("/api/eval/results/{run_id}")
async def get_results(run_id: str):
    """Get results of a specific evaluation run."""
    run = _eval_results.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return {
        "run_id": run.run_id,
        "timestamp": run.timestamp,
        "dataset": run.dataset,
        "total_cases": run.total_cases,
        "passed": run.passed,
        "failed": run.failed,
        "pass_rate": round(run.pass_rate, 4),
        "avg_score": round(run.avg_score, 4),
        "duration_seconds": run.duration_seconds,
        "evaluators_used": run.evaluators_used,
        "scores_by_evaluator": {
            k: round(v, 4) for k, v in run.scores_by_evaluator().items()
        },
        "results": [r.model_dump() for r in run.results],
    }


# --- CLI ---

def cli_main():
    """Run evaluation from the command line."""
    parser = argparse.ArgumentParser(
        description="AI Platform Evaluation Framework CLI"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="",
        help="Dataset YAML filename (e.g. enrollment_queries.yaml)",
    )
    parser.add_argument(
        "--experiment",
        type=str,
        default="",
        help="Named experiment to run",
    )
    parser.add_argument(
        "--evaluators",
        type=str,
        nargs="*",
        default=[],
        help="Evaluator names to use",
    )
    parser.add_argument(
        "--report",
        type=str,
        choices=["console", "json", "html", "all"],
        default="console",
        help="Report format",
    )
    parser.add_argument(
        "--target-url",
        type=str,
        default="",
        help="Override orchestrator URL",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=False,
        help="Run test cases in parallel",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Output path for json/html reports",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        default=False,
        help="Start the evaluation API server",
    )

    args = parser.parse_args()

    if args.serve:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=settings.eval_port)
        return

    dataset_dir = Path(settings.default_dataset_dir)

    if args.experiment:
        exp = get_experiment(args.experiment)
        evaluator_names = exp.evaluators
        target_url = args.target_url or exp.get_target_url()

        if exp.dataset == "all":
            all_datasets = load_all_datasets(dataset_dir)
            test_cases = []
            for cases in all_datasets.values():
                test_cases.extend(cases)
            dataset_name = "all"
        else:
            test_cases = load_test_cases(dataset_dir / exp.dataset)
            dataset_name = exp.dataset
    elif args.dataset:
        test_cases = load_test_cases(dataset_dir / args.dataset)
        dataset_name = args.dataset
        evaluator_names = args.evaluators or list(EVALUATOR_REGISTRY.keys())
        target_url = args.target_url or settings.orchestrator_url
    else:
        parser.error("Either --dataset or --experiment must be provided (or use --serve)")

    evaluators = build_evaluators(evaluator_names)

    runner = run_parallel if args.parallel else run_sequential
    run = asyncio.run(
        runner(
            test_cases=test_cases,
            evaluators=evaluators,
            target_url=target_url,
            dataset_name=dataset_name,
        )
    )

    # Generate reports
    if args.report in ("console", "all"):
        print_eval_report(run)

    if args.report in ("json", "all"):
        path = write_json_report(run, args.output if args.output else None)
        print(f"JSON report written to: {path}")

    if args.report in ("html", "all"):
        path = write_html_report(run, args.output if args.output else None)
        print(f"HTML report written to: {path}")


if __name__ == "__main__":
    cli_main()
