# Security Assessment v1

## Summary
- Total checks: 6
- Passed: 6
- Failed: 0

## Findings
- `missing_auth`: status=401 expected=401 pass=True
- `tampered_token`: status=401 expected=401 pass=True
- `internal_no_token`: status=401 expected=401 pass=True
- `waf_signature_block`: status=400 expected=400 pass=True
- `strict_mode_quarantine`: status=200 expected=200 pass=True
- `rate_limit_pressure`: status=429 expected=200/429 pass=True

## Notes
- This red-team run uses in-process FastAPI TestClient for deterministic checks.
- Network-edge controls (Ingress mTLS/WAF) require cluster-level validation in staging.
