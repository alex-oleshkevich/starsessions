import pytest
from starlette.requests import HTTPConnection

from starsessions import Serializer, SessionStore
from starsessions.encryptors import Encryptor
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


async def test_regenerate_session_id(store: SessionStore, serializer: Serializer, encryptor: Encryptor) -> None:
    scope = {"type": "http"}
    base_session_id = "some_id"
    connection = HTTPConnection(scope)
    connection.scope["session"] = {"abc": "value"}
    connection.scope["session_handler"] = SessionHandler(
        connection, base_session_id, store, serializer, encryptor, lifetime=60
    )

    await store.write(base_session_id, b"value", 3600, 3600)
    assert await store.read(base_session_id, 3600) == b"value"
    session_id = regenerate_session_id(connection)
    assert session_id
    assert session_id != base_session_id


def test_get_session_id(store: SessionStore, serializer: Serializer, encryptor: Encryptor) -> None:
    scope = {"type": "http"}
    base_session_id = "some_id"
    connection = HTTPConnection(scope)
    connection.scope["session"] = {}
    connection.scope["session_handler"] = SessionHandler(
        connection, base_session_id, store, serializer, encryptor, lifetime=60
    )

    session_id = get_session_id(connection)
    assert session_id == base_session_id


def test_get_session_handler(store: SessionStore, serializer: Serializer, encryptor: Encryptor) -> None:
    scope = {"type": "http"}
    base_session_id = "some_id"
    connection = HTTPConnection(scope)
    connection.scope["session"] = {}
    connection.scope["session_handler"] = SessionHandler(
        connection, base_session_id, store, serializer, encryptor, lifetime=60
    )

    assert get_session_handler(connection) == connection.scope["session_handler"]


@pytest.mark.asyncio
async def test_load_session(store: SessionStore, serializer: Serializer, encryptor: Encryptor) -> None:
    scope = {"type": "http"}
    base_session_id = "session_id"
    connection = HTTPConnection(scope)
    connection.scope["session"] = {}
    connection.scope["session_handler"] = SessionHandler(
        connection, base_session_id, store, serializer, encryptor, lifetime=60
    )

    await store.write("session_id", b'{"key": "value"}', lifetime=60, ttl=60)
    await load_session(connection)
    assert is_loaded(connection)
    assert connection.session == {"key": "value"}


async def test_regenerate_id_removes_old_session_on_save(
    store: SessionStore, serializer: Serializer, encryptor: Encryptor
) -> None:
    old_id = "old_session_id"
    await store.write(old_id, b'{"key": "value"}', lifetime=60, ttl=60)

    scope = {"type": "http"}
    connection = HTTPConnection(scope)
    connection.scope["session"] = {}
    connection.scope["session_handler"] = SessionHandler(connection, old_id, store, serializer, encryptor, lifetime=60)

    await load_session(connection)
    handler = get_session_handler(connection)
    handler.regenerate_id()
    await handler.save(remaining_time=60)

    assert await store.read(old_id, lifetime=60) == b""


async def test_destroy_without_session_id(store: SessionStore, serializer: Serializer, encryptor: Encryptor) -> None:
    scope = {"type": "http"}
    connection = HTTPConnection(scope)
    connection.scope["session"] = {}
    connection.scope["session_handler"] = SessionHandler(connection, None, store, serializer, encryptor, lifetime=60)

    await get_session_handler(connection).destroy()
