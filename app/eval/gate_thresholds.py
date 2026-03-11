from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings


def main() -> None:
    report_path = Path("app/eval/benchmark_report_v1.json")
    if not report_path.exists():
        raise SystemExit("Missing benchmark report. Run benchmark.py first.")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    metrics = report["metrics"]

    checks = {
        "critical_recall": metrics["critical_recall"] >= settings.critical_recall_threshold,
        "top1_accuracy": metrics["top1_accuracy"] >= settings.top1_accuracy_threshold,
        "escalation_fnr": metrics["escalation_fnr"] <= settings.escalation_fnr_threshold,
        "p95_latency_seconds": metrics["p95_latency_seconds"] <= settings.p95_latency_threshold_seconds,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"Benchmark gate failed: {failed}")

    print("Benchmark gate passed.")


if __name__ == "__main__":
    main()
