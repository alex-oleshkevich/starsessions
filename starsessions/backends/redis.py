import typing

import aioredis

from ..serializers import JsonSerializer, Serializer
from .base import SessionBackend


class RedisBackend(SessionBackend):
    """Stores session data in a Redis server."""

    def __init__(
        self,
        url: str = None,
        connection: aioredis.Redis = None,
        serializer: Serializer = None,
    ) -> None:
        assert (
            url or connection
        ), 'Either "url" or "connection" arguments must be provided.'
        self._serializer = serializer or JsonSerializer()
        self._connection = connection or aioredis.from_url(url)

    async def read(self, session_id: str) -> typing.Dict:
        value = await self._connection.get(session_id)
        if value is None:
            return {}
        return self._serializer.deserialize(value)

    async def write(
        self, data: typing.Dict, session_id: typing.Optional[str] = None
    ) -> str:
        session_id = session_id or await self.generate_id()
        await self._connection.set(session_id, self._serializer.serialize(data))
        return session_id

    async def remove(self, session_id: str) -> None:
        await self._connection.delete(session_id)

    async def exists(self, session_id: str) -> bool:
        result = await self._connection.exists(session_id)
        return result > 0
