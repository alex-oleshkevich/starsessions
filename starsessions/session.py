from __future__ import annotations

import secrets
import time
import typing

from starlette.requests import HTTPConnection

from starsessions.encryptors import Encryptor
from starsessions.exceptions import SessionNotLoaded
from starsessions.serializers import Serializer
from starsessions.stores import SessionStore
from starsessions.types import SessionMetadata


def generate_session_id() -> str:
    """Generate a new, cryptographically strong session ID."""
    return secrets.token_hex(16)


def regenerate_session_id(connection: HTTPConnection) -> str:
    """
    Generate new session ID and set it as current session ID.

    Returns new session ID.
    """
    return get_session_handler(connection).regenerate_id()


def get_session_id(connection: HTTPConnection) -> str | None:
    """Get current session ID."""
    return get_session_handler(connection).session_id


def get_session_handler(connection: HTTPConnection) -> SessionHandler:
    """
    Get session handler.

    Session handler is a tool for low level session management.
    """
    return typing.cast(SessionHandler, connection.scope["session_handler"])


async def load_session(connection: HTTPConnection) -> None:
    """
    Initialize session.

    Will replace any existing session data. Should be called once per request.
    """

    await get_session_handler(connection).load()


def is_loaded(connection: HTTPConnection) -> bool:
    """Test if session has been loaded for this connection."""
    return get_session_handler(connection).is_loaded


def get_session_metadata(connection: HTTPConnection) -> SessionMetadata:
    """
    Get session metadata. The session must be loaded first otherwise it raises.

    :raise SessionNotLoaded: if session is not loaded.
    """
    if not is_loaded(connection):
        raise SessionNotLoaded("Cannot read session metadata because session was not loaded.")

    metadata = get_session_handler(connection).metadata
    assert metadata  # satisfy mypy
    return metadata


def get_session_remaining_seconds(connection: HTTPConnection) -> int:
    """Get total seconds remaining before this session expires."""
    now = time.time()
    metadata = get_session_metadata(connection)
    return int((metadata["created"] + metadata["lifetime"]) - now)


class SessionHandler:
    """
    A tool for low level session management.

    This is private API, no backward compatibility guarantee.
    """

    def __init__(
        self,
        connection: HTTPConnection,
        session_id: str | None,
        store: SessionStore,
        serializer: Serializer,
        encryptor: Encryptor,
        lifetime: int,
    ) -> None:
        self.connection = connection
        self.session_id = session_id
        self.store = store
        self.serializer = serializer
        self.encryptor = encryptor
        self.is_loaded = False
        self.initially_empty = False
        self.lifetime = lifetime
        self.metadata: SessionMetadata | None = None
        self._remove_data_for_session: str | None = None

    async def load(self) -> None:
        # don't refresh existing session, it may contain user data
        if self.is_loaded:  # pragma: no cover
            return

        self.is_loaded = True
        data = {}
        if self.session_id:
            raw = await self.store.read(session_id=self.session_id, lifetime=self.lifetime)
            try:
                data = self.serializer.deserialize(self.encryptor.decrypt(raw))
            except Exception:
                data = {}

        # read and merge metadata
        metadata = {
            "lifetime": self.lifetime,
            "created": time.time(),
            "last_access": time.time(),
        }
        metadata.update(data.pop("__metadata__", {}))
        metadata.update(
            {
                "last_access": time.time(),
                "lifetime": self.lifetime,
            },
        )  # force update
        self.metadata = metadata  # type: ignore[assignment]

        self.connection.scope["session"] = {}
        self.connection.session.update(data)

        self.initially_empty = len(self.connection.session) == 0

    async def save(self, remaining_time: int) -> str:
        self.connection.session.update({"__metadata__": self.metadata})

        self.session_id = await self.store.write(
            session_id=self.session_id or generate_session_id(),
            data=self.encryptor.encrypt(
                self.serializer.serialize(self.connection.session),
            ),
            lifetime=self.lifetime,
            ttl=remaining_time,
        )
        if self._remove_data_for_session:
            await self.store.remove(self._remove_data_for_session)
            self._remove_data_for_session = None
        return self.session_id

    async def destroy(self) -> None:
        """Destroy session."""
        if self.session_id:
            await self.store.remove(self.session_id)

    @property
    def is_empty(self) -> bool:
        return len(self.connection.session) == 0

    def regenerate_id(self) -> str:
        self._remove_data_for_session = self.session_id
        self.session_id = generate_session_id()
        return self.session_id
