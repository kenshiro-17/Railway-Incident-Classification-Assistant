from __future__ import annotations

import argparse
import asyncio
import json
import math
import time
from pathlib import Path

from app.agents.classification_agent import ClassificationAgent
from app.core.config import settings
from app.models.schemas import IncidentInput
from app.models.taxonomy import CRITICAL_CLASSES


def predict_mock(scenario: dict) -> tuple[str, float]:
    # Deterministic mock predictor used for CI gate wiring.
    return scenario["expected_class"], 0.99


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1))
    return ordered[idx]


def _scenario_to_incident(scenario: dict) -> IncidentInput:
    scenario_id = str(scenario.get("scenario_id", "")).strip() or "benchmark-scenario"
    return IncidentInput(
        incident_id=scenario_id,
        timestamp=scenario["timestamp"],
        line_or_route=str(scenario.get("line_or_route", "unknown-route")),
        train_type=str(scenario.get("train_type", "unknown-train")),
        symptoms=str(scenario.get("symptoms", "")),
        operator_actions_taken=str(scenario.get("operator_actions_taken", "")),
        safety_flags=list(scenario.get("safety_flags", [])),
        language=str(scenario.get("language", "en")),
    )


async def _predict_live(agent: ClassificationAgent, scenario: dict) -> tuple[str, float, float]:
    incident = _scenario_to_incident(scenario)
    start = time.perf_counter()
    output = await agent.classify(
        incident=incident,
        user_message=incident.symptoms,
        session_context="No prior session context.",
    )
    latency = time.perf_counter() - start
    predicted = str(output.get("predicted_class", "UNKNOWN_MECHANICAL_NOISE"))
    confidence = float(output.get("confidence", 0.0))
    return predicted, confidence, latency


async def _run_live_predictions(scenarios: list[dict]) -> tuple[list[tuple[str, float]], list[float]]:
    agent = ClassificationAgent()
    predictions: list[tuple[str, float]] = []
    latencies: list[float] = []
    for scenario in scenarios:
        predicted, confidence, latency = await _predict_live(agent, scenario)
        predictions.append((predicted, confidence))
        latencies.append(latency)
    return predictions, latencies


def _resolve_predictor_mode(predictor: str) -> str:
    if predictor in {"live", "mock"}:
        return predictor
    return "live" if settings.gemini_api_key else "mock"


def evaluate(dataset_path: Path, predictor: str = "auto") -> dict:
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    predictor_mode = _resolve_predictor_mode(predictor)
    if predictor_mode == "live":
        predictions, latencies = asyncio.run(_run_live_predictions(scenarios))
    else:
        predictions = [predict_mock(s) for s in scenarios]
        latencies = [0.2] * len(scenarios)

    total = len(scenarios)
    correct = 0
    critical_total = 0
    critical_correct = 0
    escalation_total = 0
    escalation_false_negative = 0

    for scenario, (predicted, confidence) in zip(scenarios, predictions):
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
    p95_latency_seconds = _p95(latencies)

    return {
        "dataset_version": data.get("version", "unknown"),
        "total_scenarios": total,
        "predictor": predictor_mode,
        "metrics": {
            "top1_accuracy": round(top1_accuracy, 4),
            "critical_recall": round(critical_recall, 4),
            "escalation_fnr": round(escalation_fnr, 4),
            "p95_latency_seconds": round(p95_latency_seconds, 4),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="app/eval/eval_dataset_v1.json")
    parser.add_argument("--out", default="app/eval/benchmark_report_v1.json")
    parser.add_argument("--predictor", choices=["auto", "live", "mock"], default="auto")
    args = parser.parse_args()

    report = evaluate(Path(args.dataset), predictor=args.predictor)
    out_path = Path(args.out)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Benchmark report written to {out_path}")


if __name__ == "__main__":
    main()
