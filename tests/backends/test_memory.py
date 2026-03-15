from unittest.mock import patch

import pytest

from starsessions.stores import InMemoryStore, SessionStore


@pytest.fixture
def in_memory_store() -> SessionStore:
    return InMemoryStore()


@pytest.mark.asyncio
async def test_in_memory_read_write(in_memory_store: InMemoryStore) -> None:
    new_id = await in_memory_store.write("session_id", b"data", lifetime=60, ttl=60)
    assert new_id == "session_id"
    assert await in_memory_store.read("session_id", lifetime=60) == b"data"


@pytest.mark.asyncio
async def test_in_memory_expires(in_memory_store: InMemoryStore) -> None:
    # ttl=0 falls back to gc_ttl — data must be readable immediately
    new_id = await in_memory_store.write("session_id", b"data", lifetime=0, ttl=0)
    assert new_id == "session_id"
    assert await in_memory_store.read("session_id", lifetime=60) == b"data"
    assert len(in_memory_store.data) == 1

    # ttl=1 — data is readable immediately
    new_id = await in_memory_store.write("session_id", b"data", lifetime=0, ttl=1)
    assert new_id == "session_id"
    assert await in_memory_store.read("session_id", lifetime=60) == b"data"
    assert len(in_memory_store.data) == 1


@pytest.mark.asyncio
async def test_in_memory_ttl_unit_is_seconds(in_memory_store: InMemoryStore) -> None:
    """ttl is in seconds; simulates time advancing past the TTL via time_ns mock."""
    base_ns = 1_000_000_000_000  # arbitrary starting point in ns
    ttl_seconds = 30

    with patch("starsessions.stores.memory.time") as mock_time:
        mock_time.time_ns.return_value = base_ns
        await in_memory_store.write("session_id", b"data", lifetime=60, ttl=ttl_seconds)

        # before expiry: still within TTL
        mock_time.time_ns.return_value = base_ns + (ttl_seconds - 1) * 1_000_000_000
        assert await in_memory_store.read("session_id", lifetime=60) == b"data"

        # after expiry: past TTL
        mock_time.time_ns.return_value = base_ns + (ttl_seconds + 1) * 1_000_000_000
        assert await in_memory_store.read("session_id", lifetime=60) == b""


@pytest.mark.asyncio
async def test_in_memory_remove(in_memory_store: InMemoryStore) -> None:
    await in_memory_store.write("session_id", b"data", lifetime=60, ttl=60)
    await in_memory_store.remove("session_id")
    assert await in_memory_store.read("session_id", lifetime=60) == b""

    # should not fail on missing key
    await in_memory_store.remove("missing")
