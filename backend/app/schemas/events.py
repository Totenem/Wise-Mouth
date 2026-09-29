"""Shared contracts. Mirrored in frontend/lib/types.ts - change both together."""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class SignalType(str, Enum):
    uncertainty = "uncertainty"
    hedging = "hedging"
    commitment = "commitment"
    commitment_change = "commitment_change"
    repeated_concern = "repeated_concern"
    disagreement = "disagreement"
    unanswered_question = "unanswered_question"


class Utterance(BaseModel):
    id: str
    room: str
    speaker: str
    text: str
    start_ms: int
    is_final: bool = True


class Ref(BaseModel):
    speaker: str
    text: str
    timestamp_ms: int


class Signal(BaseModel):
    id: str
    type: SignalType
    speaker: str
    evidence: str
    timestamp_ms: int
    confidence: float
    summary: str = ""
    topic: str | None = None
    related: Ref | None = None
    status: Literal["active", "resolved"] = "active"
    count: int = 1
    participants: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
