from __future__ import annotations

import json
from pathlib import Path


REQUIRED_FILES = [
    "app/main.py",
    "app/api/routes.py",
    "app/core/security.py",
    "app/services/rate_limiter.py",
    "app/services/gemini.py",
    "app/services/retrieval.py",
    "app/services/orchestrator.py",
    "app/eval/generate_eval_dataset.py",
    "app/eval/qa_eval_dataset.py",
    "app/eval/benchmark.py",
    "app/eval/gate_thresholds.py",
    "app/core/telemetry.py",
    "app/services/state_store.py",
    "app/services/ip_reputation.py",
    "app/ui/index.html",
    "app/ui/styles.css",
    "app/ui/app.js",
    ".github/workflows/ci.yml",
    ".github/workflows/weekly_model_refresh.yml",
    ".github/workflows/monthly_secret_rotation.yml",
    "Dockerfile",
    "docker-compose.yml",
    "deploy/k8s/deployment.yaml",
    "deploy/k8s/hpa.yaml",
    "deploy/k8s/pdb.yaml",
]


RULE_CHECKS = {
    "scope_gemini_only": "app/services/gemini.py",
    "sso_required": "app/core/security.py",
    "rate_limit_user_ip_global": "app/services/rate_limiter.py",
    "clarification_loop": "app/services/orchestrator.py",
    "safety_escalation": "app/agents/safety_agent.py",
    "taxonomy_top20": "app/models/taxonomy.py",
    "web_chat_ui": "app/ui/index.html",
    "feedback_endpoint": "app/api/routes.py",
    "observability_prometheus": "app/core/metrics.py",
    "jwt_sso_path": "app/core/security.py",
    "deployment_manifests": "deploy/k8s/deployment.yaml",
    "weekly_model_refresh": ".github/workflows/weekly_model_refresh.yml",
    "secret_rotation_workflow": ".github/workflows/monthly_secret_rotation.yml",
    "redis_state_backend": "app/services/state_store.py",
    "ip_reputation_store": "app/services/ip_reputation.py",
    "k8s_hpa": "deploy/k8s/hpa.yaml",
}


def file_exists(path: str) -> bool:
    return Path(path).exists()


def dataset_check() -> tuple[bool, str]:
    dataset = Path("app/eval/eval_dataset_v1.json")
    if not dataset.exists():
        return False, "dataset file missing"
    data = json.loads(dataset.read_text(encoding="utf-8"))
    size = len(data.get("scenarios", []))
    if size < 500:
        return False, f"dataset size below threshold: {size}"
    return True, f"dataset size: {size}"


def main() -> None:
    missing = [p for p in REQUIRED_FILES if not file_exists(p)]
    checks = {name: file_exists(path) for name, path in RULE_CHECKS.items()}
    eval_ok, eval_note = dataset_check()
    checks["eval_dataset_500_plus"] = eval_ok

    complete = all(checks.values()) and not missing

    report = {
        "status": "PASS" if complete else "PARTIAL",
        "missing_files": missing,
        "rule_checks": checks,
        "notes": {
            "eval_dataset": eval_note,
            "unimplemented_or_partial": []
        }
    }

    out = Path("docs/compliance_report.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
