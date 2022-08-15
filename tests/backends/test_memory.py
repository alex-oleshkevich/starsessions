import pytest

from starsessions.stores import InMemoryStore, SessionStore


@pytest.fixture()
def in_memory_store() -> SessionStore:
    return InMemoryStore()


@pytest.mark.asyncio
async def test_in_memory_read_write(in_memory_store: SessionStore) -> None:
    new_id = await in_memory_store.write("session_id", b"data", ttl=60)
    assert new_id == "session_id"
    assert await in_memory_store.read("session_id", lifetime=60) == b"data"


@pytest.mark.asyncio
async def test_in_memory_remove(in_memory_store: SessionStore) -> None:
    await in_memory_store.write("session_id", b"data", ttl=60)
    await in_memory_store.remove("session_id")
    assert await in_memory_store.exists("session_id") is False


@pytest.mark.asyncio
async def test_in_memory_exists(in_memory_store: SessionStore) -> None:
    await in_memory_store.write("session_id", b"data", ttl=60)
    assert await in_memory_store.exists("session_id") is True
    assert await in_memory_store.exists("other id") is False
