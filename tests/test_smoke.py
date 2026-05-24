"""W0 smoke tests. Verify imports, config, state, graph compilation."""
import pytest
from amoa.config import settings
from amoa.state import MissionState, HelloMessage
from amoa.graph import build_graph, hello_node


def test_settings_load():
    """Config loads from .env without crashing."""
    assert settings.anthropic_api_key
    assert settings.google_api_key
    assert settings.groq_api_key


def test_mission_state_default():
    """MissionState constructs with no args."""
    state = MissionState()
    assert state.messages == []


def test_hello_message_creates_timestamp():
    msg = HelloMessage(text="hi")
    assert msg.timestamp is not None


def test_graph_compiles():
    """Graph builds without crashing."""
    g = build_graph()
    assert g is not None


@pytest.mark.asyncio
async def test_hello_node_returns_message():
    """Live API call — costs ~$0.001."""
    state = MissionState()
    result = await hello_node(state)
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["messages"][0].text


def test_state_messages_concat():
    """Operator.add accumulates message lists."""
    s1 = MissionState(messages=[HelloMessage(text="a")])
    s2 = MissionState(messages=[HelloMessage(text="b")])
    combined = s1.messages + s2.messages
    assert len(combined) == 2
