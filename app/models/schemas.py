from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.models.taxonomy import INCIDENT_CLASSES, TAXONOMY_VERSION


class IncidentInput(BaseModel):
    incident_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime
    line_or_route: str = Field(min_length=1, max_length=120)
    train_type: str = Field(min_length=1, max_length=80)
    symptoms: str = Field(min_length=3, max_length=4000)
    operator_actions_taken: str = Field(default="", max_length=2000)
    safety_flags: List[str] = Field(default_factory=list)
    language: str = Field(default="en")
    attachments_ref: Optional[str] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in {"en", "de"}:
            raise ValueError("language must be en or de")
        return value


class ChatSessionCreate(BaseModel):
    locale: str = "en"


class ChatMessageRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=128)
    incident: IncidentInput
    user_message: str = Field(min_length=1, max_length=3000)
    clarification_turn: int = 0


class SimilarIncident(BaseModel):
    incident_id: str
    class_label: str
    similarity: float
    summary: str


class ChatResponse(BaseModel):
    clarifying_questions: List[str] = Field(default_factory=list)
    predicted_class: str = "UNCLASSIFIED"
    confidence: float = 0.0
    similar_incidents: List[SimilarIncident] = Field(default_factory=list)
    suggested_next_steps: List[str] = Field(default_factory=list)
    escalation_required: bool = False
    escalation_reason: str = ""
    evidence_refs: List[str] = Field(default_factory=list)
    trace_id: str
    taxonomy_version: str = TAXONOMY_VERSION


class ClassifyRequest(BaseModel):
    incident: IncidentInput


class FeedbackRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=128)
    incident_id: str = Field(min_length=8, max_length=128)
    is_correct: bool
    corrected_label: Optional[str] = None
    comment: str = Field(default="", max_length=1000)

    @field_validator("corrected_label")
    @classmethod
    def validate_corrected_label(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in INCIDENT_CLASSES:
            raise ValueError("corrected_label must be in taxonomy")
        return value


class ErrorResponse(BaseModel):
    detail: str
    trace_id: str
