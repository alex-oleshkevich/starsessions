import typing
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from starsessions.backends import SessionBackend
from starsessions.serializers import JsonSerializer, Serializer
from starsessions.session import SessionHandler


class SessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        backend: SessionBackend,
        session_cookie: str = "session",
        max_age: int = 14 * 24 * 60 * 60,  # 14 days, in seconds
        same_site: str = "lax",
        https_only: bool = False,
        autoload: bool = False,
        domain: typing.Optional[str] = None,
        path: typing.Optional[str] = None,
        serializer: typing.Optional[Serializer] = None,
    ) -> None:
        self.app = app
        self.backend = backend
        self.serializer = serializer or JsonSerializer()
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
        session_id = connection.cookies.get(self.session_cookie)
        handler = SessionHandler(connection, session_id, self.backend, self.serializer)

        scope["session"] = {}
        scope["session_handler"] = handler

        if self.autoload:
            await handler.load()

        async def send_wrapper(message: Message) -> None:
            if message["type"] != "http.response.start":
                await send(message)
                return

            if not handler.is_loaded:  # session was not loaded, do nothing
                await send(message)
                return

            nonlocal session_id
            path = self.path or scope.get("root_path", "") or "/"

            if handler.is_empty:
                # if session was initially empty then do nothing
                if handler.initially_empty:
                    await send(message)
                    return

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
                    if handler.session_id:
                        await self.backend.remove(handler.session_id)
                await send(message)
                return

            # persist session data
            session_id = await handler.save()

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
