"""W0 hello-world LangGraph. Validates the stack end-to-end."""
import asyncio
import json
from pathlib import Path

# from groq import AsyncGroq
from langgraph.graph import END, START, StateGraph

from amoa.agents.safety_pilot import run_safety_pilot

# from amoa.config import settings
from amoa.state import MissionState


async def safety_pilot_node(state: MissionState) -> dict:
    """LangGraph node wrapping the Safety Pilot agent."""
    cdm_path = (
        Path(__file__).parent.parent.parent
        / "tests" / "fixtures" / "cdms" / "three_scenarios.json"
    )
    scenarios = json.loads(cdm_path.read_text())
    cdm = scenarios["high_risk"]

    assessment = await run_safety_pilot(cdm)
    return {"safety_assessment": assessment}


def build_graph():
    graph = StateGraph(MissionState)
    graph.add_node("safety_pilot", safety_pilot_node)
    graph.add_edge(START, "safety_pilot")
    graph.add_edge("safety_pilot", END)
    return graph.compile()


async def run_demo() -> MissionState:
    g = build_graph()
    initial = MissionState()
    result = await g.ainvoke(initial)
    return MissionState(**result)


if __name__ == "__main__":
    state = asyncio.run(run_demo())
    a = state.safety_assessment
    print(f"Risk Level    : {a.risk_level}")
    print(f"Action        : {a.recommended_action}")
    print(f"PC            : {a.pc}")
    print(f"Miss Distance : {a.miss_distance_m} m")
    print(f"Reasoning     : {a.reasoning}")
