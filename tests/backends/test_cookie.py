import pytest

from starsessions import SessionBackend


@pytest.mark.asyncio
async def test_cookie_read_write(cookie: SessionBackend, session_payload: dict) -> None:
    new_id = await cookie.write(session_payload, "session_id")
    assert await cookie.read(new_id) == session_payload


@pytest.mark.asyncio
async def test_cookie_remove(cookie: SessionBackend) -> None:
    await cookie.remove("session_id")


@pytest.mark.asyncio
async def test_cookie_exists(cookie: SessionBackend) -> None:
    assert await cookie.exists("session_id") is False


@pytest.mark.asyncio
async def test_cookie_generate_id(cookie: SessionBackend) -> None:
    new_id = await cookie.generate_id()
    assert isinstance(new_id, str)
