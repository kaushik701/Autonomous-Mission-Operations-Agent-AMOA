"""
Health Guard agent — telemetry anomaly detection.
Uses Gemini 2.5 Flash-Lite via llm.py:structured_completion.
"""
from enum import StrEnum

from pydantic import BaseModel, Field

from amoa.llm import structured_completion


class AnomalySeverity(StrEnum):
    NOMINAL = "NOMINAL"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class HealthAssessment(BaseModel):
    """Output schema for Health Guard."""
    anomaly_detected: bool
    severity: AnomalySeverity
    affected_channels: list[str] = Field(description="Channel names showing anomalous behavior")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="One sentence explaining the assessment")


SYSTEM_PROMPT = """You are Health Guard, a satellite telemetry anomaly detection agent.

You receive windows of satellite telemetry data and must assess whether an anomaly is present.

Severity levels:
- NOMINAL: No anomaly detected, all channels within expected ranges
- WATCH: Minor deviation, monitor closely
- WARNING: Significant anomaly, investigate immediately  
- CRITICAL: Severe anomaly, immediate action required

Return ONLY valid JSON matching this schema. No markdown, no explanation outside the JSON:
{
  "anomaly_detected": <bool>,
  "severity": "NOMINAL" | "WATCH" | "WARNING" | "CRITICAL",
  "affected_channels": [<string>, ...],
  "confidence": <float 0.0-1.0>,
  "reasoning": "<one sentence>"
}"""


async def run_health_guard(telemetry_window: dict) -> HealthAssessment:
    """
    Run Health Guard on a telemetry window.

    Args:
        telemetry_window: Dict with keys: values (list), channel_name (str)

    Returns:
        Validated HealthAssessment.
    """
    user_message = f"""Analyze this telemetry window:

Channel: {telemetry_window.get('channel_name', 'unknown')}
Window size: {len(telemetry_window['values'])} samples
Sample values (first 20): {telemetry_window['values'][:20]}
Is anomaly (ground truth label): {telemetry_window.get('is_anomaly', 'unknown')}

Assess whether this telemetry shows anomalous behavior."""

    return await structured_completion(
        system=SYSTEM_PROMPT,
        user=user_message,
        schema=HealthAssessment,
        provider="gemini",
    )