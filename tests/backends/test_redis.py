from typing import Tuple, Dict

import pytest

from starsessions import Session, SessionBackend
from starsessions.backends.redis import RedisBackend


@pytest.mark.asyncio
async def test_redis_read_write(redis_session_payload: Tuple[SessionBackend, Dict[str, str]]) -> None:
    redis, session_payload = redis_session_payload
    new_id = await redis.write(session_payload, "session_id")
    assert new_id == "session_id"
    assert await redis.read("session_id") == session_payload


@pytest.mark.asyncio
async def test_redis_remove(
    redis_session_payload: Tuple[SessionBackend, Dict[str, str]], session_payload: dict
) -> None:
    redis, session_payload = redis_session_payload
    await redis.write(session_payload, "session_id")
    await redis.remove("session_id")
    assert await redis.exists("session_id") is False


@pytest.mark.asyncio
async def test_redis_exists(
    redis_session_payload: Tuple[SessionBackend, Dict[str, str]], session_payload: dict
) -> None:
    redis, session_payload = redis_session_payload
    await redis.write(session_payload, "session_id")
    assert await redis.exists("session_id") is True
    assert await redis.exists("other id") is False


@pytest.mark.asyncio
async def test_redis_generate_id(redis_session_payload: Tuple[SessionBackend, Dict[str, str]]) -> None:
    redis, session_payload = redis_session_payload
    new_id = await redis.generate_id()
    assert isinstance(new_id, str)


@pytest.mark.asyncio
async def test_redis_empty_session(redis_session_payload: Tuple[SessionBackend, Dict[str, str]]) -> None:
    redis, session_payload = redis_session_payload
    assert await redis.read("unknown_session_id") == {}


def test_session_is_empty(redis_session: Session) -> None:
    assert redis_session.is_empty is True

    redis_session["key"] = "value"
    assert redis_session.is_empty is False


def test_session_is_modified(redis_session: Session) -> None:
    assert redis_session.is_modified is False

    redis_session["key"] = "value"
    assert redis_session.is_modified is True


def test_improperly_configured_redis_key() -> None:
    with pytest.raises(AssertionError):
        RedisBackend(redis_key_func="a_random_string")  # type: ignore[arg-type]
