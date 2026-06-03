"""
W3 Friday: Snapshot tests for all three agents.
Locks expected output shapes on canonical inputs.
Catches behavior drift on prompt changes.

Run with: uv run pytest tests/test_snapshots.py -v
Update snapshots: uv run pytest tests/test_snapshots.py --snapshot-update
"""
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from syrupy.assertion import SnapshotAssertion

from amoa.agents.safety_pilot import run_safety_pilot
from amoa.agents.health_guard import run_health_guard
from amoa.agents.payload_scientist import run_payload_scientist

# Canonical inputs — never change these after W3
CANONICAL_CDM = {
    "pc": 1e-5,
    "miss_distance_m": 412.3,
    "tca": "2026-06-07T09:15:22",
    "sat1_name": "SENTINEL-2A",
    "sat2_name": "SL-16 R/B",
}

CANONICAL_TELEMETRY = {
    "channel_name": "temperature_sensor_1",
    "values": [23.1, 23.4, 23.2, 45.8, 23.3, 23.1],  # spike at index 3
    "is_anomaly": 1,
}

CANONICAL_SCENE = {
    "filename": "canonical_test_scene.tif",
    "base64_image": "iVBORw0KGgo=",  # minimal valid base64
    "original_width": 1024,
    "original_height": 1024,
    "band": "TCI",
}


@pytest.mark.asyncio
async def test_safety_pilot_snapshot(snapshot: SnapshotAssertion):
    """Lock Safety Pilot output shape on canonical CDM."""
    mock_response = json.dumps({
        "pc": 1e-5,
        "miss_distance_m": 412.3,
        "tca": "2026-06-07T09:15:22",
        "sat1_name": "SENTINEL-2A",
        "sat2_name": "SL-16 R/B",
        "risk_level": "MEDIUM",
        "recommended_action": "MONITOR",
        "confidence": 0.92,
        "reasoning": "PC of 1e-5 is in the MEDIUM band — monitor closely.",
    })
    with patch("amoa.llm._call_provider", new=AsyncMock(return_value=mock_response)):
        result = await run_safety_pilot(CANONICAL_CDM)
    assert result.model_dump() == snapshot


@pytest.mark.asyncio
async def test_health_guard_snapshot(snapshot: SnapshotAssertion):
    """Lock Health Guard output shape on canonical telemetry window."""
    mock_response = json.dumps({
        "anomaly_detected": True,
        "severity": "WARNING",
        "affected_channels": ["temperature_sensor_1"],
        "confidence": 0.88,
        "reasoning": "Spike at index 3 is 22 degrees above baseline.",
    })
    with patch("amoa.llm._call_provider", new=AsyncMock(return_value=mock_response)):
        result = await run_health_guard(CANONICAL_TELEMETRY)
    assert result.model_dump() == snapshot


@pytest.mark.asyncio
async def test_payload_scientist_snapshot(snapshot: SnapshotAssertion):
    """Lock Payload Scientist output shape on canonical scene."""
    mock_response = json.dumps({
        "cloud_coverage_pct": 15.0,
        "image_quality": "GOOD",
        "land_cover": "AGRICULTURAL",
        "observation_value": 0.78,
        "features_observed": ["field patterns", "irrigation channels"],
        "confidence": 0.85,
        "reasoning": "Low cloud cover, clear agricultural patterns visible.",
    })
    with patch("amoa.llm._call_provider", new=AsyncMock(return_value=mock_response)):
        result = await run_payload_scientist(CANONICAL_SCENE)
    assert result.model_dump() == snapshot