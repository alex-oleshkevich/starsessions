import os
import pytest
from pytest_asyncio.plugin import SubRequest

from starsessions.stores.base import SessionStore
from starsessions.stores.redis import RedisStore


def redis_key_callable(session_id: str) -> str:
    return f"this:is:a:redis:key:{session_id}"


@pytest.fixture(params=['prefix_', redis_key_callable], ids=["using string", "using redis_key_callable"])
def redis_store(request: SubRequest) -> SessionStore:
    redis_key = request.param
    url = os.environ.get("REDIS_URL", "redis://localhost")
    return RedisStore(url, prefix=redis_key)


@pytest.mark.asyncio
async def test_redis_read_write(redis_store: SessionStore) -> None:
    new_id = await redis_store.write("session_id", b'data', lifetime=60)
    assert new_id == "session_id"
    assert await redis_store.read("session_id", lifetime=60) == b'data'


@pytest.mark.asyncio
async def test_redis_write_with_session_only_setup(redis_store: SessionStore) -> None:
    await redis_store.write("session_id", b'data', lifetime=0)


@pytest.mark.asyncio
async def test_redis_remove(redis_store: SessionStore) -> None:
    await redis_store.write("session_id", b'data', lifetime=60)
    await redis_store.remove("session_id")
    assert await redis_store.exists("session_id") is False


@pytest.mark.asyncio
async def test_redis_exists(redis_store: SessionStore) -> None:
    await redis_store.write("session_id", b'data', lifetime=60)
    assert await redis_store.exists("session_id") is True
    assert await redis_store.exists("other id") is False


@pytest.mark.asyncio
async def test_redis_empty_session(redis_store: SessionStore) -> None:
    assert await redis_store.read("unknown_session_id", lifetime=60) == b''
