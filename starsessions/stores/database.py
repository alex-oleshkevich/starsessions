import datetime
import typing

import databases

from sqlalchemy.schema import CreateTable
from sqlalchemy import Column, String, LargeBinary, DateTime, MetaData, Table

from starsessions.exceptions import ImproperlyConfigured
from starsessions.stores.base import SessionStore

metadata = MetaData()

session_data = Table(
    "session_data",
    metadata,
    Column("id", String, primary_key=True),
    Column("data", LargeBinary),
    Column("expires_at", DateTime, index=True),
)


async def create_table(database: databases.Database, if_not_exists: bool = True) -> None:
    """
    Create the session_data table in the database, this is for use
    during development or testing.

    In normal operation Alembic should be used to create tables.

    :param database: A databases.Database instance.
    :param if_not_exists: Set `if_not_exists=False` if you want the
    query to throw an exception when the table already exists.
    """
    for table in metadata.tables.values():
        schema = CreateTable(table, if_not_exists=if_not_exists)
        query = str(schema.compile())
        await database.execute(query=query)


class DatabaseStore(SessionStore):
    """Stores session data in a database using SQLAlchemy."""

    def __init__(self, database: typing.Optional[databases.Database] = None, gc_ttl: int = 3600 * 24 * 30) -> None:
        """Initialize the session with a Database instance.

        :param database: A databases.Database instance
        :param gc_ttl: TTL for sessions that have no expiration time
        """

        if not database:
            raise ImproperlyConfigured("'database' argument must be provided.")

        self.database = database
        self.gc_ttl = gc_ttl

    async def read(self, session_id: str, lifetime: int) -> bytes:
        """Read session data from the database."""
        query = session_data.select().where(session_data.c.id == session_id)
        result = await self.database.fetch_one(query)
        if result is None:
            return b""

        if result["expires_at"] < datetime.datetime.utcnow():
            await self.remove(session_id)
            return b""

        return bytes(result["data"])

    async def write(self, session_id: str, data: bytes, lifetime: int, ttl: int) -> str:
        """Write session data to the database."""
        if lifetime == 0:
            # Use gc_ttl for session-only cookies, as zero is not a valid expiry value
            ttl = self.gc_ttl

        ttl = max(1, ttl)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=ttl)

        query = session_data.select().where(session_data.c.id == session_id)
        existing = await self.database.fetch_one(query)

        if existing:
            query = (
                session_data.update().where(session_data.c.id == session_id).values(data=data, expires_at=expires_at)
            )
        else:
            query = session_data.insert().values(id=session_id, data=data, expires_at=expires_at)

        await self.database.execute(query)
        return session_id

    async def remove(self, session_id: str) -> None:
        """Remove session data from the database."""
        query = session_data.delete().where(session_data.c.id == session_id)
        await self.database.execute(query)
