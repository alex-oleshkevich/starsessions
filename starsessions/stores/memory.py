from __future__ import annotations

import dataclasses
import time

from starsessions.stores.base import SessionStore


@dataclasses.dataclass
class Record:
    expires: int
    value: bytes


class InMemoryStore(SessionStore):
    """Stores session data in a dictionary."""

    def __init__(self, gc_ttl: int = 3600 * 24) -> None:
        self.data: dict[str, Record] = {}
        self.gc_ttl = gc_ttl

    async def read(self, session_id: str, lifetime: int) -> bytes:
        value = self.data.get(session_id)
        if value is None:
            return b""

        if value.expires < time.time_ns():
            self.data.pop(session_id, None)
            return b""

        return value.value

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        self._evict_expired()
        effective_ttl = ttl if ttl > 0 else self.gc_ttl
        self.data[session_id] = Record(expires=effective_ttl * 1_000_000_000 + time.time_ns(), value=data)
        return session_id

    def _evict_expired(self) -> None:
        now = time.time_ns()
        self.data = {k: v for k, v in self.data.items() if v.expires >= now}

    async def remove(self, session_id: str) -> None:
        try:
            del self.data[session_id]
        except KeyError:
            pass
