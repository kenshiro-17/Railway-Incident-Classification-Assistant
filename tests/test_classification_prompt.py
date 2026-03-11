from __future__ import annotations

import unittest
from datetime import UTC, datetime

from app.agents.classification_agent import ClassificationAgent
from app.models.schemas import IncidentInput


class ClassificationPromptTest(unittest.TestCase):
    def test_prompt_contains_system_rules_and_context(self) -> None:
        agent = ClassificationAgent()
        incident = IncidentInput(
            timestamp=datetime.now(UTC),
            line_or_route="Line-A",
            train_type="EMU",
            symptoms="Door fault after departure",
            operator_actions_taken="Attempted reset",
            language="en",
        )
        prompt = agent.build_prompt(
            incident=incident,
            user_message="classify this",
            session_context="Turn 1: previous door event",
        )
        self.assertIn("Non-negotiable rules", prompt)
        self.assertIn("Session context", prompt)
        self.assertIn("Allowed classes only", prompt)


if __name__ == "__main__":
    unittest.main()
