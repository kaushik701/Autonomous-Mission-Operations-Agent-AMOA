"""
Unified eval harness — invoked via `make eval`.
Runs all fixture tests, statistical comparisons, snapshot checks.
Produces eval/results/RESULTS.md.
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path("src/amoa/eval/results")
RESULTS_MD = RESULTS_DIR / "RESULTS.md"


def run_pytest() -> dict:
    result = subprocess.run(
        ["uv", "run", "pytest", "-v", "--tb=short", "--json-report",
         "--json-report-file=src/amoa/eval/results/pytest_report.json"],
        capture_output=True, text=True
    )
    return {"returncode": result.returncode, "stdout": result.stdout}


def load_baseline_metrics() -> dict:
    path = Path("src/amoa/eval/baseline_metrics.json")
    if path.exists():
        return json.loads(path.read_text())
    return {}


def write_results_md(pytest_result: dict, baseline: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# AMOA Eval Results",
        f"**Run:** {datetime.utcnow().isoformat()}",
        f"",
        f"## Test Suite",
        f"- Exit code: {pytest_result['returncode']}",
        f"- {'✅ All tests passed' if pytest_result['returncode'] == 0 else '❌ Some tests failed'}",
        f"",
        f"## Baseline Metrics (IsolationForest)",
    ]
    if baseline:
        lines += [
            f"- F1: {baseline.get('f1', 'N/A')}",
            f"- Precision: {baseline.get('precision', 'N/A')}",
            f"- Recall: {baseline.get('recall', 'N/A')}",
            f"- Windows: {baseline.get('n_windows', 'N/A')}",
        ]
    else:
        lines.append("- No baseline metrics found — run W2 IsolationForest first")

    RESULTS_MD.write_text("\n".join(lines))
    print(f"Results written to {RESULTS_MD}")


if __name__ == "__main__":
    print("Running AMOA eval harness...")
    pytest_result = run_pytest()
    baseline = load_baseline_metrics()
    write_results_md(pytest_result, baseline)
    print("Done.")