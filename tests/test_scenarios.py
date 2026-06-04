"""
Scenario tests for the full graph + Conflict Resolver.

Each scenario pre-builds MissionState from a fixture JSON, patches the three
agent nodes to return that fixture data (no live LLM calls), invokes the graph,
and asserts the resolver's decision.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from amoa.graph import build_graph
from amoa.state import MissionState, FailureEvent
from amoa.agents.safety_pilot import SafetyAssessment
from amoa.agents.health_guard import HealthAssessment
from amoa.agents.payload_scientist import PayloadAssessment

SCENARIOS_DIR = Path(__file__).parent / "fixtures" / "scenarios"


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
    """Return async mock callables for each agent node based on pre-built state."""
    async def mock_safety(_state):
        if pre.safety_assessment:
            return {"safety_assessment": pre.safety_assessment}
        return {"failure_log": [FailureEvent(
            agent="safety_pilot", error="mock: no data", category="schema_violation"
        )]}

    async def mock_health(_state):
        if pre.health_assessment:
            return {"health_assessment": pre.health_assessment}
        return {"failure_log": pre.failure_log or [FailureEvent(
            agent="health_guard", error="mock: no data", category="schema_violation"
        )]}

    async def mock_payload(_state):
        if pre.payload_assessment:
            return {"payload_assessment": pre.payload_assessment}
        return {}

    return mock_safety, mock_health, mock_payload


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario_name,expected_action,expected_degraded", [
    ("clear",    "NOMINAL_OPS", False),
    ("conflict", "MANEUVER",    False),
    ("degraded", "NOMINAL_OPS", True),
])
async def test_scenario(scenario_name, expected_action, expected_degraded):
    scenario = _load(scenario_name)
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
    assert result.supervisor_decision is not None, "Resolver produced no decision"
    assert result.supervisor_decision.priority_action == expected_action, (
        f"[{scenario_name}] expected {expected_action!r}, "
        f"got {result.supervisor_decision.priority_action!r}"
    )
    assert result.supervisor_decision.degraded_mode == expected_degraded, (
        f"[{scenario_name}] expected degraded_mode={expected_degraded}"
    )
