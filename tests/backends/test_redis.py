import os
import typing

import pytest
import redis.asyncio as redis

from starsessions import ImproperlyConfigured
from starsessions.stores.redis import RedisStore

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost")


def redis_key_callable(session_id: str) -> str:
    return f"prefix_{session_id}"


@pytest.mark.parametrize("prefix", ["prefix_", redis_key_callable])
async def test_redis_prefix(prefix: typing.Union[str, typing.Callable[[str], str]]) -> None:
    url = os.environ.get("REDIS_URL", "redis://localhost")
    client = redis.Redis.from_url(url)
    redis_store = RedisStore(prefix=prefix, connection=client)
    async with client:
        new_id = await redis_store.write("session_id", b"data", lifetime=60, ttl=60)
        assert new_id == "session_id"
        assert await redis_store.read("session_id", lifetime=60) == b"data"
        assert await client.get("prefix_session_id") == b"data"


async def test_redis_read_write() -> None:
    client = redis.Redis.from_url(REDIS_URL)
    redis_store = RedisStore(connection=client)
    async with client:
        new_id = await redis_store.write("session_id", b"data", lifetime=60, ttl=60)
        assert new_id == "session_id"
        assert await redis_store.read("session_id", lifetime=60) == b"data"


async def test_redis_write_with_session_only_setup() -> None:
    client = redis.Redis.from_url(REDIS_URL)
    redis_store = RedisStore(connection=client)
    async with client:
        await redis_store.write("session_id", b"data", lifetime=0, ttl=0)


async def test_redis_remove() -> None:
    client = redis.Redis.from_url(REDIS_URL)
    redis_store = RedisStore(connection=client)
    async with client:
        await redis_store.write("session_id", b"data", lifetime=60, ttl=60)
        await redis_store.remove("session_id")
        assert await redis_store.read("session_id", lifetime=60) == b""


async def test_redis_empty_session() -> None:
    client = redis.Redis.from_url(REDIS_URL)
    redis_store = RedisStore(connection=client)
    async with client:
        assert await redis_store.read("unknown_session_id", lifetime=60) == b""


async def test_redis_requires_url_or_connection() -> None:
    with pytest.raises(ImproperlyConfigured):
        RedisStore()


async def test_redis_uses_url() -> None:
    with pytest.warns(DeprecationWarning):
        store = RedisStore(url="redis://")
        assert isinstance(store._connection, redis.Redis)
        await store._connection.aclose()
