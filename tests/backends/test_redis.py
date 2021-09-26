import pytest

from starsessions import Session, SessionBackend


@pytest.mark.asyncio
async def test_redis_read_write(redis: SessionBackend, session_payload: dict) -> None:
    new_id = await redis.write(session_payload, "session_id")
    assert new_id == "session_id"
    assert await redis.read("session_id") == session_payload


@pytest.mark.asyncio
async def test_redis_remove(redis: SessionBackend, session_payload: dict) -> None:
    await redis.write(session_payload, "session_id")
    await redis.remove("session_id")
    assert await redis.exists("session_id") is False


@pytest.mark.asyncio
async def test_redis_exists(redis: SessionBackend, session_payload: dict) -> None:
    await redis.write(session_payload, "session_id")
    assert await redis.exists("session_id") is True
    assert await redis.exists("other id") is False


@pytest.mark.asyncio
async def test_redis_generate_id(redis: SessionBackend) -> None:
    new_id = await redis.generate_id()
    assert isinstance(new_id, str)


@pytest.mark.asyncio
async def test_redis_empty_session(redis: SessionBackend) -> None:
    assert await redis.read("unknown_session_id") == {}


def test_session_is_empty(redis_session: Session) -> None:
    assert redis_session.is_empty is True

    redis_session["key"] = "value"
    assert redis_session.is_empty is False


def test_session_is_modified(redis_session: Session) -> None:
    assert redis_session.is_modified is False

    redis_session["key"] = "value"
    assert redis_session.is_modified is True
