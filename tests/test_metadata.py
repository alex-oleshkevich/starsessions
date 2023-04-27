import json
import pytest
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.types import Receive, Scope, Send
from unittest import mock

from starsessions import SessionMiddleware, SessionNotLoaded, SessionStore
from starsessions.session import get_session_metadata, load_session


def test_requires_loaded_session(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:  # pragma: nocover
        connection = HTTPConnection(scope, receive)
        response = JSONResponse(get_session_metadata(connection))
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store)
    client = TestClient(app)
    with pytest.raises(SessionNotLoaded, match="Cannot read session metadata because session was not loaded."):
        assert client.get("/").json() == {}


def test_load_should_create_new_metadata(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)

        response = JSONResponse(get_session_metadata(connection))
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, lifetime=1209600)
    client = TestClient(app)
    with mock.patch("time.time", lambda: 1660556520):
        assert client.get("/", cookies={"session": "session_id"}).json() == {
            "created": 1660556520,
            "last_access": 1660556520,
            "lifetime": 1209600,
        }


def test_load_should_not_overwrite_created_timestamp(store: SessionStore) -> None:
    metadata = {"created": 42, "last_access": 0, "lifetime": 0}

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        await store.write("session_id", json.dumps({"__metadata__": metadata}).encode(), lifetime=60, ttl=60)

        connection = HTTPConnection(scope, receive)
        await load_session(connection)

        response = JSONResponse(get_session_metadata(connection))
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, lifetime=1209600)
    client = TestClient(app)
    with mock.patch("time.time", lambda: 1660556520):
        assert client.get("/", cookies={"session": "session_id"}).json() == {
            "created": 42,
            "last_access": 1660556520,
            "lifetime": 0,
        }


def test_should_update_last_access_time_on_load(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)

        connection.session["key"] = "value"  # change session to trigger save

        response = JSONResponse(get_session_metadata(connection))
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, lifetime=1209600)
    client = TestClient(app)
    with mock.patch("time.time", lambda: 1660556520):
        assert client.get("/", cookies={"session": "session_id"}).json() == {
            "created": 1660556520,
            "last_access": 1660556520,
            "lifetime": 1209600,
        }

    with mock.patch("time.time", lambda: 1660556000):
        assert client.get("/", cookies={"session": "session_id"}).json() == {
            "created": 1660556520,
            "last_access": 1660556000,
            "lifetime": 1209600,
        }
