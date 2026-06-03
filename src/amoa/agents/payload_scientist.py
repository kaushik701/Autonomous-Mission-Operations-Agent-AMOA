"""
Payload Scientist agent — Sentinel-2 imagery analysis.
Uses Gemini 2.5 Flash Vision via llm.py:structured_completion.
"""
from enum import StrEnum

from pydantic import BaseModel, Field

from amoa.llm import structured_completion


class ImageQuality(StrEnum):
    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    UNUSABLE = "UNUSABLE"


class LandCoverType(StrEnum):
    URBAN = "URBAN"
    AGRICULTURAL = "AGRICULTURAL"
    FOREST = "FOREST"
    COASTAL = "COASTAL"
    WATER = "WATER"
    BARREN = "BARREN"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class PayloadAssessment(BaseModel):
    """Output schema for Payload Scientist."""
    cloud_coverage_pct: float = Field(ge=0.0, le=100.0,
        description="Estimated cloud coverage percentage")
    image_quality: ImageQuality
    land_cover: LandCoverType
    observation_value: float = Field(ge=0.0, le=1.0,
        description="Scientific value of this scene 0-1")
    features_observed: list[str] = Field(
        description="Notable features detected in the scene")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="One sentence explaining the assessment")


SYSTEM_PROMPT = """You are the Payload Scientist, a satellite imagery analysis agent.

You receive Sentinel-2 multispectral imagery and must assess its scientific value
for mission planning.

Your job:
1. Estimate cloud coverage percentage (0-100).
2. Assess image quality: GOOD (clear, usable), DEGRADED (partial cloud/noise),
   UNUSABLE (fully obscured).
3. Identify dominant land cover type.
4. Rate observation value 0-1: how scientifically valuable is this scene?
5. List notable features observed.

Return ONLY valid JSON matching this schema. No markdown, no explanation outside the JSON:
{
  "cloud_coverage_pct": <float 0-100>,
  "image_quality": "GOOD" | "DEGRADED" | "UNUSABLE",
  "land_cover": "URBAN" | "AGRICULTURAL" | "FOREST" | "COASTAL" | "WATER"
               | "BARREN" | "MIXED" | "UNKNOWN",
  "observation_value": <float 0-1>,
  "features_observed": [<string>, ...],
  "confidence": <float 0-1>,
  "reasoning": "<one sentence>"
}"""


async def run_payload_scientist(scene: dict) -> PayloadAssessment:
    """
    Run Payload Scientist on a Sentinel-2 scene.

    Args:
        scene: Dict from sentinel_loader.load_scene()
                Must contain base64_image and filename.

    Returns:
        Validated PayloadAssessment.
    """
    user_message = f"""Analyze this Sentinel-2 satellite image.

Scene: {scene['filename']}
Original dimensions: {scene['original_width']}x{scene['original_height']} pixels
Band: {scene['band']}

Assess the scene and return your structured assessment."""

    return await structured_completion(
        system=SYSTEM_PROMPT,
        user=user_message,
        schema=PayloadAssessment,
        provider="gemini-vision",
        image_b64=scene["base64_image"],
    )