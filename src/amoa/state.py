"""Shared LangGraph state schema. Grows weekly.

W0: hello-world placeholder.
W1-W4: agent assessments added incrementally.
"""
import operator
from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field


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
