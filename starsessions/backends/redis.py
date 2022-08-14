import aioredis
import typing

from starsessions.backends.base import SessionBackend
from starsessions.exceptions import ImproperlyConfigured


class RedisBackend(SessionBackend):
    """Stores session data in a Redis server."""

    def __init__(
        self,
        url: typing.Optional[str] = None,
        connection: typing.Optional[aioredis.Redis] = None,
        redis_key_func: typing.Optional[typing.Callable[[str], str]] = None,
        expire: typing.Optional[int] = None,
    ) -> None:
        """
        Initializes redis session backend.

        Args:
            url (str, optional): Redis URL. Defaults to None.
            connection (aioredis.Redis, optional): aioredis connection. Defaults to None.
            redis_key_func (typing.Callable[[str], str], optional): Customize redis key name. Defaults to None.
            expire (int, optional): Key expiry in seconds. Defaults to None.
        """
        if not (url or connection):
            raise ImproperlyConfigured("Either 'url' or 'connection' arguments must be provided.")

        self._connection: aioredis.Redis = connection or aioredis.from_url(url)  # type: ignore[no-untyped-call]

        if redis_key_func and not callable(redis_key_func):
            raise ImproperlyConfigured("The redis_key_func needs to be a callable that takes a single string argument.")

        self._redis_key_func = redis_key_func
        self.expire = expire

    def get_redis_key(self, session_id: str) -> str:
        if self._redis_key_func:
            return self._redis_key_func(session_id)
        else:
            return session_id

    async def read(self, session_id: str) -> bytes:
        value = await self._connection.get(self.get_redis_key(session_id))
        if value is None:
            return b''
        return value  # type: ignore

    async def write(self, session_id: str, data: bytes) -> str:
        await self._connection.set(self.get_redis_key(session_id), data, ex=self.expire)
        return session_id

    async def remove(self, session_id: str) -> None:
        await self._connection.delete(self.get_redis_key(session_id))

    async def exists(self, session_id: str) -> bool:
        result: int = await self._connection.exists(self.get_redis_key(session_id))
        return result > 0
