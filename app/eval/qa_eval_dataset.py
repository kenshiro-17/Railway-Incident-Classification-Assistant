from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from app.models.taxonomy import INCIDENT_CLASSES


class EvalQAFailure(Exception):
    pass


def run_checks(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]

    if len(scenarios) < 500:
        raise EvalQAFailure("Dataset must contain at least 500 scenarios")

    ids = [s["scenario_id"] for s in scenarios]
    if len(set(ids)) != len(ids):
        raise EvalQAFailure("Duplicate scenario_id detected")

    class_counts = Counter(s["expected_class"] for s in scenarios)
    missing = [c for c in INCIDENT_CLASSES if c not in class_counts]
    if missing:
        raise EvalQAFailure(f"Missing class coverage: {missing}")

    if min(class_counts.values()) < 10:
        raise EvalQAFailure("Class balance floor not met (min per class < 10)")

    lang_counts = Counter(s["language"] for s in scenarios)
    if lang_counts.get("en", 0) < 100 or lang_counts.get("de", 0) < 100:
        raise EvalQAFailure("EN/DE minimum coverage not met")

    severe = Counter(s["severity"] for s in scenarios)
    return {
        "total": len(scenarios),
        "class_counts": class_counts,
        "language_counts": lang_counts,
        "severity_counts": severe
    }


def main() -> None:
    path = Path("app/eval/eval_dataset_v1.json")
    if not path.exists():
        raise SystemExit("Dataset missing. Run generate_eval_dataset.py first.")
    report = run_checks(path)
    report_path = Path("app/eval/eval_dataset_v1_qa_report.json")
    report_path.write_text(json.dumps({k: dict(v) if hasattr(v, "items") else v for k, v in report.items()}, indent=2), encoding="utf-8")
    print(f"QA passed. Report written to {report_path}")


if __name__ == "__main__":
    main()
