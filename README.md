# Railway Incident Classification Assistant

Production-oriented incident triage and classification assistant for railway operations teams.

The system ingests structured incident reports, asks key clarifying questions, classifies failures, compares against historical incidents, and returns evidence-linked next steps with safety-first escalation behavior.

## Core Capabilities

- Chat-based incident triage for operations/maintenance teams
- Top-20 controlled incident taxonomy classification
- Clarification loop for incomplete reports
- Historical similarity retrieval from CSV/XLSX datasets
- Strict safety escalation policy for critical/low-confidence cases
- Prompt-injection detection and strict session quarantine mode
- Multi-layer rate limiting (user/IP/global, burst+sustained)
- Optional provider-agnostic fallback model if Gemini is unavailable
- Security-first middleware (WAF signatures, size limits, hardened headers)

## Architecture

- Backend: FastAPI (`app/`)
- LLM Provider Layer: Gemini + provider abstraction fallback (`app/services/gemini.py`)
- Agent Orchestration:
  - Intake
  - Questioning
  - Classification
  - Retrieval
  - Recommendation
  - Safety
- Shared state:
  - Redis-backed when `RIA_REDIS_URL` is configured
  - In-memory fallback for local development
- Observability:
  - Prometheus metrics (`/metrics`)
  - Optional OpenTelemetry tracing

## Security Model

- Authn/Authz:
  - Stub SSO for local development
  - JWT mode for production
  - Role checks for privileged endpoints
- Abuse and overload controls:
  - Rate limiting + DDoS guard
  - IP reputation blocklist
  - WAF payload checks for sensitive endpoints
- Prompt-injection defense:
  - Instruction override/exfiltration pattern detection
  - Strict mode session quarantine after repeated attempts
- Audit and integrity:
  - Hash-chained immutable audit log entries
  - Audit chain verification and signed export utilities

## Quick Start (Local)

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure environment

```bash
copy .env.example .env
```

Set at minimum:
- `RIA_GEMINI_API_KEY`
- `RIA_SSO_MODE=stub` for local development

### 3) Run API + UI

```bash
uvicorn app.main:app --reload
```

Open:
- `http://localhost:8000`

## Testing and Verification

### Unit and integration tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Evaluation gate (dataset + QA + benchmark)

```bash
python -m app.eval.generate_eval_dataset
python -m app.eval.qa_eval_dataset
python -m app.eval.benchmark
python -m app.eval.gate_thresholds
```

### Security checks

```bash
python -m bandit -r app -q
$env:PYTHONPATH='.'; python scripts/red_team_simulation.py
python scripts/verify_audit_chain.py
python scripts_compliance_check.py
```

Security report output:
- `docs/security_assessment_v1.md`
- `docs/security_assessment_v1.json`

## Docker

### Build and run

```bash
docker compose up --build
```

Primary files:
- `Dockerfile`
- `docker-compose.yml`

## Kubernetes Deployment and Scaling

Manifests are under `deploy/k8s/`:
- `deployment.yaml`
- `service.yaml`
- `ingress.yaml`
- `hpa.yaml`
- `pdb.yaml`
- `network-policy.yaml`
- `configmap.yaml`
- `secret.template.yaml`

Scaling roadmap:
- `docs/kubernetes_scaling_plan.md`

## Operations Scripts

- Red-team simulation: `scripts/red_team_simulation.py`
- Abuse/chaos load script: `scripts/chaos_abuse_test.py`
- Weekly Gemini model refresh: `.github/workflows/weekly_model_refresh.yml`
- Monthly secret-rotation artifact: `.github/workflows/monthly_secret_rotation.yml`
- Rotate secrets utility: `scripts/rotate_secrets.py`
- Signed audit export: `scripts/export_audit_signed.py`
- Verify audit chain: `scripts/verify_audit_chain.py`

## CI/CD

GitHub Actions workflows:
- `ci.yml`: tests + eval gate + compliance checks
- `weekly_model_refresh.yml`: model compatibility refresh PR
- `monthly_secret_rotation.yml`: encrypted rotation artifact generation

## Configuration Notes

The full configuration surface is documented in `.env.example` and loaded via `RIA_` prefix.

Important production settings:
- `RIA_SSO_MODE=jwt`
- `RIA_REQUIRE_JWT_IN_PROD=true`
- `RIA_REQUIRE_MTLS_FOR_INTERNAL=true`
- `RIA_WAF_ENABLED=true`
- `RIA_REDIS_URL=redis://...`
- `RIA_OTEL_ENABLED=true`

## Current Status

- Security checks: passing
- Red-team simulation: passing
- Compliance checks: passing
- Test suite: passing
