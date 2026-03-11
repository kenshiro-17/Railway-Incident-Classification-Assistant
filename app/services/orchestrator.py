from __future__ import annotations

from uuid import uuid4

from app.agents.classification_agent import ClassificationAgent
from app.agents.intake_agent import IntakeAgent
from app.agents.questioning_agent import QuestioningAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.safety_agent import SafetyAgent
from app.core.config import settings
from app.core.metrics import escalations_total
from app.core.security import hash_text
from app.models.schemas import ChatMessageRequest, ChatResponse
from app.services.audit import audit_logger
from app.services.prompt_injection import detect_prompt_injection, sanitize_untrusted_text
from app.services.redaction import redact_text
from app.services.session_context import SessionTurn, session_context_store
from app.services.session_security import session_security_store


class AssistantOrchestrator:
    def __init__(self) -> None:
        self.intake = IntakeAgent()
        self.questioning = QuestioningAgent()
        self.classification = ClassificationAgent()
        self.retrieval = RetrievalAgent()
        self.recommendation = RecommendationAgent()
        self.safety = SafetyAgent()

    async def run(self, request: ChatMessageRequest, user_id: str) -> ChatResponse:
        trace_id = str(uuid4())
        quarantine_seconds = session_security_store.is_quarantined(request.session_id)
        if quarantine_seconds > 0:
            response = ChatResponse(
                trace_id=trace_id,
                clarifying_questions=[],
                predicted_class="UNCLASSIFIED",
                confidence=0.0,
                suggested_next_steps=[
                    f"Session is temporarily quarantined due to repeated prompt-injection attempts. Retry in {quarantine_seconds} seconds.",
                    "Use a new supervised session for urgent incident triage."
                ],
                escalation_required=True,
                escalation_reason="Session quarantined by strict prompt-injection policy.",
            )
            escalations_total.labels(reason="prompt_injection_quarantine").inc()
            self._audit(user_id=user_id, request=request, response=response)
            return response
        incident = self.intake.run(request.incident)
        guard = detect_prompt_injection(
            request.user_message,
            incident.symptoms,
            incident.operator_actions_taken,
        )
        if guard.blocked:
            quarantined = session_security_store.record_injection_attempt(request.session_id)
            response = ChatResponse(
                trace_id=trace_id,
                clarifying_questions=[
                    "Please provide only factual incident details: symptoms, sequence of events, and actions taken."
                ],
                predicted_class="UNCLASSIFIED",
                confidence=0.0,
                suggested_next_steps=[
                    "Potential prompt-injection pattern detected. Re-submit incident facts without instruction-like text.",
                    "Escalate to supervisor if the report source appears tampered."
                ],
                escalation_required=True,
                escalation_reason=(
                    "Session quarantined due to repeated prompt-injection attempts."
                    if quarantined
                    else "Potential prompt-injection content detected in incident chat payload."
                ),
            )
            reason_label = "prompt_injection_quarantine" if quarantined else "prompt_injection"
            escalations_total.labels(reason=reason_label).inc()
            self._audit(user_id=user_id, request=request, response=response)
            return response

        missing = self.questioning.missing_questions(incident)
        if missing and request.clarification_turn < settings.max_clarification_turns:
            response = ChatResponse(
                trace_id=trace_id,
                clarifying_questions=missing,
                predicted_class="UNCLASSIFIED",
                confidence=0.0,
                suggested_next_steps=["Please provide the missing details to continue classification."],
                escalation_required=False,
                escalation_reason=""
            )
            self._audit(user_id=user_id, request=request, response=response)
            escalations_total.labels(reason="insufficient_info").inc()
            return response
        if missing and request.clarification_turn >= settings.max_clarification_turns:
            response = ChatResponse(
                trace_id=trace_id,
                clarifying_questions=[],
                predicted_class="UNCLASSIFIED",
                confidence=0.0,
                suggested_next_steps=[
                    "Insufficient information for safe classification. Escalate to supervisor and provide missing incident details."
                ],
                escalation_required=True,
                escalation_reason="Required incident details remained missing after maximum clarification turns."
            )
            self._audit(user_id=user_id, request=request, response=response)
            return response

        session_context = session_context_store.render_context(request.session_id)
        clean_user_message = sanitize_untrusted_text(request.user_message)
        model_out = await self.classification.classify(
            incident=incident,
            user_message=clean_user_message,
            session_context=session_context,
        )
        similar = self.retrieval.run(incident.symptoms)
        next_steps = self.recommendation.run(
            predicted_class=model_out["predicted_class"],
            similar=similar,
            model_steps=model_out["suggested_next_steps"]
        )
        escalation_required, escalation_reason = self.safety.evaluate(
            predicted_class=model_out["predicted_class"],
            confidence=model_out["confidence"],
            safety_flags=incident.safety_flags
        )

        response = ChatResponse(
            trace_id=trace_id,
            clarifying_questions=model_out["clarifying_questions"],
            predicted_class=model_out["predicted_class"],
            confidence=model_out["confidence"],
            similar_incidents=similar,
            suggested_next_steps=next_steps,
            escalation_required=escalation_required,
            escalation_reason=escalation_reason,
            evidence_refs=[f"historical:{s.incident_id}" for s in similar]
        )
        if response.escalation_required:
            reason = response.escalation_reason.lower()
            if "critical" in reason:
                label = "critical_class"
            elif "low confidence" in reason:
                label = "low_confidence"
            elif "safety flag" in reason:
                label = "safety_flag"
            else:
                label = "policy"
            escalations_total.labels(reason=label).inc()
        session_context_store.append(
            request.session_id,
            SessionTurn(
                user_message=clean_user_message,
                incident_summary=incident.symptoms,
                predicted_class=response.predicted_class,
                escalation_required=response.escalation_required,
            ),
        )
        self._audit(user_id=user_id, request=request, response=response)
        return response

    def _audit(self, user_id: str, request: ChatMessageRequest, response: ChatResponse) -> None:
        raw = f"{request.user_message}\n{request.incident.symptoms}\n{request.incident.operator_actions_taken}"
        audit_logger.log(
            {
                "user_id": user_id,
                "incident_id": request.incident.incident_id,
                "input_hash": hash_text(redact_text(raw)),
                "model": settings.gemini_model,
                "template_version": settings.prompt_template_version,
                "output_class": response.predicted_class,
                "escalation_required": response.escalation_required,
                "trace_id": response.trace_id
            }
        )


orchestrator = AssistantOrchestrator()
