import aioredis
import typing

from ..serializers import JsonSerializer, Serializer
from .base import SessionBackend


class RedisBackend(SessionBackend):
    """Stores session data in a Redis server."""

    def __init__(
        self,
        url: str = None,
        connection: aioredis.Redis = None,
        serializer: Serializer = None,
        redis_key_func: typing.Callable[[str], str] = None,
        expire: int = None,
    ) -> None:
        """Initializes redis session backend.

        Args:
            url (str, optional): Redis URL. Defaults to None.
            connection (aioredis.Redis, optional): aioredis connection. Defaults to None.
            serializer (Serializer, optional): Object serializer. Defaults to None.
            redis_key_func (typing.Callable[[str], str], optional): Customize redis key name. Defaults to None.
            expire (int, optional): Key expiry in seconds. Defaults to None.
        """
        assert url or connection, 'Either "url" or "connection" arguments must be provided.'
        self._serializer = serializer or JsonSerializer()
        self._connection = connection or aioredis.from_url(url)
        if redis_key_func:
            assert callable(
                redis_key_func
            ), "The redis_key_func needs to be a callable that takes a single string argument."
        self._redis_key_func = redis_key_func
        self.expire = expire

    def get_redis_key(self, session_id: str) -> str:
        if self._redis_key_func:
            return self._redis_key_func(session_id)
        else:
            return session_id

    async def read(self, session_id: str) -> typing.Dict:
        value = await self._connection.get(self.get_redis_key(session_id))
        if value is None:
            return {}
        return self._serializer.deserialize(value)

    async def write(self, data: typing.Dict, session_id: typing.Optional[str] = None) -> str:
        session_id = session_id or await self.generate_id()
        session_id = session_id or await self.generate_id()
        await self._connection.set(
            self.get_redis_key(session_id),
            self._serializer.serialize(data),
            ex=self.expire,
        )
        return session_id

    async def remove(self, session_id: str) -> None:
        await self._connection.delete(self.get_redis_key(session_id))

    async def exists(self, session_id: str) -> bool:
        result = await self._connection.exists(self.get_redis_key(session_id))
        return result > 0
