import re
import typing as t
from starlette.datastructures import URL, MutableHeaders, Secret
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from . import CookieBackend, SessionBackend
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
        secret_key: t.Union[str, Secret] = None,
        backend: SessionBackend = None,
        exclude_patterns: t.List[t.Union[str, t.Pattern]] = None,
        include_patterns: t.List[t.Union[str, t.Pattern]] = None,
    ) -> None:
        if exclude_patterns is not None and include_patterns is not None:
            raise ValueError('"exclude_patterns" and "include_patterns" are mutually exclusive.')
        self._exclude_patterns = exclude_patterns or []
        self._include_patterns = include_patterns or []

        self.app = app
        if backend is None:
            if secret_key is None:
                raise ImproperlyConfigured("CookieBackend requires secret_key argument.")
            backend = CookieBackend(secret_key, max_age)

        self.backend = backend
        self.session_cookie = session_cookie
        self.max_age = max_age
        self.autoload = autoload
        self.security_flags = "httponly; samesite=" + same_site
        if https_only:  # Secure flag can be used with HTTPS only
            self.security_flags += "; secure"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        session_id = connection.cookies.get(self.session_cookie, None)

        scope["session"] = Session(self.backend, session_id)
        if self._should_autoload(scope):
            await scope["session"].load()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                path = scope.get("root_path", "") or "/"
                if scope["session"].is_modified:
                    # We have session data to persist (data was changed, cleared, etc).
                    nonlocal session_id
                    session_id = await scope["session"].persist()

                    headers = MutableHeaders(scope=message)
                    header_value = "%s=%s; path=%s; Max-Age=%d; %s" % (
                        self.session_cookie,
                        session_id,
                        path,
                        self.max_age,
                        self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
                elif scope["session"].is_loaded and scope["session"].is_empty:
                    # no interactions to session were done
                    headers = MutableHeaders(scope=message)
                    header_value = "{}={}; {}".format(
                        self.session_cookie,
                        f"null; path={path}; expires=Thu, 01 Jan 1970 00:00:00 GMT;",
                        self.security_flags,
                    )
                    headers.append("Set-Cookie", header_value)
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _should_autoload(self, scope: Scope) -> bool:
        if self.autoload:
            return True

        url = URL(scope=scope)
        for pattern in self._exclude_patterns:
            if re.search(pattern, str(url)):
                return True

        return bool(self._include_patterns and any(re.search(pattern, str(url)) for pattern in self._include_patterns))
