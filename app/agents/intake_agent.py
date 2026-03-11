from __future__ import annotations

from app.models.schemas import IncidentInput


class IntakeAgent:
    def run(self, incident: IncidentInput) -> IncidentInput:
        incident.symptoms = incident.symptoms.strip().replace("\x00", "")
        incident.operator_actions_taken = incident.operator_actions_taken.strip().replace("\x00", "")
        incident.line_or_route = incident.line_or_route.strip()
        incident.train_type = incident.train_type.strip()
        return incident
