from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings


class AuditLogger:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._bootstrap_hash()

    def _bootstrap_hash(self) -> str:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return "genesis"
        with self.path.open("rb") as handle:
            lines = handle.readlines()
            if not lines:
                return "genesis"
            try:
                previous = json.loads(lines[-1].decode("utf-8"))
                return str(previous.get("entry_hash", "genesis"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return "genesis"

    def log(self, event: Dict[str, Any]) -> None:
        event["logged_at"] = datetime.now(timezone.utc).isoformat()
        event["prev_hash"] = self._last_hash
        payload = json.dumps(event, ensure_ascii=True, sort_keys=True)
        entry_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        event["entry_hash"] = entry_hash
        line = json.dumps(event, ensure_ascii=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        self._last_hash = entry_hash


audit_logger = AuditLogger(settings.audit_log_path)
