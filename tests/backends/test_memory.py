import pytest
import typing

from starsessions import Session, SessionBackend


@pytest.mark.asyncio  # type: ignore[misc]
async def test_in_memory_read_write(in_memory: SessionBackend, session_payload: typing.Dict[str, typing.Any]) -> None:
    new_id = await in_memory.write(session_payload, "session_id")
    assert new_id == "session_id"
    assert await in_memory.read("session_id") == session_payload


@pytest.mark.asyncio  # type: ignore[misc]
async def test_in_memory_remove(in_memory: SessionBackend, session_payload: typing.Dict[str, typing.Any]) -> None:
    await in_memory.write(session_payload, "session_id")
    await in_memory.remove("session_id")
    assert await in_memory.exists("session_id") is False


@pytest.mark.asyncio  # type: ignore[misc]
async def test_in_memory_exists(in_memory: SessionBackend, session_payload: typing.Dict[str, typing.Any]) -> None:
    await in_memory.write(session_payload, "session_id")
    assert await in_memory.exists("session_id") is True
    assert await in_memory.exists("other id") is False


@pytest.mark.asyncio  # type: ignore[misc]
async def test_in_memory_generate_id(in_memory: SessionBackend) -> None:
    new_id = await in_memory.generate_id()
    assert isinstance(new_id, str)


def test_session_is_empty(in_memory_session: Session) -> None:
    assert in_memory_session.is_empty is True

    in_memory_session["key"] = "value"
    assert in_memory_session.is_empty is False


def test_session_is_modified(in_memory_session: Session) -> None:
    assert in_memory_session.is_modified is False

    in_memory_session["key"] = "value"
    assert in_memory_session.is_modified is True
