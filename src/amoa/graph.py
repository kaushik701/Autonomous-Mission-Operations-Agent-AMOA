"""W3 LangGraph — Safety Pilot + Health Guard + Payload Scientist in parallel via Send fan-out."""
import asyncio
import json
from pathlib import Path

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from amoa.agents.health_guard import run_health_guard
from amoa.agents.payload_scientist import run_payload_scientist
from amoa.agents.safety_pilot import run_safety_pilot
from amoa.data.esa_loader import load_channel_window
from amoa.data.sentinel_loader import list_scenes, load_scene
from amoa.state import MissionState


def _load_cdm() -> dict:
    cdm_path = (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "cdms" / "three_scenarios.json"
    )
    return json.loads(cdm_path.read_text())["high_risk"]


def _load_scene() -> dict:
    tci_scenes = [p for p in list_scenes() if "TCI" in p.name and "_1" not in p.name]
    path = tci_scenes[0] if tci_scenes else list_scenes()[0]
    return load_scene(path)


def _load_telemetry() -> dict:
    df = load_channel_window(10, start_idx=0, window_size=50)
    return {
        "channel_name": "channel_10",
        "values": df.iloc[:, 0].tolist(),
        "is_anomaly": 0,
    }


def dispatch(state: MissionState) -> list[Send]:
    """Fan out Safety Pilot and Health Guard in parallel.

    Each Send carries only the payload the destination node needs —
    not the full MissionState. Mismatch = silent fan-out failure.
    """
    return [
        Send("safety_pilot", {"cdm": _load_cdm()}),
        Send("health_guard", {"telemetry": _load_telemetry()}),
        Send("payload_scientist", {"scene": _load_scene()}),
    ]


async def safety_pilot_node(payload: dict) -> dict:
    """Receives CDM payload from Send fan-out, returns safety_assessment."""
    assessment = await run_safety_pilot(payload["cdm"])
    return {"safety_assessment": assessment}


async def health_guard_node(payload: dict) -> dict:
    """Receives telemetry payload from Send fan-out, returns health_assessment."""
    assessment = await run_health_guard(payload["telemetry"])
    return {"health_assessment": assessment}


async def payload_scientist_node(payload: dict) -> dict:
    """Receives scene payload from Send fan-out, returns payload_assessment."""
    assessment = await run_payload_scientist(payload["scene"])
    return {"payload_assessment": assessment}


def build_graph():
    graph = StateGraph(MissionState)
    graph.add_node("safety_pilot", safety_pilot_node)
    graph.add_node("health_guard", health_guard_node)
    graph.add_node("payload_scientist", payload_scientist_node)
    graph.add_conditional_edges(
        START, dispatch, ["safety_pilot", "health_guard", "payload_scientist"]
    )
    graph.add_edge("safety_pilot", END)
    graph.add_edge("health_guard", END)
    graph.add_edge("payload_scientist", END)
    return graph.compile()


async def run_demo() -> MissionState:
    g = build_graph()
    result = await g.ainvoke(MissionState())
    return MissionState(**result)


if __name__ == "__main__":
    state = asyncio.run(run_demo())

    a = state.safety_assessment
    print("-- Safety Pilot ----------------------")
    print(f"Risk Level    : {a.risk_level}")
    print(f"Action        : {a.recommended_action}")
    print(f"PC            : {a.pc}")
    print(f"Miss Distance : {a.miss_distance_m} m")
    print(f"Reasoning     : {a.reasoning}")

    h = state.health_assessment
    print("\n-- Health Guard ----------------------")
    print(f"Anomaly       : {h.anomaly_detected}")
    print(f"Severity      : {h.severity}")
    print(f"Channels      : {h.affected_channels}")
    print(f"Confidence    : {h.confidence}")
    print(f"Reasoning     : {h.reasoning}")

    p = state.payload_assessment
    print("\n-- Payload Scientist -----------------")
    print(f"Cloud Cover   : {p.cloud_coverage_pct}%")
    print(f"Image Quality : {p.image_quality}")
    print(f"Land Cover    : {p.land_cover}")
    print(f"Obs Value     : {p.observation_value}")
    print(f"Confidence    : {p.confidence}")
    print(f"Features      : {p.features_observed}")
    print(f"Reasoning     : {p.reasoning}")
