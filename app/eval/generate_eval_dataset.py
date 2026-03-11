from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from app.models.taxonomy import INCIDENT_CLASSES

SEVERITY = ["low", "medium", "high", "critical"]
ROUTES = ["Line-A", "Line-B", "Intercity-7", "Depot-3", "Cargo-12"]
TRAINS = ["EMU", "DMU", "Freight", "Regional", "HighSpeed"]

COMMON_WORDS = {
    "en": ["intermittent", "warning", "noise", "fault", "reset", "indicator", "temperature", "pressure"],
    "de": ["Stoerung", "Warnung", "Geraeusch", "Fehler", "Reset", "Anzeige", "Temperatur", "Druck"]
}


def make_scenario(i: int, language: str, class_label: str) -> dict:
    base_dt = datetime(2026, 1, 1) + timedelta(minutes=i * 5)
    words = random.sample(COMMON_WORDS[language], 4)  # nosec B311
    severe = i % 2 == 0
    safety_flags = ["smoke"] if class_label in {"ONBOARD_FIRE_ALERT", "SMOKE_DETECTED"} else []

    return {
        "scenario_id": f"SCN-{i:04d}",
        "timestamp": base_dt.isoformat(),
        "line_or_route": random.choice(ROUTES),  # nosec B311
        "train_type": random.choice(TRAINS),  # nosec B311
        "language": language,
        "severity": "critical" if severe else random.choice(SEVERITY[:-1]),  # nosec B311
        "expected_class": class_label,
        "symptoms": f"{words[0]} {words[1]} observed with {words[2]} and {words[3]} during operation.",
        "required_clarifying_questions": [
            "What happened immediately before the fault?",
            "What operator actions were taken?"
        ],
        "safety_flags": safety_flags,
        "case_type": random.choice(["common", "rare", "ambiguous", "multi_fault", "contradictory", "missing_info"])  # nosec B311
    }


def main() -> None:
    random.seed(42)
    target = 600
    scenarios = []
    for i in range(target):
        lang = "en" if i % 3 else "de"
        cls = INCIDENT_CLASSES[i % len(INCIDENT_CLASSES)]
        scenarios.append(make_scenario(i=i + 1, language=lang, class_label=cls))

    out_dir = Path("app/eval")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "eval_dataset_v1.json"
    out_file.write_text(json.dumps({"version": "eval_dataset_v1", "scenarios": scenarios}, indent=2), encoding="utf-8")
    print(f"Generated {target} scenarios at {out_file}")


if __name__ == "__main__":
    main()
