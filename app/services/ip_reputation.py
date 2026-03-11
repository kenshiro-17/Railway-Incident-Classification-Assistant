from __future__ import annotations

from pathlib import Path

from app.core.config import settings


class IPReputationStore:
    def __init__(self) -> None:
        self._blocked: set[str] = set()
        self.reload()

    def reload(self) -> None:
        path = Path(settings.ip_blocklist_path)
        if not path.exists():
            self._blocked = set()
            return
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
        self._blocked = {line for line in lines if line and not line.startswith("#")}

    def is_blocked(self, ip: str) -> bool:
        return ip in self._blocked


ip_reputation_store = IPReputationStore()
