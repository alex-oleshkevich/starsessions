import pytest

from starsessions.backends import InMemoryBackend, SessionBackend


@pytest.fixture()
def in_memory_backend() -> SessionBackend:
    return InMemoryBackend()


@pytest.mark.asyncio
async def test_in_memory_read_write(in_memory_backend: SessionBackend) -> None:
    new_id = await in_memory_backend.write("session_id", b'data')
    assert new_id == "session_id"
    assert await in_memory_backend.read("session_id") == b'data'


@pytest.mark.asyncio
async def test_in_memory_remove(in_memory_backend: SessionBackend) -> None:
    await in_memory_backend.write("session_id", b'data')
    await in_memory_backend.remove("session_id")
    assert await in_memory_backend.exists("session_id") is False


@pytest.mark.asyncio
async def test_in_memory_exists(in_memory_backend: SessionBackend) -> None:
    await in_memory_backend.write("session_id", b'data')
    assert await in_memory_backend.exists("session_id") is True
    assert await in_memory_backend.exists("other id") is False
