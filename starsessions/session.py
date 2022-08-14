from __future__ import annotations

import secrets
import typing
from starlette.requests import HTTPConnection

from starsessions.backends import SessionBackend
from starsessions.serializers import Serializer


def generate_session_id() -> str:
    """Generate a new, cryptographically strong session ID."""
    return secrets.token_hex(128)


def regenerate_session_id(connection: HTTPConnection) -> str:
    """
    Generate new session ID and set it as current session ID.

    Returns new session ID.
    """
    return get_session_handler(connection).regenerate_id()


def get_session_id(connection: HTTPConnection) -> typing.Optional[str]:
    """Get current session ID."""
    return get_session_handler(connection).session_id


def get_session_handler(connection: HTTPConnection) -> SessionHandler:
    """
    Get session handler.

    Session handler is a tool for low level session management.
    """
    return typing.cast(SessionHandler, connection.scope['session_handler'])


async def load_session(connection: HTTPConnection) -> None:
    """
    Initialize session.

    Will replace any existing session data. Should be called once per request.
    """

    await get_session_handler(connection).load()


def is_loaded(connection: HTTPConnection) -> bool:
    """Test if session has been loaded for this connection."""
    return get_session_handler(connection).is_loaded


class SessionHandler:
    """
    A tool for low level session management.

    This is private API, no backward compatibility guarantee.
    """

    def __init__(
        self,
        connection: HTTPConnection,
        session_id: typing.Optional[str],
        backend: SessionBackend,
        serializer: Serializer,
    ) -> None:
        self.connection = connection
        self.session_id = session_id
        self.backend = backend
        self.serializer = serializer
        self.is_loaded = False
        self.initially_empty = False

    async def load(self) -> None:
        self.is_loaded = True
        data = {}
        if self.session_id:
            data = self.serializer.deserialize(
                await self.backend.read(self.session_id),
            )

        self.connection.session.clear()  # replace session contents to avoid mixing existing and new session data
        self.connection.session.update(data)

        self.initially_empty = len(self.connection.session) == 0

    async def save(self) -> str:
        self.session_id = await self.backend.write(
            self.session_id or generate_session_id(),
            self.serializer.serialize(self.connection.session),
        )
        return self.session_id

    @property
    def is_empty(self) -> bool:
        return len(self.connection.session) == 0

    def regenerate_id(self) -> str:
        self.session_id = generate_session_id()
        return self.session_id
