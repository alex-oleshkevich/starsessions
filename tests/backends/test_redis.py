import asyncio
import httpx
import os
import pytest
from pytest_asyncio.plugin import SubRequest
from starlette.requests import HTTPConnection
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from starsessions import SessionMiddleware
from starsessions.session import load_session
from starsessions.stores.base import SessionStore
from starsessions.stores.redis import RedisStore


def redis_key_callable(session_id: str) -> str:
    return f"this:is:a:redis:key:{session_id}"


@pytest.fixture(params=["prefix_", redis_key_callable], ids=["using string", "using redis_key_callable"])
def redis_store(request: SubRequest) -> SessionStore:
    redis_key = request.param
    url = os.environ.get("REDIS_URL", "redis://localhost")
    return RedisStore(url, prefix=redis_key)


@pytest.mark.asyncio
async def test_redis_read_write(redis_store: SessionStore) -> None:
    new_id = await redis_store.write("session_id", b"data", lifetime=60, ttl=60)
    assert new_id == "session_id"
    assert await redis_store.read("session_id", lifetime=60) == b"data"


@pytest.mark.asyncio
async def test_redis_write_with_session_only_setup(redis_store: SessionStore) -> None:
    await redis_store.write("session_id", b"data", lifetime=0, ttl=0)


@pytest.mark.asyncio
async def test_redis_remove(redis_store: SessionStore) -> None:
    await redis_store.write("session_id", b"data", lifetime=60, ttl=60)
    await redis_store.remove("session_id")
    assert await redis_store.exists("session_id") is False


@pytest.mark.asyncio
async def test_redis_exists(redis_store: SessionStore) -> None:
    await redis_store.write("session_id", b"data", lifetime=60, ttl=60)
    assert await redis_store.exists("session_id") is True
    assert await redis_store.exists("other id") is False


@pytest.mark.asyncio
async def test_redis_empty_session(redis_store: SessionStore) -> None:
    assert await redis_store.read("unknown_session_id", lifetime=60) == b""


@pytest.mark.asyncio
async def test_redis_concurrent_sessions() -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)

        if connection.url.path == "/login":
            connection.session["logged_user"] = "joe"

        elif connection.url.path == "/logout":
            # just ensure a concurrent request can start
            await asyncio.sleep(1)
            connection.session.clear()

        elif connection.url.path == "/slow":
            # just ensure we are slower that logout method
            await asyncio.sleep(2)

        response = Response(connection.session.get("logged_user", "<not-logged>"))
        await response(scope, receive, send)

    url = os.environ.get("REDIS_URL", "redis://localhost")
    redis_store = RedisStore(url)
    await redis_store.remove("session_id")

    app = SessionMiddleware(app, store=redis_store, lifetime=1000)

    client = httpx.AsyncClient(base_url="http://localhost:80", app=app)

    response = await client.get("/")
    assert response.content == b"<not-logged>"
    session_id = response.cookies.get("session")
    assert session_id is None

    response = await client.get("/login")
    assert response.content == b"joe"
    session_id = response.cookies.get("session")
    assert session_id is not None

    response = await client.get("/", cookies={"session": session_id})
    assert response.content == b"joe"
    assert session_id == response.cookies.get("session")

    # This take 1 second
    task_logout = asyncio.create_task(client.get("/logout", cookies={"session": session_id}))

    # Start another slow request in the meantime
    await asyncio.sleep(0.2)
    task_slow = asyncio.create_task(client.get("/slow", cookies={"session": session_id}))

    # Wait both finished
    await asyncio.gather(task_logout, task_slow)

    # Logout works
    response_logout = task_logout.result()
    assert response_logout.content == b"<not-logged>"
    assert session_id == response.cookies.get("session")

    # Slow start before logout finish, so it's ok to get the logged user
    response_slow = task_slow.result()
    assert response_slow.content == b"joe"
    assert session_id == response.cookies.get("session")

    # Since we logout the session should have vanished, but it doesn't...
    response = await client.get("/", cookies={"session": session_id})
    assert response.content == b"<not-logged>"
