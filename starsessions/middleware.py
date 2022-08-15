import re
import typing
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from starsessions.serializers import JsonSerializer, Serializer
from starsessions.session import SessionHandler, load_session
from starsessions.stores import SessionStore


class SessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        store: SessionStore,
        lifetime: int = 0,  # session-only
        cookie_name: str = "session",
        cookie_same_site: str = "lax",
        cookie_https_only: bool = True,
        cookie_domain: typing.Optional[str] = None,
        cookie_path: typing.Optional[str] = None,
        serializer: typing.Optional[Serializer] = None,
    ) -> None:
        self.app = app
        self.store = store
        self.serializer = serializer or JsonSerializer()
        self.cookie_name = cookie_name
        self.lifetime = lifetime
        self.cookie_domain = cookie_domain
        self.cookie_path = cookie_path
        self.security_flags = "httponly; samesite=" + cookie_same_site
        if cookie_https_only:  # Secure flag can be used with HTTPS only
            self.security_flags += "; secure"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        session_id = connection.cookies.get(self.cookie_name)
        handler = SessionHandler(connection, session_id, self.store, self.serializer, self.lifetime)

        scope["session"] = {}
        scope["session_handler"] = handler

        async def send_wrapper(message: Message) -> None:
            if message["type"] != "http.response.start":
                await send(message)
                return

            if not handler.is_loaded:  # session was not loaded, do nothing
                await send(message)
                return

            nonlocal session_id
            path = self.cookie_path or scope.get("root_path", "") or "/"

            if handler.is_empty:
                # if session was initially empty then do nothing
                if handler.initially_empty:
                    await send(message)
                    return

                # session data loaded but empty, no matter whether it was initially empty or cleared
                # we have to remove the cookie and clear the storage
                if not self.cookie_path or self.cookie_path and scope["path"].startswith(self.cookie_path):
                    headers = MutableHeaders(scope=message)
                    header_value = "{}={}; {}".format(
                        self.cookie_name,
                        f"null; path={path}; expires=Thu, 01 Jan 1970 00:00:00 GMT;",
                        self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
                    await handler.destroy()
                await send(message)
                return

            # persist session data
            session_id = await handler.save()

            headers = MutableHeaders(scope=message)
            header_parts = [
                f"{self.cookie_name}={session_id}",
                f"path={path}",
            ]
            if self.lifetime:
                header_parts.append(f"Max-Age={self.lifetime}")
            if self.cookie_domain:
                header_parts.append(f"Domain={self.cookie_domain}")

            header_parts.append(self.security_flags)
            header_value = "; ".join(header_parts)
            headers.append("Set-Cookie", header_value)

            await send(message)

        await self.app(scope, receive, send_wrapper)


class SessionAutoloadMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        paths: typing.Optional[typing.List[typing.Union[str, typing.Pattern[str]]]] = None,
    ) -> None:
        self.app = app
        self.paths = paths or []

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope, receive)
        if self.should_autoload(connection):
            await load_session(connection)

        await self.app(scope, receive, send)

    def should_autoload(self, connection: HTTPConnection) -> bool:
        if not self.paths:
            return True

        for path in self.paths:
            if re.match(path, connection.url.path):
                return True
        return False
