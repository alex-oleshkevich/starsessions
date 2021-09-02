import abc
import typing
import uuid


class SessionBackend(abc.ABC):
    """Base class for session backends."""

    @abc.abstractmethod
    async def read(
        self, session_id: str
    ) -> typing.Dict[str, typing.Any]:  # pragma: no cover
        """Read session data from the storage."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def write(
        self, data: typing.Dict, session_id: typing.Optional[str] = None
    ) -> str:  # pragma: no cover
        """Write session data to the storage."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def remove(self, session_id: str) -> None:  # pragma: no cover
        """Remove session data from the storage."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def exists(self, session_id: str) -> bool:  # pragma: no cover
        """Test if storage contains session data for a given session_id."""
        raise NotImplementedError()

    async def generate_id(self) -> str:
        """Generate a new session id."""
        return str(uuid.uuid4())
