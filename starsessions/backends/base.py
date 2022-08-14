import abc


class SessionBackend(abc.ABC):  # pragma: no cover
    """Base class for session backends."""

    @abc.abstractmethod
    async def read(self, session_id: str) -> bytes:
        """Read session data from the storage."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def write(self, session_id: str, data: bytes) -> str:
        """
        Write session data to the storage.

        Must return session ID. Either new or from arguments..
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def remove(self, session_id: str) -> None:
        """Remove session data from the storage."""
        raise NotImplementedError()

    @abc.abstractmethod
    async def exists(self, session_id: str) -> bool:
        """Test if storage contains session data for a given session_id."""
        raise NotImplementedError()
