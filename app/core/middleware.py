from __future__ import annotations

import time
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.services.ip_reputation import ip_reputation_store

WAF_PATTERNS = (
    "union select",
    "<script",
    "javascript:",
    "onerror=",
    "drop table",
    "../",
)


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id", str(uuid4()))
        client_ip = request.client.host if request.client else ""
        if client_ip and ip_reputation_store.is_blocked(client_ip):
            return JSONResponse(
                status_code=403,
                content={"detail": "Request denied by security policy.", "trace_id": trace_id},
            )

        body = b""
        if request.method in {"POST", "PUT", "PATCH"}:
            body = await request.body()
            if len(body) > settings.max_request_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request entity too large.", "trace_id": trace_id},
                )
            request._body = body
            if settings.waf_enabled and request.url.path in {"/chat/message", "/incident/classify"}:
                lowered = body.decode("utf-8", errors="ignore").lower()
                if any(pattern in lowered for pattern in WAF_PATTERNS):
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Request blocked by WAF policy.", "trace_id": trace_id},
                    )

        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > settings.max_request_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request entity too large.", "trace_id": trace_id},
            )

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            return JSONResponse(
                status_code=500,
                content={"detail": "An internal error occurred. Contact support with trace ID.", "trace_id": trace_id},
            )

        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none';"
        )
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Response-Time-ms"] = str(round((time.perf_counter() - start) * 1000, 2))
        return response
