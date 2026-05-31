"""
W1 Thursday: Safety Pilot end-to-end tests with mocked CDM fixtures.

Three scenarios: low / medium / high risk.
No real API calls — _call_provider is mocked.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from amoa.agents.safety_pilot import run_safety_pilot, RiskLevel, RecommendedAction

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "cdms" / "three_scenarios.json").read_text()
)


def make_mock_response(risk_level: str, action: str, pc: float, cdm: dict) -> str:
    """Build a valid JSON response string for the mock."""
    return json.dumps({
        "pc": pc,
        "miss_distance_m": cdm["miss_distance_m"],
        "tca": cdm["tca"],
        "sat1_name": cdm["sat1_name"],
        "sat2_name": cdm["sat2_name"],
        "risk_level": risk_level,
        "recommended_action": action,
        "confidence": 0.95,
        "reasoning": f"PC of {pc} places this conjunction in the {risk_level} category.",
    })


@pytest.mark.asyncio
async def test_low_risk_cdm():
    """PC=1e-7 → LOW risk, MONITOR."""
    cdm = FIXTURES["low_risk"]
    mock_response = make_mock_response("LOW", "MONITOR", cdm["pc"], cdm)

    with patch("amoa.llm._call_provider", new=AsyncMock(return_value=mock_response)):
        result = await run_safety_pilot(cdm)

    assert result.risk_level == RiskLevel.LOW
    assert result.recommended_action == RecommendedAction.MONITOR
    assert result.pc == 1e-7
    assert result.confidence > 0.0


@pytest.mark.asyncio
async def test_medium_risk_cdm():
    """PC=1e-5 → MEDIUM risk, MONITOR."""
    cdm = FIXTURES["medium_risk"]
    mock_response = make_mock_response("MEDIUM", "MONITOR", cdm["pc"], cdm)

    with patch("amoa.llm._call_provider", new=AsyncMock(return_value=mock_response)):
        result = await run_safety_pilot(cdm)

    assert result.risk_level == RiskLevel.MEDIUM
    assert result.recommended_action == RecommendedAction.MONITOR
    assert result.pc == 1e-5


@pytest.mark.asyncio
async def test_high_risk_cdm():
    """PC=1e-3 → HIGH risk, MANEUVER."""
    cdm = FIXTURES["high_risk"]
    mock_response = make_mock_response("HIGH", "MANEUVER", cdm["pc"], cdm)

    with patch("amoa.llm._call_provider", new=AsyncMock(return_value=mock_response)):
        result = await run_safety_pilot(cdm)

    assert result.risk_level == RiskLevel.HIGH
    assert result.recommended_action == RecommendedAction.MANEUVER
    assert result.pc == 1e-3