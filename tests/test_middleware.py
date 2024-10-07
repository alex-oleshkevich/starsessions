import datetime
import pytest
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse, Response
from starlette.testclient import TestClient
from starlette.types import Receive, Scope, Send

from starsessions import SessionMiddleware, SessionStore
from starsessions.session import load_session


def test_loads_empty_session(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await load_session(connection)

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store)
    client = TestClient(app)
    assert client.get("/").json() == {}


def test_handles_not_existing_session(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await load_session(connection)

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store)
    client = TestClient(app)
    assert client.get("/", cookies={"session": "session_id"}).json() == {}


def test_loads_existing_session(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await store.write("session_id", b'{"key": "value"}', lifetime=60, ttl=60)
        await load_session(connection)

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store)
    client = TestClient(app)
    assert client.get("/", cookies={"session": "session_id"}).json() == {"key": "value"}


def test_send_cookie_if_session_created(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)

        connection.session["key"] = "value"
        response = Response("")
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store)
    client = TestClient(app)
    response = client.get("/")
    assert "session" in response.headers.get("set-cookie")


def test_send_cookie_if_session_updated(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await store.write("session_id", b'{"key2": "value2"}', lifetime=60, ttl=60)
        await load_session(connection)

        connection.session["key"] = "value"
        response = Response("")
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store)
    client = TestClient(app)
    response = client.get("/")
    assert "session" in response.headers.get("set-cookie")


def test_send_cookie_if_session_destroyed(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await store.write("session_id", b'{"key2": "value2"}', lifetime=60, ttl=60)
        await load_session(connection)

        connection.session.clear()
        response = Response("")
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store)
    client = TestClient(app)
    response = client.get("/", cookies={"session": "session_id"})
    assert "session" in response.headers.get("set-cookie")
    assert "01 Jan 1970 00:00:00 GMT" in response.headers.get("set-cookie")


def test_send_cookie_with_domain_if_session_destroyed_and_domain_set(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await store.write("session_id", b'{"key2": "value2"}', lifetime=60, ttl=60)
        await load_session(connection)

        connection.session.clear()
        response = Response("")
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, cookie_domain="example.com")
    client = TestClient(app)
    response = client.get("/", cookies={"session": "session_id"})
    assert "session" in response.headers.get("set-cookie")
    assert "01 Jan 1970 00:00:00 GMT" in response.headers.get("set-cookie")
    assert "domain=example.com" in response.headers["set-cookie"].lower()


@pytest.mark.asyncio
async def test_will_clear_storage_if_session_destroyed(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await store.write("session_id", b'{"key2": "value2"}', lifetime=60, ttl=60)
        await load_session(connection)

        connection.session.clear()
        response = Response("")
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store)
    client = TestClient(app)
    client.get("/", cookies={"session": "session_id"})
    assert await store.read("session_id", lifetime=60) == b""


def test_will_not_send_cookie_if_initially_empty_session_destroyed(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)

        connection.session.clear()
        response = Response("")
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store)
    client = TestClient(app)
    response = client.get("/", cookies={"session": "session_id"})
    assert "set-cookie" not in response.headers


def test_max_age_argument_set_in_cookie(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session["key"] = "value"

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, lifetime=1)
    client = TestClient(app)
    response = client.get("/")

    # requests removes expired cookies from response.cookies,
    assert "max-age" in response.headers.get("set-cookie").lower()


def test_same_site_argument_set_in_cookie(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session["key"] = "value"

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, cookie_same_site="none")
    client = TestClient(app)
    response = client.get("/")

    assert "samesite=none" in response.headers["set-cookie"]


def test_path_argument_set_in_cookie(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session["key"] = "value"

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, cookie_path="/admin")
    client = TestClient(app)
    response = client.get("/")

    assert "path=/admin" in response.headers["set-cookie"].lower()


def test_domain_argument_set_in_cookie(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session["key"] = "value"

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, cookie_domain="example.com")
    client = TestClient(app)
    response = client.get("/")

    assert "domain=example.com" in response.headers["set-cookie"].lower()


def test_set_secure_cookie(store: SessionStore) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session["key"] = "value"

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, cookie_https_only=True)
    client = TestClient(app)
    response = client.get("/")

    assert "secure" in response.headers["set-cookie"].lower()


def test_session_only_cookies(store: SessionStore) -> None:
    """
    When max-age is 0 then we set up a session-only cookie.

    This cookie will expire immediately after closing browser.
    """

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session["key"] = "value"

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, lifetime=0)
    client = TestClient(app)
    response = client.get("/")
    assert "max-age" not in response.headers["set-cookie"].lower()


def test_session_timedelta_lifetime(store: SessionStore) -> None:
    """It should accept datetime.timedelta as lifetime value."""

    async def app(scope: Scope, receive: Receive, send: Send) -> None:  # pragma: nocover
        pass

    app = SessionMiddleware(app, store=store, lifetime=datetime.timedelta(seconds=60))
    assert app.lifetime == 60
