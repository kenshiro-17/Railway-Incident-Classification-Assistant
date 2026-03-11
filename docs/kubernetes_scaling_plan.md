# Kubernetes Scaling Plan (Future)

## Objectives
- Sustain national traffic spikes without degraded triage latency.
- Preserve safety controls (rate limit, injection quarantine, escalation integrity) under scale.
- Enable zero-downtime deployments and resilient regional failover.

## Phase 1: Baseline Production (0-3 months)
- Deploy 3 replicas behind Ingress + HPA (`deploy/k8s/hpa.yaml`).
- Use Redis for shared state (`RIA_REDIS_URL`) so quarantine/rate-context works across pods.
- Enforce ingress WAF + mTLS + per-connection limits.
- Add PodDisruptionBudget to protect availability.

## Phase 2: Regional Scale-Out (3-6 months)
- Run active-active in at least 2 regions.
- Use global load balancing with geo-routing and health checks.
- Keep Redis highly available per region; replicate non-sensitive analytics asynchronously.
- Roll out canary deployments with 5%-25%-50%-100% traffic policy.

## Phase 3: Peak Resilience (6-12 months)
- Enable KEDA/autoscaling from queue depth and p95 latency.
- Add isolated worker pools for ingestion/evaluation jobs.
- Introduce circuit breakers around external LLM calls and strict fallback policy.
- Run monthly chaos drills for DDoS + injection storms.

## SLOs and Guardrails
- API p95 latency <= 5s.
- Critical incident recall >= 0.95.
- Error rate < 1% during normal load.
- 0 safety-policy bypass defects.

## Capacity Testing Cadence
- Weekly synthetic load tests.
- Monthly abuse/chaos campaign (`scripts/chaos_abuse_test.py`).
- Quarterly regional failover rehearsal.
