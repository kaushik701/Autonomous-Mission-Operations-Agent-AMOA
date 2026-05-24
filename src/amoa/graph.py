"""W0 hello-world LangGraph. Validates the stack end-to-end."""
import asyncio
from anthropic import AsyncAnthropic
from langgraph.graph import StateGraph, START, END

from amoa.config import settings
from amoa.state import MissionState, HelloMessage


async def hello_node(state: MissionState) -> dict:
    """Single node that calls Claude and adds the response to state."""
    client = AsyncAnthropic(api_key=settings.anthropic_api_key, base_url=settings.anthropic_base_url)

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=128,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are about to help build AMOA, an autonomous mission "
                    "operations agent for satellites. In one sentence, what is "
                    "the hardest part of multi-agent coordination?"
                ),
            }
        ],
    )
    text = response.content[0].text
    return {"messages": [HelloMessage(text=text)]}


def build_graph():
    graph = StateGraph(MissionState)
    graph.add_node("hello", hello_node)
    graph.add_edge(START, "hello")
    graph.add_edge("hello", END)
    return graph.compile()


async def run_demo() -> MissionState:
    g = build_graph()
    initial = MissionState()
    result = await g.ainvoke(initial)
    return MissionState(**result)


if __name__ == "__main__":
    state = asyncio.run(run_demo())
    for msg in state.messages:
        print(f"[{msg.timestamp.isoformat()}] {msg.text}")
