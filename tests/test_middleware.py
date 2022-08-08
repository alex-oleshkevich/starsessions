import pytest
import re
import typing
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from starsessions import ImproperlyConfigured, InMemoryBackend, SessionMiddleware


def view_session(request: Request) -> JSONResponse:
    return JSONResponse({"session": dict(request.session)})


async def update_session(request: Request) -> JSONResponse:
    data = await request.json()
    request.session.update(data)
    return JSONResponse({"session": dict(request.session)})


async def clear_session(request: Request) -> JSONResponse:
    request.session.clear()
    return JSONResponse({"session": dict(request.session)})


def create_app(**middleware_kwargs: typing.Any) -> Starlette:
    return Starlette(
        routes=[
            Route("/view_session", view_session),
            Route("/update_session", update_session, methods=["POST"]),
            Route("/clear_session", clear_session, methods=["POST"]),
        ],
        middleware=[
            Middleware(SessionMiddleware, **middleware_kwargs),
        ],
    )


def test_session_middleware() -> None:
    """Verify common use cases: read session, modify session, and clear session."""
    client = TestClient(
        create_app(secret_key="example", autoload=True),
    )
    response = client.get("/view_session")
    assert response.json() == {"session": {}}

    response = client.post("/update_session", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    # check cookie max-age
    set_cookie = response.headers["set-cookie"]
    max_age_matches = re.search(r"; Max-Age=([0-9]+);", set_cookie)
    assert max_age_matches is not None
    assert int(max_age_matches[1]) == 14 * 24 * 3600

    response = client.get("/view_session")
    assert response.json() == {"session": {"some": "data"}}

    response = client.post("/clear_session")
    assert response.json() == {"session": {}}

    response = client.get("/view_session")
    assert response.json() == {"session": {}}


def test_storage_has_no_data_for_session_id() -> None:
    """Test a case when session ID is set but storage has no value for it."""
    headers = {"cookie": "session=someid"}
    client = TestClient(create_app(secret_key="example", autoload=True))
    response = client.get("/view_session", headers=headers)
    assert response.json() == {"session": {}}


def test_cookie_should_expire_when_max_age_is_in_past() -> None:
    """Session cookie must be removed if current time is greater than session's max age."""
    client = TestClient(create_app(secret_key="example", max_age=-1, autoload=True))

    response = client.post("/update_session", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    # requests removes expired cookies from response.cookies, we need to
    # fetch session id from the headers and pass it explicitly
    expired_cookie_header = response.headers["set-cookie"]
    match = re.search(r"session=([^;]*);", expired_cookie_header)
    assert match
    expired_session_value = match[1]
    response = client.get("/view_session", cookies={"session": expired_session_value})
    assert response.json() == {"session": {}}


def test_secure_session_cookie() -> None:
    """Test that insecure clients (non-TLS) cannot access cookie when https_only=True."""
    secure_client = TestClient(
        create_app(secret_key="example", https_only=True, autoload=True),
        base_url="https://testserver",
    )
    unsecure_client = TestClient(
        create_app(secret_key="example", https_only=True, autoload=True),
        base_url="http://testserver",
    )

    response = unsecure_client.get("/view_session")
    assert response.json() == {"session": {}}

    response = unsecure_client.post("/update_session", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    response = unsecure_client.get("/view_session")
    assert response.json() == {"session": {}}

    response = secure_client.get("/view_session")
    assert response.json() == {"session": {}}

    response = secure_client.post("/update_session", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    response = secure_client.get("/view_session")
    assert response.json() == {"session": {"some": "data"}}

    response = secure_client.post("/clear_session")
    assert response.json() == {"session": {}}

    response = secure_client.get("/view_session")
    assert response.json() == {"session": {}}


def test_session_cookie_subpath() -> None:
    """Sub apps with own session should be separated from the main session by default.
    Cookies for main app and sub apps are separated by path attribute."""
    app = create_app(secret_key="example", autoload=True)
    second_app = create_app(secret_key="example", autoload=True)
    app.mount("/second_app", second_app)

    client = TestClient(app, base_url="http://testserver/second_app")
    response = client.post("second_app/update_session", json={"some": "data"})
    cookie = response.headers["set-cookie"]
    match = re.search(r"; path=(\S+);", cookie)
    assert match
    cookie_path = match.groups()[0]
    assert cookie_path == "/second_app"


def test_session_middleware_wants_secret_key() -> None:
    """When no backend passed to SessionMiddleware then CookieBackend will be used by default.
    This backend needs `secret_key` to sign cookie."""
    with pytest.raises(ImproperlyConfigured):
        create_app()


def test_session_middleware_with_custom_backend() -> None:
    """SessionMiddleware should accept and work with custom backend."""
    backend = InMemoryBackend()

    client = TestClient(create_app(backend=backend, autoload=True))
    response = client.post("/update_session", json={'some': 'data'}, headers={"cookie": "session=someid"})
    assert response.json() == {"session": {'some': 'data'}}
    assert backend.data == {'someid': {'some': 'data'}}, 'Session backend was not updated.'


def test_session_clears_on_browser_exit() -> None:
    """When max-age is 0 then we set up a session-only cookie.
    This cookie will expire immediately after closing browser."""
    client = TestClient(create_app(secret_key="example", autoload=True, max_age=0))

    response = client.get("/view_session")
    assert response.json() == {"session": {}}

    response = client.post("/update_session", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    # when max_age=0 then no Max-Age cookie component expected
    set_cookie = response.headers["set-cookie"]
    assert 'Max-Age' not in set_cookie

    client.cookies.clear_session_cookies()
    response = client.get("/view_session")
    assert response.json() == {"session": {}}


def test_session_cookie_should_be_set_to_custom_path() -> None:
    """We should be able to enable sessions for a specific paths only.
    In this test case, session cookie should be bound to the /admin."""
    client = TestClient(create_app(secret_key="example", autoload=True, path='/admin'))

    response = client.post("/update_session", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    # check cookie max-age
    set_cookie = response.headers["set-cookie"]
    assert 'path=/admin' in set_cookie


def test_session_cookie_domain() -> None:
    """We should be able to bind session cookie to a specific domain.
    In this test case, session cookie should be bound to the example.com domain."""
    client = TestClient(create_app(secret_key="example", autoload=True, domain='example.com'))

    response = client.post("/update_session", json={"some": "data"})
    assert response.json() == {"session": {"some": "data"}}

    # check cookie max-age
    set_cookie = response.headers["set-cookie"]
    assert 'Domain=example.com' in set_cookie


def test_middleware_has_to_clean_storage_after_removing_cookie() -> None:
    """When SessionMiddleware removes cookie it also has to clean the storage."""
    backend = InMemoryBackend()
    client = TestClient(create_app(backend=backend, secret_key="example", autoload=True))

    # set some session data
    client.post("/update_session", json={"some": "data"})
    assert len(backend.data)  # it now contains 1 session

    # clear session data, the middleware has to free storage space
    client.post("/clear_session")
    assert not len(backend.data)  # it now contains zero sessions
