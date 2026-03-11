from __future__ import annotations

import unittest
from pathlib import Path

from app.eval.generate_eval_dataset import main as generate
from app.eval.qa_eval_dataset import run_checks


class EvalDatasetTest(unittest.TestCase):
    def test_eval_dataset_generation_and_qa(self) -> None:
        generate()
        report = run_checks(Path("app/eval/eval_dataset_v1.json"))
        self.assertGreaterEqual(report["total"], 500)


if __name__ == "__main__":
    unittest.main()
