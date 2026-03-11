from __future__ import annotations

import unittest

from app.agents.safety_agent import SafetyAgent


class SafetyTest(unittest.TestCase):
    def test_safety_escalates_on_critical_class(self) -> None:
        agent = SafetyAgent()
        escalated, reason = agent.evaluate("ONBOARD_FIRE_ALERT", 0.95, [])
        self.assertTrue(escalated)
        self.assertIn("Critical", reason)

    def test_safety_escalates_on_low_confidence(self) -> None:
        agent = SafetyAgent()
        escalated, _ = agent.evaluate("DOOR_MALFUNCTION", 0.2, [])
        self.assertTrue(escalated)


if __name__ == "__main__":
    unittest.main()
