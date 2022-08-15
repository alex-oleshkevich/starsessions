import typing

from starsessions.stores.base import SessionStore


class InMemoryStore(SessionStore):
    """Stores session data in a dictionary."""

    def __init__(self) -> None:
        self.data: typing.Dict[str, bytes] = {}

    async def read(self, session_id: str, lifetime: int) -> bytes:
        return self.data.get(session_id, b"")

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        self.data[session_id] = data
        return session_id

    async def remove(self, session_id: str) -> None:
        try:
            del self.data[session_id]
        except KeyError:
            pass

    async def exists(self, session_id: str) -> bool:
        return session_id in self.data
