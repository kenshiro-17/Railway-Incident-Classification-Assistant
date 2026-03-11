from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

http_requests_total = Counter(
    "ria_http_requests_total",
    "HTTP requests total",
    labelnames=("method", "path", "status"),
)
http_request_latency_seconds = Histogram(
    "ria_http_request_latency_seconds",
    "HTTP request latency in seconds",
    labelnames=("method", "path"),
)
rate_limit_blocks_total = Counter(
    "ria_rate_limit_blocks_total",
    "Rate limit blocks",
    labelnames=("window",),
)
escalations_total = Counter(
    "ria_escalations_total",
    "Escalation decisions",
    labelnames=("reason",),
)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
