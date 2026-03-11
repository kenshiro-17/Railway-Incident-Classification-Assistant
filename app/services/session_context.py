from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.services.state_store import state_store

@dataclass
class SessionTurn:
    user_message: str
    incident_summary: str
    predicted_class: str
    escalation_required: bool


class SessionContextStore:
    def __init__(self, max_turns: int = 5) -> None:
        self.max_turns = max_turns
        self.prefix = "session_context:"

    def append(self, session_id: str, turn: SessionTurn) -> None:
        key = f"{self.prefix}{session_id}"
        state_store.append_json_list(
            key=key,
            value=turn.__dict__,
            max_items=self.max_turns,
            ttl_seconds=settings.state_ttl_seconds,
        )

    def render_context(self, session_id: str) -> str:
        key = f"{self.prefix}{session_id}"
        turns_raw = state_store.get_json_list(key)
        if not turns_raw:
            return "No prior session context."
        turns: list[SessionTurn] = [SessionTurn(**item) for item in turns_raw if isinstance(item, dict)]
        lines = []
        for i, turn in enumerate(turns, start=1):
            lines.append(
                f"Turn {i}: msg={turn.user_message[:200]!r}; incident={turn.incident_summary[:240]!r}; "
                f"predicted_class={turn.predicted_class}; escalation={turn.escalation_required}"
            )
        return "\n".join(lines)


session_context_store = SessionContextStore(max_turns=5)
