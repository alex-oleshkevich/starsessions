import pytest
import re
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
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


def create_app() -> Starlette:
    app = Starlette()
    app.add_route("/view_session", view_session)
    app.add_route("/update_session", update_session, methods=["POST"])
    app.add_route("/clear_session", clear_session, methods=["POST"])
    return app


def test_session() -> None:
    app = create_app()
    app.add_middleware(SessionMiddleware, secret_key="example", autoload=True)
    client = TestClient(app)

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


def test_empty_session() -> None:
    app = create_app()
    app.add_middleware(SessionMiddleware, secret_key="example", autoload=True)

    headers = {"cookie": "session=someid"}
    client = TestClient(app)
    response = client.get("/view_session", headers=headers)
    assert response.json() == {"session": {}}


def test_session_expires() -> None:
    app = create_app()
    app.add_middleware(SessionMiddleware, secret_key="example", max_age=-1, autoload=True)
    client = TestClient(app)

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


def test_secure_session() -> None:
    app = create_app()
    app.add_middleware(SessionMiddleware, secret_key="example", https_only=True, autoload=True)
    secure_client = TestClient(app, base_url="https://testserver")
    unsecure_client = TestClient(app, base_url="http://testserver")

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
    app = create_app()
    second_app = create_app()
    second_app.add_middleware(SessionMiddleware, secret_key="example", autoload=True)
    app.mount("/second_app", second_app)
    client = TestClient(app, base_url="http://testserver/second_app")
    response = client.post("second_app/update_session", json={"some": "data"})
    cookie = response.headers["set-cookie"]
    match = re.search(r"; path=(\S+);", cookie)
    assert match
    cookie_path = match.groups()[0]
    assert cookie_path == "/second_app"


def test_session_wants_secret_key() -> None:
    with pytest.raises(ImproperlyConfigured):
        app = create_app()
        app.add_middleware(SessionMiddleware)


def test_session_custom_backend() -> None:
    backend = InMemoryBackend()
    app = create_app()
    app.add_middleware(SessionMiddleware, backend=backend, autoload=True)

    headers = {"cookie": "session=someid"}
    client = TestClient(app)
    response = client.get("/view_session", headers=headers)
    assert response.json() == {"session": {}}


def test_session_clears_on_tab_close() -> None:
    app = create_app()
    app.add_middleware(SessionMiddleware, secret_key="example", autoload=True, max_age=0)
    client = TestClient(app)

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
