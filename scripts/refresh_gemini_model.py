from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
PREFERRED_MODEL_ORDER = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-pro",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
]


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def write_env(path: Path, key: str, value: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    found = False
    updated: list[str] = []
    for line in lines:
        if line.startswith(key + "="):
            updated.append(f"{key}={value}")
            found = True
        else:
            updated.append(line)
    if not found:
        updated.append(f"{key}={value}")
    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def fetch_generate_models(api_key: str) -> list[str]:
    params = {"key": api_key}
    with httpx.Client(timeout=20.0) as client:
        response = client.get(GEMINI_API_BASE, params=params)
        response.raise_for_status()
        body = response.json()

    models = []
    for item in body.get("models", []):
        methods = set(item.get("supportedGenerationMethods", []))
        if "generateContent" not in methods:
            continue
        name = str(item.get("name", ""))
        # model names are usually "models/<id>"
        model_id = name.split("/", 1)[1] if "/" in name else name
        if model_id:
            models.append(model_id)
    return sorted(set(models))


def choose_model(current: str, available: list[str]) -> tuple[str, str]:
    if current in available:
        return current, "current_model_supported"
    for preferred in PREFERRED_MODEL_ORDER:
        if preferred in available:
            return preferred, "switched_to_preferred_supported"
    if available:
        return available[0], "switched_to_first_supported"
    return current, "no_supported_models_found"


def main() -> None:
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    values = load_env(env_path)

    api_key = os.getenv("RIA_GEMINI_API_KEY", values.get("RIA_GEMINI_API_KEY", ""))
    if not api_key or api_key == "REPLACE_WITH_REAL_KEY":
        raise SystemExit("Missing RIA_GEMINI_API_KEY. Set it in environment or .env.")

    current_model = os.getenv("RIA_GEMINI_MODEL", values.get("RIA_GEMINI_MODEL", "gemini-2.0-flash"))
    available = fetch_generate_models(api_key=api_key)
    selected, reason = choose_model(current=current_model, available=available)

    changed = selected != current_model
    if changed:
        if env_path.exists():
            write_env(env_path, "RIA_GEMINI_MODEL", selected)
        if env_example_path.exists():
            write_env(env_example_path, "RIA_GEMINI_MODEL", selected)

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "current_model": current_model,
        "selected_model": selected,
        "changed": changed,
        "reason": reason,
        "available_count": len(available),
    }

    report_path = Path("app/data/model_update_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
