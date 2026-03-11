# Slice Coverage Matrix

## Slice 0
- FastAPI skeleton: `app/main.py`, `app/api/routes.py`
- SSO + RBAC: `app/core/security.py`
- Config system: `app/core/config.py`
- Taxonomy v1: `app/models/taxonomy.py`
- Observability baseline: `/health`, `/metrics`, audit logs

## Slice 1
- Gemini adapter: `app/services/gemini.py`
- Prompt/output contract: `app/agents/classification_agent.py`
- Clarification loop: `app/services/orchestrator.py`
- Safety escalation: `app/agents/safety_agent.py`

## Slice 2
- Per-user/IP/global rate limits with burst+sustained windows: `app/services/rate_limiter.py`
- 429 with Retry-After: enforced in HTTPException headers

## Slice 3
- CSV/XLSX ingestion + similarity retrieval: `app/services/retrieval.py`
- Evidence-linked recommendations: `app/agents/recommendation_agent.py`

## Slice 4
- 600 scenario generation: `app/eval/generate_eval_dataset.py`
- QA checks + report: `app/eval/qa_eval_dataset.py`

## Slice 5
- Web chat pilot UX: `app/ui/index.html`
- Feedback capture endpoint: `/feedback`
- Runbook starter: `docs/runbook.md`
