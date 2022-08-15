import typing
from base64 import b64decode, b64encode
from itsdangerous import BadSignature, TimestampSigner
from starlette.datastructures import Secret

from starsessions.stores.base import SessionStore


class CookieStore(SessionStore):
    """Stores session data in the browser's cookie as a signed string."""

    def __init__(self, secret_key: typing.Union[str, Secret]):
        self._signer = TimestampSigner(str(secret_key))

    async def read(self, session_id: str, lifetime: int) -> bytes:
        """A session_id is a signed session value."""
        try:
            data = self._signer.unsign(session_id, max_age=lifetime)
            return b64decode(data)
        except BadSignature:
            return b""

    async def write(self, session_id: str, data: bytes, lifetime: int) -> str:
        """The data is a session id in this storage."""
        encoded_data = b64encode(data)
        return self._signer.sign(encoded_data).decode("utf-8")

    async def remove(self, session_id: str) -> None:
        """Session data stored on client side - no way to remove it."""

    async def exists(self, session_id: str) -> bool:
        return False
