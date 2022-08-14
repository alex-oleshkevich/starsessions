import typing

from .base import SessionBackend


class InMemoryBackend(SessionBackend):
    """Stores session data in a dictionary."""

    def __init__(self) -> None:
        self.data: typing.Dict[str, typing.Any] = {}

    async def read(self, session_id: str) -> typing.Dict[str, typing.Any]:
        return self.data.get(session_id, {}).copy()  # type: ignore[no-any-return]

    async def write(self, session_id: str, data: typing.Dict[str, typing.Any]) -> str:
        self.data[session_id] = data
        return session_id

    async def remove(self, session_id: str) -> None:
        try:
            del self.data[session_id]
        except KeyError:
            pass

    async def exists(self, session_id: str) -> bool:
        return session_id in self.data
