from __future__ import annotations

from typing import List

from app.models.schemas import IncidentInput


class QuestioningAgent:
    def missing_questions(self, incident: IncidentInput) -> List[str]:
        questions: List[str] = []
        if len(incident.symptoms.strip()) < 25:
            questions.append("Can you describe the sequence of events and fault indicators in more detail?")
        if not incident.operator_actions_taken:
            questions.append("What actions have already been taken by the operator or crew?")
        if not incident.safety_flags:
            questions.append("Were there any immediate safety risks such as smoke, fire, or brake loss?")
        return questions
