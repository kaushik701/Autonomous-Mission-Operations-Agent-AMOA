"""
Safety Pilot agent — collision avoidance.

Reads CDM data, assesses conjunction risk, returns SafetyAssessment.
All LLM calls go through llm.py:structured_completion.
"""

from enum import StrEnum

from pydantic import BaseModel, Field

from amoa.llm import structured_completion

# ── Output Schema ──────────────────────────────────────────────────────────

class RiskLevel(StrEnum):
    LOW = "LOW"          # PC < 1e-6
    MEDIUM = "MEDIUM"    # 1e-6 <= PC < 1e-4
    HIGH = "HIGH"        # PC >= 1e-4


class RecommendedAction(StrEnum):
    MONITOR = "MONITOR"    # Watch and update as better tracking data arrives
    MANEUVER = "MANEUVER"  # Fire thrusters to increase miss distance


class SafetyAssessment(BaseModel):
    """Output schema for Safety Pilot. Validated by structured_completion."""
    pc: float = Field(description="Probability of collision from CDM")
    miss_distance_m: float = Field(description="Miss distance in meters")
    tca: str = Field(description="Time of closest approach, ISO format")
    sat1_name: str = Field(description="Primary satellite name")
    sat2_name: str = Field(description="Secondary object name")
    risk_level: RiskLevel = Field(description="LOW / MEDIUM / HIGH")
    recommended_action: RecommendedAction = Field(description="MONITOR or MANEUVER")
    confidence: float = Field(ge=0.0, le=1.0, description="Agent confidence 0-1")
    reasoning: str = Field(description="One sentence explaining the assessment")


# ── System Prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are the Safety Pilot, a collision avoidance agent for satellite mission operations.

You receive Conjunction Data Messages (CDMs) from NASA Space-Track describing predicted close
approaches between tracked objects in Earth orbit.

Your job:
1. Assess the conjunction risk based on probability of collision (PC) and miss distance.
2. Classify risk level using these thresholds:
   - LOW: PC < 1e-6 (routine, no concern)
   - MEDIUM: 1e-6 <= PC < 1e-4 (monitor closely)
   - HIGH: PC >= 1e-4 (consider maneuver immediately)
3. Recommend MONITOR or MANEUVER.
4. Express your confidence in the assessment (0.0 to 1.0).

Return ONLY valid JSON matching this schema. No markdown, no explanation outside the JSON:
{
  "pc": <float>,
  "miss_distance_m": <float>,
  "tca": "<ISO datetime string>",
  "sat1_name": "<string>",
  "sat2_name": "<string>",
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "recommended_action": "MONITOR" | "MANEUVER",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<one sentence>"
}"""


# ── Agent Function ─────────────────────────────────────────────────────────

async def run_safety_pilot(cdm: dict) -> SafetyAssessment:
    """
    Run the Safety Pilot agent on a CDM dict.

    Args:
        cdm: Dict with keys: pc, miss_distance_m, tca, sat1_name, sat2_name.

    Returns:
        Validated SafetyAssessment.
    """
    user_message = f"""Analyze this conjunction data message:

Probability of Collision (PC): {cdm['pc']}
Miss Distance: {cdm['miss_distance_m']} meters
Time of Closest Approach: {cdm['tca']}
Primary Object: {cdm['sat1_name']}
Secondary Object: {cdm['sat2_name']}

Assess the risk and return your structured assessment."""

    return await structured_completion(
        system=SYSTEM_PROMPT,
        user=user_message,
        schema=SafetyAssessment,
        provider="groq",
    )