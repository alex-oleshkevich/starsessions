import pytest

from starsessions.backends.base import SessionBackend
from starsessions.backends.redis import RedisBackend
from starsessions.session import Session


@pytest.mark.asyncio
async def test_redis_read_write(redis_backend: SessionBackend) -> None:
    new_id = await redis_backend.write("session_id", b'data')
    assert new_id == "session_id"
    assert await redis_backend.read("session_id") == b'data'


@pytest.mark.asyncio
async def test_redis_remove(redis_backend: SessionBackend) -> None:
    await redis_backend.write("session_id", b'data')
    await redis_backend.remove("session_id")
    assert await redis_backend.exists("session_id") is False


@pytest.mark.asyncio
async def test_redis_exists(redis_backend: SessionBackend) -> None:
    await redis_backend.write("session_id", b'data')
    assert await redis_backend.exists("session_id") is True
    assert await redis_backend.exists("other id") is False


@pytest.mark.asyncio
async def test_redis_empty_session(redis_backend: SessionBackend) -> None:
    assert await redis_backend.read("unknown_session_id") == b''


def test_session_is_empty(redis_session: Session) -> None:
    assert redis_session.is_empty is True

    redis_session["key"] = "value"
    assert redis_session.is_empty is False


def test_session_is_modified(redis_session: Session) -> None:
    assert redis_session.is_modified is False

    redis_session["key"] = "value"
    assert redis_session.is_modified is True


def test_improperly_configured_redis_key() -> None:
    with pytest.raises(Exception):
        RedisBackend(redis_key_func="a_random_string")  # type: ignore[arg-type]
