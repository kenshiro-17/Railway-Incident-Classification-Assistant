from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Railway Incident Classification Assistant"
    environment: str = "dev"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_endpoint: str = "https://generativelanguage.googleapis.com/v1beta/models"
    prompt_template_version: str = "v1.0.0"

    threshold_low_confidence: float = 0.65
    max_clarification_turns: int = 2

    burst_window_seconds: int = 60
    burst_limit_per_user: int = 20
    burst_limit_per_ip: int = 40
    burst_limit_global: int = 500

    sustained_window_seconds: int = 3600
    sustained_limit_per_user: int = 300
    sustained_limit_per_ip: int = 600
    sustained_limit_global: int = 10000

    audit_log_path: str = "app/data/audit.log"
    raw_retention_days: int = 7
    structured_retention_days: int = 90

    sso_mode: str = "stub"  # stub | jwt
    sso_jwks_url: str = ""
    sso_issuer: str = ""
    sso_audience: str = ""
    sso_user_claim: str = "sub"
    sso_role_claim: str = "role"
    require_jwt_in_prod: bool = True

    allowed_origins: str = "http://localhost:8000"
    trusted_hosts: str = "localhost,127.0.0.1"
    max_request_bytes: int = 65536

    critical_recall_threshold: float = 0.95
    top1_accuracy_threshold: float = 0.80
    escalation_fnr_threshold: float = 0.02
    p95_latency_threshold_seconds: float = 5.0

    ddos_block_after_violations: int = 25
    ddos_block_window_seconds: int = 300
    ddos_block_duration_seconds: int = 900
    prompt_injection_strict_mode: bool = True
    prompt_injection_max_attempts: int = 3
    prompt_injection_window_seconds: int = 600
    prompt_injection_quarantine_seconds: int = 1800
    redis_url: str = ""
    state_ttl_seconds: int = 7200
    bootstrap_retrieval_from_eval_dataset: bool = True
    retrieval_eval_dataset_path: str = "app/eval/eval_dataset_v1.json"

    gemini_fail_closed_in_prod: bool = True
    fallback_provider_enabled: bool = True
    gemini_timeout_seconds: float = 25.0

    internal_api_token: str = ""
    require_mtls_for_internal: bool = False
    mtls_verified_header: str = "X-Client-Cert-Verified"

    ip_blocklist_path: str = "app/data/ip_blocklist.txt"
    waf_enabled: bool = True

    otel_enabled: bool = False
    otel_service_name: str = "ria-assistant"
    otel_exporter_otlp_endpoint: str = ""
    audit_signing_key: str = ""
    secrets_encryption_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="RIA_")


settings = Settings()
