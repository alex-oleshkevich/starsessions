import abc


class SessionStore(abc.ABC):  # pragma: no cover
    """Base class for session storages."""

    @abc.abstractmethod
    async def read(self, session_id: str, lifetime: int) -> bytes:
        """
        Read session data from the storage.

        :param session_id: ID associated with session
        :param lifetime: session lifetime duration
        :returns bytes: session data as bytes
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def write(self, session_id: str, data: bytes, ttl: int) -> str:
        """
        Write session data to the storage.

        Must return session ID. Either new or from arguments.

        :param session_id: ID associated with session
        :param data: session data serialized to bytes
        :param ttl: keep session data this amount of time, in seconds
        :returns str: session ID
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def remove(self, session_id: str) -> None:
        """
        Remove session data from the storage.

        :param session_id: ID associated with session
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def exists(self, session_id: str) -> bool:
        """
        Test if storage contains session data for a given session_id.

        :param session_id: ID associated with session
        :returns bool: True if there is data in session store otherwise False.
        """
        raise NotImplementedError()
