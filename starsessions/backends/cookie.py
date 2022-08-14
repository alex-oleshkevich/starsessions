import typing
from base64 import b64decode, b64encode
from itsdangerous import BadSignature, TimestampSigner
from starlette.datastructures import Secret

from starsessions.backends.base import SessionBackend


class CookieBackend(SessionBackend):
    """Stores session data in the browser's cookie as a signed string."""

    def __init__(self, secret_key: typing.Union[str, Secret], max_age: int):
        self._signer = TimestampSigner(str(secret_key))
        self._max_age = max_age

    async def read(self, session_id: str) -> bytes:
        """A session_id is a signed session value."""
        try:
            data = self._signer.unsign(session_id, max_age=self._max_age)
            return b64decode(data)
        except BadSignature:
            return b''

    async def write(self, session_id: str, data: bytes) -> str:
        """The data is a session id in this backend."""
        encoded_data = b64encode(data)
        return self._signer.sign(encoded_data).decode("utf-8")

    async def remove(self, session_id: str) -> None:
        """Session data stored on client side - no way to remove it."""

    async def exists(self, session_id: str) -> bool:
        return False
