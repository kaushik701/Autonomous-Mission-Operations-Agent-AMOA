"""Shared LangGraph state schema. Grows weekly.

W0: hello-world placeholder.
W1-W4: agent assessments added incrementally.
"""
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
    """W0 placeholder — replaced in W1."""
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MissionState(BaseModel):
    """Top-level state shared across agents.

    Field growth schedule:
    - W0: messages only
    - W1: + safety_assessment
    - W2: + health_assessment
    - W3: + payload_assessment
    - W4: + supervisor_decision, failure_log
    """
    messages: Annotated[list[HelloMessage], operator.add] = Field(default_factory=list)
    safety_assessment: SafetyAssessment | None = None
    health_assessment: HealthAssessment | None = None
    payload_assessment: PayloadAssessment | None = None
    supervisor_decision: SupervisorDecision | None = None
    failure_log: Annotated[list[FailureEvent], operator.add] = Field(default_factory=list)
    
