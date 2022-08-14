import pytest

from starsessions.backends import CookieBackend, SessionBackend


@pytest.fixture()
def cookie_backend() -> SessionBackend:
    return CookieBackend("key", 14)


@pytest.mark.asyncio
async def test_cookie_read_write(cookie_backend: SessionBackend) -> None:
    new_id = await cookie_backend.write("session_id", b'some data')
    assert await cookie_backend.read(new_id) == b'some data'


@pytest.mark.asyncio
async def test_cookie_remove(cookie_backend: SessionBackend) -> None:
    await cookie_backend.remove("session_id")


@pytest.mark.asyncio
async def test_cookie_exists(cookie_backend: SessionBackend) -> None:
    assert await cookie_backend.exists("session_id") is False
