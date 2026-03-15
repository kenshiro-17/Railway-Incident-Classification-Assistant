# Railway Incident Classification Assistant

Production-oriented incident triage and classification assistant for railway operations teams.

The system accepts structured or incomplete incident reports, asks clarifying questions, classifies failures against a controlled taxonomy, retrieves similar historical cases, and returns safety-aware next steps with auditability and abuse controls built in.

## Core Capabilities

- Incident intake and clarification loop
- Controlled top-20 incident taxonomy classification
- Historical similarity retrieval from CSV and XLSX datasets
- Safety escalation for critical or low-confidence situations
- Prompt-injection detection and session quarantine mode
- JWT-ready authentication and privileged endpoint checks
- Hash-chained audit logs with verification utilities
- Docker and Kubernetes deployment paths
- Prometheus metrics and optional OpenTelemetry hooks

## Architecture

### Main runtime path

```text
Incident report
  -> intake and validation
  -> clarification questions when data is incomplete
  -> classification + retrieval
  -> safety checks
  -> grounded recommendation
  -> audit log + metrics
```

### Service layers

- `app/main.py`: FastAPI application entrypoint
- `app/services/`: provider logic, orchestration, safety behavior, retrieval
- `app/eval/`: dataset generation, QA checks, benchmark and threshold gates
- `scripts/`: red-team simulation, chaos checks, audit verification, secret rotation helpers
- `deploy/k8s/`: deployment, service, ingress, HPA, network policy, and supporting manifests

Repo diagrams already included:

- `docs/runtime-architecture.png`
- `docs/production-deployment.png`

## Security Posture

- Stub SSO for local development, JWT mode for production
- Rate limiting and DDoS guard layers
- WAF-style payload inspection on sensitive routes
- Prompt-injection detection with strict quarantine behavior
- Immutable hash-chained audit entries
- Signed export and audit-chain verification scripts

## Prerequisites

- Python 3.10+
- `pip`
- Optional: Docker and Docker Compose
- Optional for production-like local runs: Redis
- Gemini API key if you want live provider behavior

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/kenshiro-17/Railway-Incident-Classification-Assistant.git
cd railway-incident-classification-assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the environment

```bash
cp .env.example .env
```

Minimum local settings:

```env
RIA_GEMINI_API_KEY=your_key_here
RIA_SSO_MODE=stub
```

Useful production-oriented settings are documented in `.env.example` and include:

- `RIA_SSO_MODE=jwt`
- `RIA_REQUIRE_JWT_IN_PROD=true`
- `RIA_REDIS_URL=redis://...`
- `RIA_WAF_ENABLED=true`
- `RIA_OTEL_ENABLED=true`

### 4. Run the application

```bash
uvicorn app.main:app --reload
```

Open:

- App: `http://127.0.0.1:8000`
- Metrics: `http://127.0.0.1:8000/metrics`

## Testing and Verification

### Unit and integration tests

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

### Evaluation gate

```bash
python -m app.eval.generate_eval_dataset
python -m app.eval.qa_eval_dataset
python -m app.eval.benchmark --predictor auto
python -m app.eval.gate_thresholds
```

### Security and resilience checks

```bash
python -m bandit -r app -q
python scripts/red_team_simulation.py
python scripts/verify_audit_chain.py
python scripts/chaos_abuse_test.py
```

## Docker

```bash
docker compose up --build
```

Key files:

- `Dockerfile`
- `docker-compose.yml`

## Kubernetes

Kubernetes manifests are under `deploy/k8s/`:

- `deployment.yaml`
- `service.yaml`
- `ingress.yaml`
- `hpa.yaml`
- `pdb.yaml`
- `network-policy.yaml`
- `configmap.yaml`
- `secret.template.yaml`

Supporting documentation:

- `docs/kubernetes_scaling_plan.md`

## Operational Scripts

| Script | Purpose |
| --- | --- |
| `scripts/red_team_simulation.py` | adversarial safety checks |
| `scripts/chaos_abuse_test.py` | abuse and overload simulation |
| `scripts/verify_audit_chain.py` | audit integrity verification |
| `scripts/export_audit_signed.py` | signed audit export |
| `scripts/rotate_secrets.py` | secret rotation support |

## CI/CD

GitHub Actions workflows include:

- `ci.yml` for tests, evaluation gate, and compliance checks
- `weekly_model_refresh.yml` for provider/model compatibility refresh
- `monthly_secret_rotation.yml` for encrypted secret rotation artifacts

## Why This Repo Is Different

This is not just a chat wrapper on top of a model API. The repo treats the assistant as an operational system with:

- constrained classification behavior
- explicit safety escalation
- retrieval grounding
- auditability
- deployment artifacts
- evaluation gates

That is what makes it relevant for safety-sensitive workflows instead of demo-only usage.

## Troubleshooting

### Provider calls fail locally

Check `RIA_GEMINI_API_KEY` and confirm your environment file is being loaded.

### State is lost between runs

Configure `RIA_REDIS_URL` if you want Redis-backed shared state instead of the in-memory fallback.

### Security scripts fail in a fresh environment

Install the repo requirements first, then run the scripts from the repository root so local imports resolve correctly.

## Current Status

Based on repo tooling and docs, the project already includes:

- tests
- evaluation utilities
- security review scripts
- deployment manifests
- observability endpoints

## License

Add the project license here if you want external reuse terms to be explicit.
