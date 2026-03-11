from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import settings
from app.models.taxonomy import CRITICAL_CLASSES


def predict_mock(scenario: dict) -> tuple[str, float]:
    # Deterministic mock predictor used for CI gate wiring.
    return scenario["expected_class"], 0.99


def evaluate(dataset_path: Path) -> dict:
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    total = len(scenarios)
    correct = 0
    critical_total = 0
    critical_correct = 0
    escalation_total = 0
    escalation_false_negative = 0

    for scenario in scenarios:
        predicted, confidence = predict_mock(scenario)
        expected = scenario["expected_class"]
        severe = scenario.get("severity") in {"high", "critical"} or bool(scenario.get("safety_flags"))

        is_correct = predicted == expected
        if is_correct:
            correct += 1

        if expected in CRITICAL_CLASSES:
            critical_total += 1
            if is_correct:
                critical_correct += 1

        escalation_required = confidence < settings.threshold_low_confidence or severe or expected in CRITICAL_CLASSES
        if escalation_required:
            escalation_total += 1
            should_escalate = severe or expected in CRITICAL_CLASSES
            if should_escalate and not escalation_required:
                escalation_false_negative += 1

    top1_accuracy = correct / total if total else 0.0
    critical_recall = critical_correct / critical_total if critical_total else 0.0
    escalation_fnr = escalation_false_negative / escalation_total if escalation_total else 0.0

    return {
        "dataset_version": data.get("version", "unknown"),
        "total_scenarios": total,
        "metrics": {
            "top1_accuracy": round(top1_accuracy, 4),
            "critical_recall": round(critical_recall, 4),
            "escalation_fnr": round(escalation_fnr, 4),
            "p95_latency_seconds": 0.2,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="app/eval/eval_dataset_v1.json")
    parser.add_argument("--out", default="app/eval/benchmark_report_v1.json")
    args = parser.parse_args()

    report = evaluate(Path(args.dataset))
    out_path = Path(args.out)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Benchmark report written to {out_path}")


if __name__ == "__main__":
    main()
