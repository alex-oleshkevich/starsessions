import typing

from .backends.base import SessionBackend


class SessionError(Exception):
    """Base class for session exceptions."""


class SessionNotLoaded(SessionError):
    pass


class ImproperlyConfigured(SessionError):
    """Exception is raised when some settings are missing or misconfigured."""


class Session:
    def __init__(self, backend: SessionBackend, session_id: str = None) -> None:
        self.session_id = session_id
        self._data: typing.Dict[str, typing.Any] = {}
        self._backend = backend
        self.is_loaded = False
        self._is_modified = False

    @property
    def is_empty(self) -> bool:
        """Check if session has data."""
        return len(self.keys()) == 0

    @property
    def is_modified(self) -> bool:
        """Check if session data has been modified,"""
        return self._is_modified

    @property
    def data(self) -> typing.Dict:
        if not self.is_loaded:
            raise SessionNotLoaded("Session is not loaded.")
        return self._data

    @data.setter
    def data(self, value: typing.Dict[str, typing.Any]) -> None:
        self._data = value

    async def load(self) -> None:
        """Load data from the backend.
        Subsequent calls do not take any effect."""
        if self.is_loaded:
            return

        if not self.session_id:
            self.data = {}
        else:
            self.data = await self._backend.read(self.session_id)

        self.is_loaded = True

    async def persist(self) -> str:
        self.session_id = await self._backend.write(self.data, self.session_id)
        return self.session_id

    async def delete(self) -> None:
        if self.session_id:
            self.data = {}
            self._is_modified = True
            await self._backend.remove(self.session_id)

    async def flush(self) -> str:
        self._is_modified = True
        await self.delete()
        return await self.regenerate_id()

    async def regenerate_id(self) -> str:
        self.session_id = await self._backend.generate_id()
        self._is_modified = True
        return self.session_id

    def keys(self) -> typing.KeysView[str]:
        return self.data.keys()

    def values(self) -> typing.ValuesView[typing.Any]:
        return self.data.values()

    def items(self) -> typing.ItemsView[str, typing.Any]:
        return self.data.items()

    def pop(self, key: str, default: typing.Any = None) -> typing.Any:
        self._is_modified = True
        return self.data.pop(key, default)

    def get(self, name: str, default: typing.Any = None) -> typing.Any:
        return self.data.get(name, default)

    def setdefault(self, key: str, default: typing.Any) -> None:
        self._is_modified = True
        self.data.setdefault(key, default)

    def clear(self) -> None:
        self._is_modified = True
        self.data.clear()

    def update(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self._is_modified = True
        self.data.update(*args, **kwargs)

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __setitem__(self, key: str, value: typing.Any) -> None:
        self._is_modified = True
        self.data[key] = value

    def __getitem__(self, key: str) -> typing.Any:
        return self.data[key]

    def __delitem__(self, key: str) -> None:
        self._is_modified = True
        del self.data[key]
