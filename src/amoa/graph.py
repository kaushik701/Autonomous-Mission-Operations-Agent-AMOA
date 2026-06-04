"""
W4: Full supervisor with Send fan-out to three agents.
Conflict Resolver receives all assessments + failure_log.
"""
import asyncio
import json
from pathlib import Path
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from amoa.state import MissionState, FailureEvent
from amoa.agents.safety_pilot import run_safety_pilot
from amoa.agents.health_guard import run_health_guard
from amoa.agents.payload_scientist import run_payload_scientist


async def safety_pilot_node(state: MissionState) -> dict:
    cdm_path = Path("tests/fixtures/cdms/three_scenarios.json")
    cdm = json.loads(cdm_path.read_text())["high_risk"]
    try:
        assessment = await run_safety_pilot(cdm)
        return {"safety_assessment": assessment}
    except Exception as e:
        return {"failure_log": [FailureEvent(
            agent="safety_pilot",
            category="timeout" if "timeout" in str(e).lower() else "schema_violation",
            error=str(e),
            recoverable=True,
        )]}


async def health_guard_node(state: MissionState) -> dict:
    window = {
        "channel_name": "temperature_sensor_1",
        "values": [23.1, 23.4, 45.8, 23.2, 23.3],
        "is_anomaly": 1,
    }
    try:
        assessment = await run_health_guard(window)
        return {"health_assessment": assessment}
    except Exception as e:
        return {"failure_log": [FailureEvent(
            agent="health_guard",
            category="rate_limit" if "429" in str(e) else "schema_violation",
            error=str(e),
            recoverable=True,
        )]}


async def payload_scientist_node(state: MissionState) -> dict:
    from amoa.data.sentinel_loader import load_scene, list_scenes
    scenes = list_scenes()
    if not scenes:
        return {"failure_log": [FailureEvent(
            agent="payload_scientist",
            category="timeout",
            error="No scenes available in data/sentinel/",
            recoverable=False,
        )]}
    try:
        scene = load_scene(scenes[0])
        assessment = await run_payload_scientist(scene)
        return {"payload_assessment": assessment}
    except Exception as e:
        return {"failure_log": [FailureEvent(
            agent="payload_scientist",
            category="schema_violation",
            error=str(e),
            recoverable=True,
        )]}


def fan_out(state: MissionState) -> list[Send]:
    return [
        Send("safety_pilot", state),
        Send("health_guard", state),
        Send("payload_scientist", state),
    ]


async def conflict_resolver_node(state: MissionState) -> dict:
    """Placeholder — full resolver built Thursday."""
    from amoa.state import SupervisorDecision
    degraded = len(state.failure_log) > 0
    safety_wins = (
        state.safety_assessment is not None
        and state.safety_assessment.risk_level.value == "HIGH"
    )
    return {
        "supervisor_decision": SupervisorDecision(
            priority_action="MANEUVER" if safety_wins else "NOMINAL_OPS",
            reasoning="Safety Pilot HIGH risk overrides all other concerns." if safety_wins
                      else "No critical issues detected.",
            confidence=0.95 if not degraded else 0.6,
            degraded_mode=degraded,
        )
    }


def build_graph():
    graph = StateGraph(MissionState)
    graph.add_node("safety_pilot", safety_pilot_node)
    graph.add_node("health_guard", health_guard_node)
    graph.add_node("payload_scientist", payload_scientist_node)
    graph.add_node("conflict_resolver", conflict_resolver_node)
    graph.add_conditional_edges(START, fan_out, ["safety_pilot", "health_guard", "payload_scientist"])
    graph.add_edge("safety_pilot", "conflict_resolver")
    graph.add_edge("health_guard", "conflict_resolver")
    graph.add_edge("payload_scientist", "conflict_resolver")
    graph.add_edge("conflict_resolver", END)
    return graph.compile()


async def run_demo() -> MissionState:
    g = build_graph()
    result = await g.ainvoke(MissionState())
    return MissionState(**result)


if __name__ == "__main__":
    state = asyncio.run(run_demo())
    d = state.supervisor_decision
    print(f"Decision  : {d.priority_action}")
    print(f"Reasoning : {d.reasoning}")
    print(f"Confidence: {d.confidence}")
    print(f"Degraded  : {d.degraded_mode}")
    print(f"Failures  : {len(state.failure_log)}")