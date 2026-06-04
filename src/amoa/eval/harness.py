"""
Unified eval harness — runs all scenario fixtures through the full graph,
writes RESULTS.md. Invoked via: uv run python -m amoa.eval.harness
"""
import asyncio
import json
from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import patch

from amoa.graph import build_graph
from amoa.state import MissionState, FailureEvent
from amoa.agents.safety_pilot import SafetyAssessment
from amoa.agents.health_guard import HealthAssessment
from amoa.agents.payload_scientist import PayloadAssessment

SCENARIOS_DIR = Path("tests/fixtures/scenarios")
RESULTS_MD = Path("RESULTS.md")
FAILURES_JSONL = Path("src/amoa/eval/failures.jsonl")


def _load(name: str) -> dict:
    return json.loads((SCENARIOS_DIR / f"{name}.json").read_text())


def _state_from(scenario: dict) -> MissionState:
    kwargs: dict = {}
    if scenario.get("safety_assessment"):
        kwargs["safety_assessment"] = SafetyAssessment(**scenario["safety_assessment"])
    if scenario.get("health_assessment"):
        kwargs["health_assessment"] = HealthAssessment(**scenario["health_assessment"])
    if scenario.get("payload_assessment"):
        kwargs["payload_assessment"] = PayloadAssessment(**scenario["payload_assessment"])
    if scenario.get("failure_log"):
        kwargs["failure_log"] = [FailureEvent(**f) for f in scenario["failure_log"]]
    return MissionState(**kwargs)


def _make_mocks(pre: MissionState):
    async def mock_safety(_state):
        if pre.safety_assessment:
            return {"safety_assessment": pre.safety_assessment}
        return {"failure_log": [FailureEvent(
            agent="safety_pilot", error="no data", category="schema_violation"
        )]}

    async def mock_health(_state):
        if pre.health_assessment:
            return {"health_assessment": pre.health_assessment}
        return {"failure_log": pre.failure_log or [FailureEvent(
            agent="health_guard", error="no data", category="schema_violation"
        )]}

    async def mock_payload(_state):
        if pre.payload_assessment:
            return {"payload_assessment": pre.payload_assessment}
        return {}

    return mock_safety, mock_health, mock_payload


async def run_scenario(name: str) -> dict:
    scenario = _load(name)
    pre = _state_from(scenario)
    mock_safety, mock_health, mock_payload = _make_mocks(pre)

    with (
        patch("amoa.graph.safety_pilot_node", side_effect=mock_safety),
        patch("amoa.graph.health_guard_node", side_effect=mock_health),
        patch("amoa.graph.payload_scientist_node", side_effect=mock_payload),
    ):
        g = build_graph()
        raw = await g.ainvoke(MissionState())

    result = MissionState(**raw)
    d = result.supervisor_decision
    return {
        "scenario": name,
        "action": d.priority_action if d else "ERROR",
        "confidence": d.confidence if d else 0.0,
        "degraded": d.degraded_mode if d else True,
        "failures": len(result.failure_log),
        "safety_risk": result.safety_assessment.risk_level.value if result.safety_assessment else "—",
        "health_severity": result.health_assessment.severity.value if result.health_assessment else "—",
    }


async def main():
    scenarios = ["clear", "conflict", "degraded"]
    rows = []
    for name in scenarios:
        print(f"  running {name}...", end=" ", flush=True)
        row = await run_scenario(name)
        rows.append(row)
        print(f"{row['action']} (conf={row['confidence']:.0%}, degraded={row['degraded']})")

        if row["failures"]:
            with open(FAILURES_JSONL, "a") as f:
                f.write(json.dumps({
                    "ts": datetime.now(UTC).isoformat(),
                    "scenario": name,
                    "failures": row["failures"],
                }) + "\n")

    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# AMOA Eval Results\n",
        f"Generated: {ts}\n\n",
        "| Scenario | Safety | Health | Action | Confidence | Degraded | Failures |\n",
        "|---|---|---|---|---|---|---|\n",
    ]
    for r in rows:
        lines.append(
            f"| {r['scenario']} | {r['safety_risk']} | {r['health_severity']} "
            f"| {r['action']} | {r['confidence']:.0%} | {r['degraded']} | {r['failures']} |\n"
        )
    lines += [
        "\n## Notes\n\n",
        "- Scenario fixtures in `tests/fixtures/scenarios/`\n",
        "- Agent nodes mocked — no live LLM calls\n",
        "- Resolver rule: Safety HIGH → MANEUVER; else NOMINAL_OPS\n",
        "- `degraded=True` when any agent failure logged\n",
    ]

    RESULTS_MD.write_text("".join(lines), encoding="utf-8")
    print(f"\nWrote {RESULTS_MD}")


if __name__ == "__main__":
    asyncio.run(main())
