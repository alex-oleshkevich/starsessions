import typing
from starlette.datastructures import MutableHeaders, Secret
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .backends import CookieBackend, SessionBackend
from .session import ImproperlyConfigured, Session


class SessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        session_cookie: str = "session",
        max_age: int = 14 * 24 * 60 * 60,  # 14 days, in seconds
        same_site: str = "lax",
        https_only: bool = False,
        autoload: bool = False,
        domain: str = None,
        path: str = None,
        secret_key: typing.Union[str, Secret] = None,
        backend: SessionBackend = None,
    ) -> None:
        self.app = app
        if backend is None:
            if secret_key is None:
                raise ImproperlyConfigured("CookieBackend requires secret_key argument.")
            backend = CookieBackend(secret_key, max_age)

        self.backend = backend
        self.session_cookie = session_cookie
        self.max_age = max_age
        self.autoload = autoload
        self.domain = domain
        self.path = path
        self.security_flags = "httponly; samesite=" + same_site
        if https_only:  # Secure flag can be used with HTTPS only
            self.security_flags += "; secure"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        session_id = connection.cookies.get(self.session_cookie, None)

        session = Session(self.backend, session_id)
        scope["session"] = session
        if self.autoload:
            await session.load()

        async def send_wrapper(message: Message) -> None:
            if message["type"] != "http.response.start":
                return await send(message)

            if not session.is_loaded:  # session was not accessed, do nothing
                return await send(message)

            nonlocal session_id
            path = self.path or scope.get("root_path", "") or "/"

            if session.is_empty:
                # session data loaded but empty, no matter whether it was initially empty or cleared
                # we have to remove the cookie and clear the storage
                if not self.path or self.path and scope['path'].startswith(self.path):
                    headers = MutableHeaders(scope=message)
                    header_value = "{}={}; {}".format(
                        self.session_cookie,
                        f"null; path={path}; expires=Thu, 01 Jan 1970 00:00:00 GMT;",
                        self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
                    await self.backend.remove(scope['session'].session_id)
                return await send(message)

            # persist session data
            session_id = await session.persist()

            headers = MutableHeaders(scope=message)
            header_parts = [
                f'{self.session_cookie}={session_id}',
                f'path={path}',
            ]
            if self.max_age:
                header_parts.append(f'Max-Age={self.max_age}')
            if self.domain:
                header_parts.append(f'Domain={self.domain}')

            header_parts.append(self.security_flags)
            header_value = '; '.join(header_parts)
            headers.append("Set-Cookie", header_value)

            await send(message)

        await self.app(scope, receive, send_wrapper)
