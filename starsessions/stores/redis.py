import aioredis
import functools
import typing

from starsessions.exceptions import ImproperlyConfigured
from starsessions.stores.base import SessionStore


def prefix_factory(prefix: str, key: str) -> str:
    return prefix + key


class RedisStore(SessionStore):
    """Stores session data in a Redis server."""

    def __init__(
        self,
        url: typing.Optional[str] = None,
        connection: typing.Optional[aioredis.Redis] = None,
        prefix: typing.Union[typing.Callable[[str], str], str] = "",
    ) -> None:
        """
        Initializes redis session store. Either `url` or `connection` required. To namespace keys in Redis use `prefix`
        argument. It can be a string or callable that accepts a single string argument and returns new Redis key as
        string.

        :param url:  Redis URL. Defaults to None.
        :param connection: aioredis connection. Defaults to None
        :param prefix: Redis key name prefix or factory.
        """
        if not (url or connection):
            raise ImproperlyConfigured("Either 'url' or 'connection' arguments must be provided.")

        if isinstance(prefix, str):
            prefix = functools.partial(prefix_factory, prefix)

        self.prefix: typing.Callable[[str], str] = prefix
        self._connection: aioredis.Redis = connection or aioredis.from_url(url)  # type: ignore[no-untyped-call]

    async def read(self, session_id: str, lifetime: int) -> bytes:
        value = await self._connection.get(self.prefix(session_id))
        if value is None:
            return b""
        return value  # type: ignore

    async def write(self, session_id: str, data: bytes, ttl: int) -> str:
        # Redis will fail for session-only cookies, as zero is not a valid expiry value.
        # We cannot know the final session duration so set here something close to reality.
        # FIXME: we want something better here
        ttl = max(ttl, 3600)  # 1h
        await self._connection.set(self.prefix(session_id), data, ex=ttl)
        return session_id

    async def remove(self, session_id: str) -> None:
        await self._connection.delete(self.prefix(session_id))

    async def exists(self, session_id: str) -> bool:
        result: int = await self._connection.exists(self.prefix(session_id))
        return result > 0
