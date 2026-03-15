from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.eval.benchmark import evaluate


class BenchmarkPredictorModesTest(unittest.TestCase):
    def _write_dataset(self, path: Path) -> None:
        dataset = {
            "version": "eval_dataset_v1",
            "scenarios": [
                {
                    "scenario_id": "SCN-0001",
                    "timestamp": "2026-01-01T00:00:00",
                    "line_or_route": "Line-A",
                    "train_type": "EMU",
                    "language": "en",
                    "severity": "medium",
                    "expected_class": "DOOR_MALFUNCTION",
                    "symptoms": "Rear door failed to close.",
                    "safety_flags": [],
                },
                {
                    "scenario_id": "SCN-0002",
                    "timestamp": "2026-01-01T00:05:00",
                    "line_or_route": "Line-B",
                    "train_type": "EMU",
                    "language": "en",
                    "severity": "critical",
                    "expected_class": "SMOKE_DETECTED",
                    "symptoms": "Smoke odor in coach B.",
                    "safety_flags": ["smoke"],
                },
            ],
        }
        path.write_text(json.dumps(dataset), encoding="utf-8")

    def test_mock_predictor_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset_path = Path(tmp) / "eval.json"
            self._write_dataset(dataset_path)
            report = evaluate(dataset_path, predictor="mock")
            self.assertEqual(report["predictor"], "mock")
            self.assertEqual(report["total_scenarios"], 2)
            self.assertGreaterEqual(report["metrics"]["top1_accuracy"], 1.0)

    def test_live_predictor_path_with_stubbed_model(self) -> None:
        async def fake_classify(*args, **kwargs):  # type: ignore[no-untyped-def]
            return {
                "predicted_class": "DOOR_MALFUNCTION",
                "confidence": 0.91,
                "clarifying_questions": [],
                "suggested_next_steps": [],
                "reasoning_summary": "stub",
            }

        with tempfile.TemporaryDirectory() as tmp:
            dataset_path = Path(tmp) / "eval.json"
            self._write_dataset(dataset_path)
            with patch("app.eval.benchmark.ClassificationAgent.classify", new=fake_classify):
                report = evaluate(dataset_path, predictor="live")
            self.assertEqual(report["predictor"], "live")
            self.assertEqual(report["total_scenarios"], 2)
            self.assertIn("p95_latency_seconds", report["metrics"])


if __name__ == "__main__":
    unittest.main()
