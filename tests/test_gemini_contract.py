from __future__ import annotations

import unittest

from app.services.gemini import HeuristicFallbackProvider, normalize_model_response


class GeminiContractTest(unittest.IsolatedAsyncioTestCase):
    async def test_fallback_provider_returns_contract_shape(self) -> None:
        provider = HeuristicFallbackProvider()
        raw = await provider.generate_json("brake pressure dropped near station")
        normalized = normalize_model_response(raw)
        self.assertIn("predicted_class", normalized)
        self.assertIn("confidence", normalized)
        self.assertIsInstance(normalized["clarifying_questions"], list)
        self.assertIsInstance(normalized["suggested_next_steps"], list)

    def test_normalize_handles_schema_drift(self) -> None:
        raw = {"predicted_class": "NOT_A_CLASS", "confidence": "1.4", "clarifying_questions": "bad"}
        normalized = normalize_model_response(raw)
        self.assertEqual(normalized["predicted_class"], "UNKNOWN_MECHANICAL_NOISE")
        self.assertEqual(normalized["confidence"], 1.0)
        self.assertEqual(normalized["clarifying_questions"], [])


if __name__ == "__main__":
    unittest.main()
