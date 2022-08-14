import pytest
import typing
from unittest import mock

from starsessions import Session, session
from starsessions.backends import InMemoryBackend, SessionBackend
from starsessions.exceptions import SessionNotLoaded


@pytest.mark.asyncio
async def test_session_load(in_memory: SessionBackend, session_payload: typing.Dict[str, typing.Any]) -> None:
    await in_memory.write("session_id", session_payload)

    session = Session(in_memory, "session_id")
    await session.load()
    assert session.items() == session_payload.items()


@pytest.mark.asyncio
async def test_session_load_with_new_session(
    in_memory: SessionBackend, session_payload: typing.Dict[str, typing.Any]
) -> None:
    session = Session(in_memory)
    await session.load()
    assert len(session.keys()) == 0


@pytest.mark.asyncio
async def test_session_subsequent_load(in_memory: SessionBackend) -> None:
    """It should return the cached data on any sequential call to load()."""
    await in_memory.write("session_id", dict(key="value"))

    session = Session(in_memory, "session_id")
    await session.load()

    assert "key" in session

    # add key2 to session. this value should survive the second load() call
    session["key2"] = "value2"
    await session.load()

    assert "key" in session
    assert "key2" in session


@pytest.mark.asyncio
async def test_session_persist(in_memory: InMemoryBackend) -> None:
    session = Session(in_memory, "session_id")
    await session.load()
    session["key"] = "value"
    new_id = await session.persist()

    # session ID should no change when was passed via arguments
    assert new_id == "session_id"

    assert in_memory.data == {"session_id": {"key": "value"}}


@pytest.mark.asyncio
async def test_session_persist_generates_id(in_memory: SessionBackend, in_memory_session: Session) -> None:
    def _generate_id() -> str:
        return "new_session_id"

    with mock.patch.object(session, 'generate_id', _generate_id):
        await in_memory_session.persist()
        assert in_memory_session.session_id == "new_session_id"


@pytest.mark.asyncio
async def test_session_delete(in_memory: SessionBackend) -> None:
    await in_memory.write("session_id", {})

    session = Session(in_memory, "session_id")
    await session.load()
    session["key"] = "value"
    await session.delete()

    assert await in_memory.exists("session_id") is False
    assert session.is_modified is True
    assert session.is_empty is True

    # it shouldn't fail on non-persisted session
    session = Session(in_memory)
    await session.load()
    await session.delete()

    assert session.is_empty is True
    assert session.is_modified is False


@pytest.mark.asyncio
async def test_session_flush(in_memory: SessionBackend) -> None:
    await in_memory.write("session_id", {"key": "value"})

    session = Session(in_memory, "session_id")
    await session.load()
    new_id = await session.flush()
    assert new_id == session.session_id
    assert new_id != "session_id"
    assert session.is_modified is True
    assert session.is_empty is True

    # it shouldn't fail on non-persisted session
    session = Session(in_memory)
    await session.load()
    await session.flush()
    assert session.is_modified is True
    assert session.is_empty is True


@pytest.mark.asyncio
async def test_session_regenerate_id(in_memory: SessionBackend) -> None:
    session = Session(in_memory, "session_id")
    new_id = await session.regenerate_id()
    assert session.session_id == new_id
    assert session.session_id != "session_id"
    assert session.is_modified is True


def test_session_keys(in_memory_session: Session) -> None:
    in_memory_session["key"] = True
    assert list(in_memory_session.keys()) == ["key"]


def test_session_values(in_memory_session: Session) -> None:
    in_memory_session["key"] = "value"
    assert list(in_memory_session.values()) == ["value"]


def test_session_items(in_memory_session: Session) -> None:
    in_memory_session["key"] = "value"
    in_memory_session["key2"] = "value2"
    assert list(in_memory_session.items()) == [
        ("key", "value"),
        ("key2", "value2"),
    ]


def test_session_pop(in_memory_session: Session) -> None:
    in_memory_session["key"] = "value"
    in_memory_session.pop("key")
    assert "key" not in in_memory_session
    assert in_memory_session.is_modified


def test_session_get(in_memory_session: Session) -> None:
    in_memory_session["key"] = "value"
    assert in_memory_session.get("key") == "value"
    assert in_memory_session.get("key2", "miss") == "miss"
    assert in_memory_session.get("key3") is None


def test_session_setdefault(in_memory_session: Session) -> None:
    in_memory_session.setdefault("key", "value")
    assert in_memory_session.get("key") == "value"
    assert in_memory_session.is_modified is True


def test_session_clear(in_memory_session: Session) -> None:
    in_memory_session["key"] = "value"
    in_memory_session.clear()
    assert in_memory_session.is_empty is True
    assert in_memory_session.is_modified is True


def test_session_update(in_memory_session: Session) -> None:
    in_memory_session.update({"key": "value"})
    assert "key" in in_memory_session
    assert in_memory_session.is_modified is True


def test_session_setitem_and_contains(in_memory_session: Session) -> None:
    # set item
    in_memory_session["key"] = "value"  # __setitem__
    assert "key" in in_memory_session  # __contain__
    assert in_memory_session.is_modified is True


def test_session_getitem(in_memory_session: Session) -> None:
    in_memory_session["key"] = "value"  # __getitem__
    assert in_memory_session["key"] == "value"


def test_session_delitem(in_memory_session: Session) -> None:
    in_memory_session["key"] = "value"
    del in_memory_session["key"]  # __delitem__
    assert "key" not in in_memory_session


def test_session_denies_access_if_not_loaded(in_memory: SessionBackend) -> None:
    session = Session(in_memory)
    with pytest.raises(SessionNotLoaded):
        session.data.keys()

    with pytest.raises(SessionNotLoaded):
        session["key"] = "value"
