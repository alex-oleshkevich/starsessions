import pytest
from starlette.requests import HTTPConnection

from starsessions import Serializer, SessionStore
from starsessions.session import (
    SessionHandler,
    generate_session_id,
    get_session_handler,
    get_session_id,
    is_loaded,
    load_session,
    regenerate_session_id,
)


def test_generate_session_id() -> None:
    assert len(generate_session_id()) == 32


def test_regenerate_session_id(store: SessionStore, serializer: Serializer) -> None:
    scope = {"type": "http"}
    base_session_id = "some_id"
    connection = HTTPConnection(scope)
    connection.scope["session"] = {}
    connection.scope["session_handler"] = SessionHandler(connection, base_session_id, store, serializer, lifetime=60)

    session_id = regenerate_session_id(connection)
    assert session_id
    assert session_id != base_session_id


def test_get_session_id(store: SessionStore, serializer: Serializer) -> None:
    scope = {"type": "http"}
    base_session_id = "some_id"
    connection = HTTPConnection(scope)
    connection.scope["session"] = {}
    connection.scope["session_handler"] = SessionHandler(connection, base_session_id, store, serializer, lifetime=60)

    session_id = get_session_id(connection)
    assert session_id == base_session_id


def test_get_session_handler(store: SessionStore, serializer: Serializer) -> None:
    scope = {"type": "http"}
    base_session_id = "some_id"
    connection = HTTPConnection(scope)
    connection.scope["session"] = {}
    connection.scope["session_handler"] = SessionHandler(connection, base_session_id, store, serializer, lifetime=60)

    assert get_session_handler(connection) == connection.scope["session_handler"]


@pytest.mark.asyncio
async def test_load_session(store: SessionStore, serializer: Serializer) -> None:
    scope = {"type": "http"}
    base_session_id = "session_id"
    connection = HTTPConnection(scope)
    connection.scope["session"] = {}
    connection.scope["session_handler"] = SessionHandler(connection, base_session_id, store, serializer, lifetime=60)

    await store.write("session_id", b'{"key": "value"}', lifetime=60)
    await load_session(connection)
    assert is_loaded(connection)
    assert connection.session == {"key": "value"}
