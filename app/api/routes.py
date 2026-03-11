from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from app.core.config import settings
from app.core.metrics import render_metrics
from app.core.security import UserContext, require_internal_client, require_supervisor_or_admin, require_user
from app.models.schemas import (
    ChatMessageRequest,
    ChatResponse,
    ChatSessionCreate,
    ClassifyRequest,
    FeedbackRequest,
)
from app.models.taxonomy import TAXONOMY_VERSION
from app.services.audit import audit_logger
from app.services.orchestrator import orchestrator
from app.services.ip_reputation import ip_reputation_store
from app.services.rate_limiter import rate_limiter

router = APIRouter()


@router.post("/chat/session")
async def create_session(payload: ChatSessionCreate, user: UserContext = Depends(require_user)) -> dict:
    return {"session_id": str(uuid4()), "locale": payload.locale, "user_id": user.user_id}


@router.post("/chat/message", response_model=ChatResponse)
async def chat_message(payload: ChatMessageRequest, request: Request, user: UserContext = Depends(require_user)) -> ChatResponse:
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.enforce(user_id=user.user_id, ip=client_ip)
    return await orchestrator.run(payload, user_id=user.user_id)


@router.post("/incident/classify", response_model=ChatResponse)
async def classify(payload: ClassifyRequest, request: Request, user: UserContext = Depends(require_user)) -> ChatResponse:
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.enforce(user_id=user.user_id, ip=client_ip)
    req = ChatMessageRequest(
        session_id=str(uuid4()),
        incident=payload.incident,
        user_message=payload.incident.symptoms,
        clarification_turn=settings.max_clarification_turns
    )
    return await orchestrator.run(req, user_id=user.user_id)


@router.post("/feedback")
async def feedback(payload: FeedbackRequest, user: UserContext = Depends(require_user)) -> dict:
    audit_logger.log(
        {
            "event": "feedback",
            "user_id": user.user_id,
            "session_id": payload.session_id,
            "incident_id": payload.incident_id,
            "is_correct": payload.is_correct,
            "corrected_label": payload.corrected_label,
            "comment": payload.comment
        }
    )
    return {"status": "accepted"}


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/version")
async def version() -> dict:
    return {
        "version": "0.1.0",
        "taxonomy": TAXONOMY_VERSION,
        "model": settings.gemini_model,
        "template_version": settings.prompt_template_version,
    }


@router.get("/metrics")
async def metrics(_: UserContext = Depends(require_supervisor_or_admin)):
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)


@router.get("/internal/health")
async def internal_health(_: None = Depends(require_internal_client)) -> dict:
    return {"status": "ok", "scope": "internal"}


@router.post("/internal/ip-reputation/reload")
async def internal_reload_ip_reputation(_: None = Depends(require_internal_client)) -> dict:
    ip_reputation_store.reload()
    return {"status": "reloaded"}
