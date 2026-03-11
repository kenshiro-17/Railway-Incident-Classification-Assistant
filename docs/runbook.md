# Pilot Runbook (Starter)

## Start Service
1. `pip install -r requirements.txt`
2. Configure `.env` with `RIA_GEMINI_API_KEY`.
3. `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Auth
- Bearer token format for pilot stub: `user:<id>|role:<worker|supervisor|admin>`

## Core Checks
- Health: `GET /health`
- Version: `GET /version`
- Metrics (supervisor/admin only): `GET /metrics`

## Safety Handling
- Any `escalation_required=true` response must be routed to human triage.

## Data Governance
- Taxonomy changes require ops sign-off and version update.
- Use `app/eval/eval_dataset_v1.json` for benchmark gate.
