from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any

from app.core.config import settings

try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = None  # type: ignore


class InMemoryStateStore:
    def __init__(self) -> None:
        self.kv: dict[str, tuple[float, str]] = {}
        self.lists: defaultdict[str, list[str]] = defaultdict(list)

    def _expired(self, key: str) -> bool:
        if key not in self.kv:
            return True
        expires_at, _ = self.kv[key]
        if expires_at <= time.time():
            del self.kv[key]
            return True
        return False

    def get_json(self, key: str) -> Any:
        if self._expired(key):
            return None
        _, raw = self.kv[key]
        return json.loads(raw)

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        self.kv[key] = (time.time() + ttl_seconds, json.dumps(value))

    def append_json_list(self, key: str, value: Any, max_items: int, ttl_seconds: int) -> None:
        lst = self.lists[key]
        lst.append(json.dumps(value))
        if len(lst) > max_items:
            self.lists[key] = lst[-max_items:]
        self.kv[key] = (time.time() + ttl_seconds, "[]")

    def get_json_list(self, key: str) -> list[Any]:
        if key in self.kv and self._expired(key):
            self.lists.pop(key, None)
            return []
        return [json.loads(item) for item in self.lists.get(key, [])]

    def set_json_list(self, key: str, values: list[Any], ttl_seconds: int) -> None:
        self.lists[key] = [json.dumps(item) for item in values]
        self.kv[key] = (time.time() + ttl_seconds, "[]")


class RedisStateStore:
    def __init__(self, url: str) -> None:
        if Redis is None:
            raise RuntimeError("redis package is not installed")
        self.client = Redis.from_url(url, decode_responses=True)

    def get_json(self, key: str) -> Any:
        raw = self.client.get(key)
        return json.loads(raw) if raw else None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        self.client.set(name=key, value=json.dumps(value), ex=ttl_seconds)

    def append_json_list(self, key: str, value: Any, max_items: int, ttl_seconds: int) -> None:
        pipe = self.client.pipeline()
        pipe.rpush(key, json.dumps(value))
        pipe.ltrim(key, -max_items, -1)
        pipe.expire(key, ttl_seconds)
        pipe.execute()

    def get_json_list(self, key: str) -> list[Any]:
        return [json.loads(item) for item in self.client.lrange(key, 0, -1)]

    def set_json_list(self, key: str, values: list[Any], ttl_seconds: int) -> None:
        pipe = self.client.pipeline()
        pipe.delete(key)
        if values:
            pipe.rpush(key, *[json.dumps(item) for item in values])
        pipe.expire(key, ttl_seconds)
        pipe.execute()


def build_state_store() -> InMemoryStateStore | RedisStateStore:
    if settings.redis_url:
        return RedisStateStore(settings.redis_url)
    return InMemoryStateStore()


state_store = build_state_store()
