"""Shared LangGraph state schema."""
import operator
from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field

from amoa.agents.safety_pilot import SafetyAssessment
from amoa.agents.health_guard import HealthAssessment
from amoa.agents.payload_scientist import PayloadAssessment

class FailureEvent(BaseModel):
    """Structured failure record logged by agents and supervisor."""
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    agent: str
    error: str
    category: str # schema_violation, timeout, rate_limit, refusal, malformed_json
    recoverable: bool = True

class SupervisorDecision(BaseModel):
    """Final output from Conflict Resolver."""
    priority_action: str # continue, retry, abort, escalate
    reasoning: str
    confidence: float
    degraded_mode: bool = False

class HelloMessage(BaseModel):
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MissionState(BaseModel):
    """Top-level state shared across all agents."""
    scenario: str = "high_risk"
    messages: Annotated[list[HelloMessage], operator.add] = Field(default_factory=list)
    safety_assessment: SafetyAssessment | None = None
    health_assessment: HealthAssessment | None = None
    payload_assessment: PayloadAssessment | None = None
    supervisor_decision: SupervisorDecision | None = None
    failure_log: Annotated[list[FailureEvent], operator.add] = Field(default_factory=list)
    
