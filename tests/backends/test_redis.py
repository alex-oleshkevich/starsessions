import os
import pytest
from pytest_asyncio.plugin import SubRequest

from starsessions.backends.base import SessionBackend
from starsessions.backends.redis import RedisBackend


def redis_key_callable(session_id: str) -> str:
    return f"this:is:a:redis:key:{session_id}"


@pytest.fixture(params=[None, redis_key_callable], ids=["default", "using redis_key_callable"])
def redis_backend(request: SubRequest) -> SessionBackend:
    redis_key = request.param
    url = os.environ.get("REDIS_URL", "redis://localhost")
    return RedisBackend(url, redis_key_func=redis_key)


@pytest.mark.asyncio
async def test_redis_read_write(redis_backend: SessionBackend) -> None:
    new_id = await redis_backend.write("session_id", b'data', lifetime=60)
    assert new_id == "session_id"
    assert await redis_backend.read("session_id", lifetime=60) == b'data'


@pytest.mark.asyncio
async def test_redis_write_with_session_only_setup(redis_backend: SessionBackend) -> None:
    await redis_backend.write("session_id", b'data', lifetime=0)


@pytest.mark.asyncio
async def test_redis_remove(redis_backend: SessionBackend) -> None:
    await redis_backend.write("session_id", b'data', lifetime=60)
    await redis_backend.remove("session_id")
    assert await redis_backend.exists("session_id") is False


@pytest.mark.asyncio
async def test_redis_exists(redis_backend: SessionBackend) -> None:
    await redis_backend.write("session_id", b'data', lifetime=60)
    assert await redis_backend.exists("session_id") is True
    assert await redis_backend.exists("other id") is False


@pytest.mark.asyncio
async def test_redis_empty_session(redis_backend: SessionBackend) -> None:
    assert await redis_backend.read("unknown_session_id", lifetime=60) == b''


def test_improperly_configured_redis_key() -> None:
    with pytest.raises(Exception):
        RedisBackend(redis_key_func="a_random_string")  # type: ignore[arg-type]
