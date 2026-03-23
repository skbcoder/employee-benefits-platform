from rich.console import Console
from rich.table import Table

from src.runners.sequential import EvalRun

console = Console()


def print_eval_report(run: EvalRun) -> None:
    """Print a Rich-formatted evaluation report to the terminal.

    Args:
        run: The completed evaluation run to report on.
    """
    console.print()
    console.print("[bold cyan]Evaluation Report[/bold cyan]", justify="center")
    console.print(f"[dim]Run ID: {run.run_id}[/dim]", justify="center")
    console.print(f"[dim]Dataset: {run.dataset} | Duration: {run.duration_seconds}s[/dim]", justify="center")
    console.print()

    # Summary table
    summary_table = Table(title="Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", justify="right")

    summary_table.add_row("Total Test Cases", str(run.total_cases))
    summary_table.add_row("Total Evaluations", str(len(run.results)))

    pass_rate = run.pass_rate * 100
    pass_color = "green" if pass_rate >= 80 else "yellow" if pass_rate >= 60 else "red"
    summary_table.add_row("Passed", f"[{pass_color}]{run.passed}[/{pass_color}]")
    summary_table.add_row("Failed", f"[red]{run.failed}[/red]" if run.failed else "0")
    summary_table.add_row(
        "Pass Rate",
        f"[{pass_color}]{pass_rate:.1f}%[/{pass_color}]",
    )
    summary_table.add_row("Avg Score", f"{run.avg_score:.4f}")

    console.print(summary_table)
    console.print()

    # Per-evaluator breakdown
    eval_table = Table(
        title="Scores by Evaluator", show_header=True, header_style="bold magenta"
    )
    eval_table.add_column("Evaluator", style="cyan")
    eval_table.add_column("Avg Score", justify="right")
    eval_table.add_column("Pass Rate", justify="right")

    scores_by_eval = run.scores_by_evaluator()
    pass_rates_by_eval = run.pass_rate_by_evaluator()

    for evaluator_name in sorted(scores_by_eval.keys()):
        avg = scores_by_eval[evaluator_name]
        pr = pass_rates_by_eval.get(evaluator_name, 0.0) * 100
        color = "green" if pr >= 80 else "yellow" if pr >= 60 else "red"
        eval_table.add_row(
            evaluator_name,
            f"{avg:.4f}",
            f"[{color}]{pr:.1f}%[/{color}]",
        )

    console.print(eval_table)
    console.print()

    # Failed test cases
    failed_results = [r for r in run.results if not r.passed]
    if failed_results:
        fail_table = Table(
            title="Failed Evaluations",
            show_header=True,
            header_style="bold red",
        )
        fail_table.add_column("Test Case", style="cyan", max_width=30)
        fail_table.add_column("Evaluator", style="yellow")
        fail_table.add_column("Score", justify="right")
        fail_table.add_column("Details", max_width=60)

        for result in failed_results:
            fail_table.add_row(
                result.test_case_id,
                result.evaluator,
                f"[red]{result.score:.4f}[/red]",
                result.details[:100],
            )

        console.print(fail_table)
    else:
        console.print("[bold green]All evaluations passed![/bold green]")

    console.print()
