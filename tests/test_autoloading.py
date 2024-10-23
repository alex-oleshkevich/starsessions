import re

import pytest
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.types import Receive, Scope, Send

from starsessions import (
    SessionAutoloadMiddleware,
    SessionMiddleware,
    SessionNotLoaded,
    SessionStore,
)


@pytest.mark.asyncio
async def test_always_loads_session(store: SessionStore) -> None:
    await store.write("session_id", b'{"key": "value"}', lifetime=60, ttl=60)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(SessionAutoloadMiddleware(app), store=store)
    client = TestClient(app, cookies={"session": "session_id"})
    assert client.get("/").json() == {"key": "value"}


@pytest.mark.asyncio
async def test_loads_for_string_paths(store: SessionStore) -> None:
    await store.write("session_id", b'{"key": "value"}', lifetime=60, ttl=60)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(SessionAutoloadMiddleware(app, paths=["/admin", "/app"]), store=store)
    client = TestClient(app, cookies={"session": "session_id"})

    with pytest.raises(SessionNotLoaded):
        assert client.get("/").json() == {}

    assert client.get("/app").json() == {"key": "value"}
    assert client.get("/admin").json() == {"key": "value"}
    assert client.get("/app/1/users").json() == {"key": "value"}
    assert client.get("/admin/settings").json() == {"key": "value"}


@pytest.mark.asyncio
async def test_loads_for_regex_paths(store: SessionStore) -> None:
    await store.write("session_id", b'{"key": "value"}', lifetime=60, ttl=60)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    rx_app = re.compile("/app*")
    rx_admin = re.compile("/admin*")

    app = SessionMiddleware(SessionAutoloadMiddleware(app, paths=[rx_admin, rx_app]), store=store)
    client = TestClient(app, cookies={"session": "session_id"})
    with pytest.raises(SessionNotLoaded):
        assert client.get("/").json() == {}

    assert client.get("/app").json() == {"key": "value"}
    assert client.get("/admin").json() == {"key": "value"}
    assert client.get("/app/1/users").json() == {"key": "value"}
    assert client.get("/admin/settings").json() == {"key": "value"}
