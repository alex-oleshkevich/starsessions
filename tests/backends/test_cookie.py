import pytest


@pytest.mark.asyncio
async def test_cookie_read_write(cookie, session_payload):
    new_id = await cookie.write(session_payload, "session_id")
    assert await cookie.read(new_id) == session_payload


@pytest.mark.asyncio
async def test_cookie_remove(cookie):
    await cookie.remove("session_id")


@pytest.mark.asyncio
async def test_cookie_exists(cookie):
    assert await cookie.exists("session_id") is False


@pytest.mark.asyncio
async def test_cookie_generate_id(cookie):
    new_id = await cookie.generate_id()
    assert isinstance(new_id, str)
