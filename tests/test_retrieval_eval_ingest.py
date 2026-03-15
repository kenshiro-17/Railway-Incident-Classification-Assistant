from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.services.retrieval import HistoricalRetrievalStore


class RetrievalEvalIngestTest(unittest.TestCase):
    def test_ingest_eval_dataset_json_populates_rows(self) -> None:
        payload = {
            "version": "eval_dataset_v1",
            "scenarios": [
                {
                    "scenario_id": "SCN-0001",
                    "expected_class": "SMOKE_DETECTED",
                    "symptoms": "Smoke odor in coach B during braking.",
                },
                {
                    "scenario_id": "SCN-0002",
                    "expected_class": "DOOR_MALFUNCTION",
                    "symptoms": "Rear door failed to close at station.",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eval.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            store = HistoricalRetrievalStore()
            result = store.ingest_eval_dataset_json(str(path))

            self.assertEqual(result["added"], 2)
            self.assertEqual(result["rejected"], 0)
            self.assertEqual(len(store.rows), 2)
            self.assertEqual(store.rows[0].incident_id, "SCN-0001")


if __name__ == "__main__":
    unittest.main()
