import time
from pathlib import Path

from opentelemetry import trace
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.middleware import SecurityMiddleware
from app.core.metrics import http_request_latency_seconds, http_requests_total
from app.core.telemetry import setup_telemetry
from app.services.retrieval import retrieval_store

app = FastAPI(title=settings.app_name)
setup_telemetry()
tracer = trace.get_tracer(__name__)
allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
trusted_hosts = [host.strip() for host in settings.trusted_hosts.split(",") if host.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Trace-Id"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
app.add_middleware(SecurityMiddleware)

app.include_router(router)


@app.on_event("startup")
async def bootstrap_retrieval_data() -> None:
    if not settings.bootstrap_retrieval_from_eval_dataset:
        return
    dataset_path = Path(settings.retrieval_eval_dataset_path)
    if not dataset_path.exists():
        return
    result = retrieval_store.ingest_eval_dataset_json(str(dataset_path))
    print(
        "Retrieval bootstrap loaded eval dataset:",
        f"added={result['added']}",
        f"rejected={result['rejected']}",
        f"duplicate={result['duplicate']}",
    )


@app.middleware("http")
async def metrics_middleware(request: Request, call_next) -> Response:
    start = time.perf_counter()
    with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.path", request.url.path)
        response = await call_next(request)
        span.set_attribute("http.status_code", response.status_code)
    elapsed = time.perf_counter() - start
    path = request.url.path
    method = request.method
    http_request_latency_seconds.labels(method=method, path=path).observe(elapsed)
    http_requests_total.labels(method=method, path=path, status=str(response.status_code)).inc()
    return response

ui_path = Path("app/ui")
if ui_path.exists():
    app.mount("/", StaticFiles(directory=str(ui_path), html=True), name="ui")
