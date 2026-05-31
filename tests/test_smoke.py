"""W0/W1 smoke tests. Verify imports, config, state, and graph compilation."""
import pytest

from amoa.config import settings
from amoa.graph import build_graph, safety_pilot_node
from amoa.state import HelloMessage, MissionState


def test_settings_load():
    """Config loads from .env without crashing."""
    assert settings.google_api_key
    assert settings.groq_api_key


def test_mission_state_default():
    """MissionState constructs with no args."""
    state = MissionState()
    assert state.messages == []
    assert state.safety_assessment is None


def test_hello_message_creates_timestamp():
    msg = HelloMessage(text="hi")
    assert msg.timestamp is not None


def test_graph_compiles():
    """Graph builds without crashing."""
    g = build_graph()
    assert g is not None


@pytest.mark.asyncio
async def test_safety_pilot_node_returns_assessment():
    """Live Groq call — verifies Safety Pilot node accepts Send payload shape."""
    from amoa.graph import _load_cdm
    payload = {"cdm": _load_cdm()}
    result = await safety_pilot_node(payload)
    assert "safety_assessment" in result
    a = result["safety_assessment"]
    assert a.risk_level is not None
    assert a.recommended_action is not None
    assert 0.0 <= a.confidence <= 1.0


def test_state_messages_concat():
    """Operator.add accumulates message lists."""
    s1 = MissionState(messages=[HelloMessage(text="a")])
    s2 = MissionState(messages=[HelloMessage(text="b")])
    combined = s1.messages + s2.messages
    assert len(combined) == 2
