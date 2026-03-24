import subprocess
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Template

from src.runners.sequential import EvalRun

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Evaluation Report - {{ run_id }}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f5f7fa; color: #333; padding: 2rem; }
  .container { max-width: 1200px; margin: 0 auto; }
  h1 { text-align: center; color: #1a1a2e; margin-bottom: 0.5rem; }
  .subtitle { text-align: center; color: #666; margin-bottom: 2rem; font-size: 0.9rem; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
           gap: 1rem; margin-bottom: 2rem; }
  .card { background: white; border-radius: 8px; padding: 1.5rem;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }
  .card .label { font-size: 0.85rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
  .card .value { font-size: 2rem; font-weight: 700; margin-top: 0.5rem; }
  .card .value.green { color: #2ecc71; }
  .card .value.yellow { color: #f39c12; }
  .card .value.red { color: #e74c3c; }
  .section { background: white; border-radius: 8px; padding: 1.5rem;
             box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem; }
  .section h2 { margin-bottom: 1rem; color: #1a1a2e; font-size: 1.2rem; }
  .bar-chart { margin: 1rem 0; }
  .bar-row { display: flex; align-items: center; margin-bottom: 0.75rem; }
  .bar-label { width: 140px; font-size: 0.85rem; font-weight: 600; }
  .bar-track { flex: 1; height: 24px; background: #ecf0f1; border-radius: 4px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 4px; display: flex; align-items: center;
              padding-left: 8px; font-size: 0.75rem; color: white; font-weight: 600;
              transition: width 0.3s ease; }
  .bar-fill.green { background: #2ecc71; }
  .bar-fill.yellow { background: #f39c12; }
  .bar-fill.red { background: #e74c3c; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th { background: #f8f9fa; padding: 0.75rem; text-align: left; border-bottom: 2px solid #dee2e6;
       font-weight: 600; }
  td { padding: 0.75rem; border-bottom: 1px solid #eee; }
  tr:hover { background: #f8f9fa; }
  .badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px;
           font-size: 0.75rem; font-weight: 600; }
  .badge.pass { background: #d4edda; color: #155724; }
  .badge.fail { background: #f8d7da; color: #721c24; }
  .details-text { max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .footer { text-align: center; color: #999; font-size: 0.8rem; margin-top: 2rem; }
</style>
</head>
<body>
<div class="container">
  <h1>Evaluation Report</h1>
  <p class="subtitle">Run {{ run_id }} | {{ dataset }} | {{ timestamp }} | Git: {{ git_sha[:8] }}</p>

  <div class="cards">
    <div class="card">
      <div class="label">Pass Rate</div>
      <div class="value {{ pass_rate_color }}">{{ pass_rate_pct }}%</div>
    </div>
    <div class="card">
      <div class="label">Avg Score</div>
      <div class="value">{{ avg_score }}</div>
    </div>
    <div class="card">
      <div class="label">Duration</div>
      <div class="value">{{ duration }}s</div>
    </div>
    <div class="card">
      <div class="label">Test Cases</div>
      <div class="value">{{ total_cases }}</div>
    </div>
    <div class="card">
      <div class="label">Passed / Failed</div>
      <div class="value green">{{ passed }}</div>
      <div style="font-size:0.9rem;color:#e74c3c;">{{ failed }} failed</div>
    </div>
  </div>

  <div class="section">
    <h2>Scores by Evaluator</h2>
    <div class="bar-chart">
      {% for eval_name, score in evaluator_scores.items() %}
      <div class="bar-row">
        <div class="bar-label">{{ eval_name }}</div>
        <div class="bar-track">
          <div class="bar-fill {{ 'green' if score >= 0.8 else 'yellow' if score >= 0.6 else 'red' }}"
               style="width: {{ (score * 100)|round|int }}%;">
            {{ (score * 100)|round(1) }}%
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>

  <div class="section">
    <h2>Detailed Results</h2>
    <table>
      <thead>
        <tr>
          <th>Test Case</th>
          <th>Evaluator</th>
          <th>Status</th>
          <th>Score</th>
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        {% for r in results %}
        <tr>
          <td>{{ r.test_case_id }}</td>
          <td>{{ r.evaluator }}</td>
          <td><span class="badge {{ 'pass' if r.passed else 'fail' }}">{{ 'PASS' if r.passed else 'FAIL' }}</span></td>
          <td>{{ r.score }}</td>
          <td class="details-text" title="{{ r.details }}">{{ r.details[:120] }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="footer">
    Generated by AI Platform Evaluation Framework
  </div>
</div>
</body>
</html>"""


def _get_git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def write_html_report(run: EvalRun, output_path: str | Path | None = None) -> Path:
    """Generate a standalone HTML evaluation report.

    Args:
        run: The completed evaluation run.
        output_path: Optional output file path. Defaults to reports/eval_{run_id}.html.

    Returns:
        Path to the written report file.
    """
    if output_path is None:
        reports_dir = Path(__file__).resolve().parent.parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        output_path = reports_dir / f"eval_{run.run_id}.html"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    pass_rate_pct = round(run.pass_rate * 100, 1)
    if pass_rate_pct >= 80:
        pass_rate_color = "green"
    elif pass_rate_pct >= 60:
        pass_rate_color = "yellow"
    else:
        pass_rate_color = "red"

    template = Template(HTML_TEMPLATE)
    html = template.render(
        run_id=run.run_id,
        dataset=run.dataset,
        timestamp=run.timestamp,
        git_sha=_get_git_sha(),
        pass_rate_pct=pass_rate_pct,
        pass_rate_color=pass_rate_color,
        avg_score=f"{run.avg_score:.4f}",
        duration=run.duration_seconds,
        total_cases=run.total_cases,
        passed=run.passed,
        failed=run.failed,
        evaluator_scores=run.scores_by_evaluator(),
        results=[r.model_dump() for r in run.results],
    )

    with open(output_path, "w") as f:
        f.write(html)

    return output_path
