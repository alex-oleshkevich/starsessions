import typing

from .base import SessionBackend


class InMemoryBackend(SessionBackend):
    """Stores session data in a dictionary."""

    def __init__(self) -> None:
        self.data: dict = {}

    async def read(self, session_id: str) -> typing.Dict:
        return self.data.get(session_id, {}).copy()

    async def write(
        self, data: typing.Dict, session_id: typing.Optional[str] = None
    ) -> str:
        session_id = session_id or await self.generate_id()
        self.data[session_id] = data
        return session_id

    async def remove(self, session_id: str) -> None:
        del self.data[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self.data
