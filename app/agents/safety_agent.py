from __future__ import annotations

from app.core.config import settings
from app.models.taxonomy import CRITICAL_CLASSES


class SafetyAgent:
    def evaluate(self, predicted_class: str, confidence: float, safety_flags: list[str]) -> tuple[bool, str]:
        normalized_flags = {f.lower() for f in safety_flags}
        if predicted_class in CRITICAL_CLASSES:
            return True, "Critical incident class requires human triage."
        if confidence < settings.threshold_low_confidence:
            return True, "Low confidence classification requires supervisor review."
        if {"fire", "smoke", "brake_loss"} & normalized_flags:
            return True, "Safety flag indicates elevated risk."
        return False, ""
