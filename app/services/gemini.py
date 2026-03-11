from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Protocol

import httpx

from app.core.config import settings
from app.models.taxonomy import INCIDENT_CLASSES


class ModelProvider(Protocol):
    async def generate_json(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        ...


@dataclass
class ClassificationOutput:
    predicted_class: str
    confidence: float
    clarifying_questions: list[str]
    suggested_next_steps: list[str]
    reasoning_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicted_class": self.predicted_class,
            "confidence": self.confidence,
            "clarifying_questions": self.clarifying_questions,
            "suggested_next_steps": self.suggested_next_steps,
            "reasoning_summary": self.reasoning_summary,
        }


def normalize_model_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    predicted = str(raw.get("predicted_class", "UNKNOWN_MECHANICAL_NOISE"))
    if predicted not in INCIDENT_CLASSES:
        predicted = "UNKNOWN_MECHANICAL_NOISE"
    try:
        confidence = float(raw.get("confidence", 0.0))
    except Exception:
        confidence = 0.0
    questions = raw.get("clarifying_questions", [])
    steps = raw.get("suggested_next_steps", [])
    return {
        "predicted_class": predicted,
        "confidence": max(0.0, min(1.0, confidence)),
        "clarifying_questions": list(questions) if isinstance(questions, list) else [],
        "suggested_next_steps": list(steps) if isinstance(steps, list) else [],
        "reasoning_summary": str(raw.get("reasoning_summary", "")),
    }


class HeuristicFallbackProvider:
    """Provider-agnostic fallback model used when external LLM is unavailable."""

    KEYWORDS = {
        "BRAKE_SYSTEM_FAILURE": ["brake", "pressure", "deceleration"],
        "DOOR_MALFUNCTION": ["door", "closing", "opening"],
        "SMOKE_DETECTED": ["smoke", "odor", "burning"],
        "ONBOARD_FIRE_ALERT": ["fire", "flame", "combustion"],
        "TRACTION_POWER_LOSS": ["power", "traction", "voltage"],
    }

    async def generate_json(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        lowered = prompt.lower()
        predicted = "UNKNOWN_MECHANICAL_NOISE"
        confidence = 0.55
        for label, words in self.KEYWORDS.items():
            if any(word in lowered for word in words):
                predicted = label
                confidence = 0.7
                break
        return ClassificationOutput(
            predicted_class=predicted if predicted in INCIDENT_CLASSES else "UNKNOWN_MECHANICAL_NOISE",
            confidence=confidence,
            clarifying_questions=["Please confirm fault timeline, subsystem alarms, and safety observations."],
            suggested_next_steps=[
                "Use conservative safety protocol and collect diagnostic logs.",
                "Escalate to supervisor if risk indicators are present."
            ],
            reasoning_summary="Fallback provider used due to external model unavailability.",
        ).to_dict()


class GeminiProvider:
    def __init__(self) -> None:
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.endpoint = f"{settings.gemini_endpoint}/{self.model}:generateContent"

    async def generate_json(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Gemini API key is not configured")
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "responseMimeType": "application/json"},
        }
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        async with httpx.AsyncClient(timeout=settings.gemini_timeout_seconds) as client:
            response = await client.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
        text = (
            body.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "{}")
        )
        return normalize_model_response(json.loads(text))


class ProviderRouter:
    def __init__(self) -> None:
        self.primary: ModelProvider = GeminiProvider()
        self.fallback: ModelProvider = HeuristicFallbackProvider()

    async def generate_json(self, prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        try:
            return await self.primary.generate_json(prompt=prompt, temperature=temperature)
        except Exception as exc:
            if settings.environment.lower() == "prod" and settings.gemini_fail_closed_in_prod and not settings.fallback_provider_enabled:
                raise RuntimeError("Primary model unavailable and fallback disabled in production") from exc
            if settings.fallback_provider_enabled:
                return normalize_model_response(await self.fallback.generate_json(prompt=prompt, temperature=temperature))
            raise


model_provider = ProviderRouter()
