# Railway Incident Classification Assistant

FastAPI + Gemini-backed modular assistant for railway incident classification.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Security and Compliance Checks

```bash
python -m app.eval.generate_eval_dataset
python -m app.eval.qa_eval_dataset
python -m app.eval.benchmark
python -m app.eval.gate_thresholds
python scripts_compliance_check.py
python -m bandit -r app -q
```

## Deployment

```bash
docker compose up --build
```

Kubernetes manifests are in `deploy/k8s/`:
- `deployment.yaml`, `service.yaml`, `ingress.yaml`
- `hpa.yaml`, `pdb.yaml`, `network-policy.yaml`
- `configmap.yaml`, `secret.template.yaml`

Future scaling plan:
- [docs/kubernetes_scaling_plan.md](docs/kubernetes_scaling_plan.md)

## Security/Operations Scripts

```bash
# Verify immutable audit chain
python scripts/verify_audit_chain.py

# Signed audit export
set RIA_AUDIT_SIGNING_KEY=... && python scripts/export_audit_signed.py

# Abuse chaos test
python scripts/chaos_abuse_test.py --base-url http://localhost:8000 --concurrency 60

# Monthly-style secret rotation artifact
set RIA_SECRETS_ENCRYPTION_KEY=... && python scripts/rotate_secrets.py
```
