import datetime
import os
import databases
import pytest
import typing

from databases import Database

from starsessions import ImproperlyConfigured
from starsessions.stores.database import DatabaseStore, create_table, session_data

DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")


@pytest.fixture
async def database() -> typing.AsyncGenerator[Database, None]:
    database = Database(DATABASE_URL)
    await database.connect()
    await create_table(database)

    yield database

    # Clean up
    if DATABASE_URL.startswith("sqlite"):
        await database.execute("DROP TABLE IF EXISTS session_data")
    else:
        await database.execute("DROP TABLE IF EXISTS session_data CASCADE")
    await database.disconnect()


async def test_database_read_write(database: databases.Database) -> None:
    db_store = DatabaseStore(database=database)

    new_id = await db_store.write("session_id", b"data", lifetime=60, ttl=60)
    assert new_id == "session_id"
    assert await db_store.read("session_id", lifetime=60) == b"data"


async def test_database_write_with_session_only_setup(database: databases.Database) -> None:
    db_store = DatabaseStore(database=database)
    await db_store.write("session_id", b"data", lifetime=0, ttl=0)


async def test_database_remove(database: databases.Database) -> None:
    db_store = DatabaseStore(database=database)

    await db_store.write("session_id", b"data", lifetime=60, ttl=60)
    await db_store.remove("session_id")
    assert await db_store.read("session_id", lifetime=60) == b""


async def test_database_empty_session(database: databases.Database) -> None:
    db_store = DatabaseStore(database=database)
    assert await db_store.read("unknown_session_id", lifetime=60) == b""


async def test_database_expired_session(database: databases.Database) -> None:
    db_store = DatabaseStore(database=database)

    # Insert expired session directly
    expires_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
    query = session_data.insert().values(id="expired_session", data=b"expired_data", expires_at=expires_at)
    await database.execute(query)

    assert await db_store.read("expired_session", lifetime=60) == b""

    # Verify it was removed due to expiration
    query = session_data.select().where(session_data.c.id == "expired_session")
    assert await database.fetch_one(query) is None


async def test_database_update_session(database: databases.Database) -> None:
    db_store = DatabaseStore(database=database)

    await db_store.write("session_id", b"initial_data", lifetime=60, ttl=60)
    await db_store.write("session_id", b"updated_data", lifetime=60, ttl=120)
    assert await db_store.read("session_id", lifetime=60) == b"updated_data"


async def test_database_requires_database() -> None:
    with pytest.raises(ImproperlyConfigured):
        DatabaseStore()


async def test_custom_gc_ttl(database: databases.Database) -> None:
    custom_ttl = 3600
    db_store = DatabaseStore(database=database, gc_ttl=custom_ttl)

    await db_store.write("session_id", b"data", lifetime=0, ttl=0)

    # Verify the correct TTL was used
    query = session_data.select().where(session_data.c.id == "session_id")
    result = await database.fetch_one(query)
    expected_expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=custom_ttl)
    assert abs((result["expires_at"] - expected_expires).total_seconds()) < 5
