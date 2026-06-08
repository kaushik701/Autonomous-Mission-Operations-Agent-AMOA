"""
Conflict Resolver — hybrid rule+LLM decision making.
Rules handle clear cases. LLM handles ambiguous ones.
Receives full MissionState including failure_log.
"""
from pydantic import BaseModel, Field
from amoa.llm import structured_completion
from amoa.state import MissionState, SupervisorDecision


RESOLVER_SYSTEM_PROMPT = """You are the Conflict Resolver for a satellite mission operations system.

You receive assessments from three specialized agents:
- Safety Pilot: collision avoidance (HIGH/MEDIUM/LOW risk)
- Health Guard: telemetry anomaly detection (CRITICAL/WARNING/WATCH/NOMINAL)
- Payload Scientist: imagery analysis (observation value 0-1)

You also receive a failure log showing which agents failed or returned incomplete data.

Rules (apply these first, before reasoning):
1. If Safety Pilot is HIGH risk → priority_action must be MANEUVER, no exceptions.
2. If Health Guard is CRITICAL → priority_action must be SAFE_MODE.
3. If both Safety and Health are degraded (in failure_log) → priority_action must be GROUND_CONTACT.

For all other cases, reason about the tradeoffs and recommend the best action.

Valid actions: MANEUVER, SAFE_MODE, GROUND_CONTACT, NOMINAL_OPS, DEFER_PAYLOAD

Return ONLY valid JSON:
{
  "priority_action": "<action>",
  "reasoning": "<one sentence>",
  "confidence": <float 0-1>,
  "degraded_mode": <bool>
}"""


async def run_conflict_resolver(state: MissionState) -> SupervisorDecision:
    """
    Hybrid resolver: rules first, LLM for ambiguous cases.
    """
    degraded = len(state.failure_log) > 0

    # Rule 1: Safety HIGH always wins
    if (state.safety_assessment and
            state.safety_assessment.risk_level.value == "HIGH"):
        return SupervisorDecision(
            priority_action="MANEUVER",
            reasoning="Hard rule: Safety Pilot HIGH risk overrides all other concerns.",
            confidence=1.0,
            degraded_mode=degraded,
        )

    # Rule 2: Health CRITICAL → safe mode
    if (state.health_assessment and
            state.health_assessment.severity.value == "CRITICAL"):
        return SupervisorDecision(
            priority_action="SAFE_MODE",
            reasoning="Hard rule: CRITICAL telemetry anomaly requires safe mode.",
            confidence=1.0,
            degraded_mode=degraded,
        )

    # Rule 3: Both safety and health failed → ground contact
    failed_agents = {f.agent for f in state.failure_log}
    if "safety_pilot" in failed_agents and "health_guard" in failed_agents:
        return SupervisorDecision(
            priority_action="GROUND_CONTACT",
            reasoning="Hard rule: cannot operate safely without Safety and Health data.",
            confidence=1.0,
            degraded_mode=True,
        )

    # LLM handles ambiguous cases
    context = f"""
Safety assessment: {state.safety_assessment.model_dump() if state.safety_assessment else 'UNAVAILABLE'}
Health assessment: {state.health_assessment.model_dump() if state.health_assessment else 'UNAVAILABLE'}
Payload assessment: {state.payload_assessment.model_dump() if state.payload_assessment else 'UNAVAILABLE'}
Failure log: {[f.model_dump() for f in state.failure_log]}
"""
    return await structured_completion(
        system=RESOLVER_SYSTEM_PROMPT,
        user=f"Resolve the current mission state:{context}",
        schema=SupervisorDecision,
        provider="groq",
    )