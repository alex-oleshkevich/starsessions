import pytest

from starsessions.stores import CookieStore, SessionStore


@pytest.fixture()
def cookie_store() -> SessionStore:
    return CookieStore("key")


@pytest.mark.asyncio
async def test_cookie_read_write(cookie_store: SessionStore) -> None:
    new_id = await cookie_store.write("session_id", b"some data", lifetime=60, ttl=60)
    assert await cookie_store.read(new_id, lifetime=60) == b"some data"


@pytest.mark.asyncio
async def test_cookie_read_data_of_session_only_cookie(
    cookie_store: SessionStore,
) -> None:
    new_id = await cookie_store.write("session_id", b"some data", lifetime=0, ttl=0)
    assert await cookie_store.read(new_id, lifetime=0) == b"some data"


@pytest.mark.asyncio
async def test_cookie_remove(cookie_store: SessionStore) -> None:
    await cookie_store.remove("session_id")


@pytest.mark.asyncio
async def test_returns_empty_string_for_bad_signature(
    cookie_store: SessionStore,
) -> None:
    # the session_id value is a signed session cookie value
    assert await cookie_store.read("session_id", lifetime=10) == b""
