import pytest

from starsessions import SessionBackend


@pytest.mark.asyncio
async def test_cookie_read_write(cookie: SessionBackend) -> None:
    new_id = await cookie.write("session_id", b'some data')
    assert await cookie.read(new_id) == b'some data'


@pytest.mark.asyncio
async def test_cookie_remove(cookie: SessionBackend) -> None:
    await cookie.remove("session_id")


@pytest.mark.asyncio
async def test_cookie_exists(cookie: SessionBackend) -> None:
    assert await cookie.exists("session_id") is False
