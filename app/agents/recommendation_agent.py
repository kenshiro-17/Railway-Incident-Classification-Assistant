from __future__ import annotations

from typing import List

from app.models.schemas import SimilarIncident


class RecommendationAgent:
    def run(self, predicted_class: str, similar: List[SimilarIncident], model_steps: List[str]) -> List[str]:
        steps = list(model_steps)
        if similar:
            steps.append(f"Review prior resolution pattern from incident {similar[0].incident_id} before dispatch.")
        if predicted_class in {"ONBOARD_FIRE_ALERT", "SMOKE_DETECTED"}:
            steps.insert(0, "Apply emergency safety protocol and alert control center immediately.")
        if not steps:
            steps = ["Escalate to supervisor and collect additional diagnostic logs."]
        return steps[:5]
