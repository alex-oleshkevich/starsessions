import pytest
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse, Response
from starlette.testclient import TestClient
from starlette.types import Receive, Scope, Send

from starsessions import SessionBackend, SessionMiddleware
from starsessions.session import load_session


def test_loads_empty_session(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await load_session(connection)

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend)
    client = TestClient(app)
    assert client.get('/').json() == {}


def test_handles_not_existing_session(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await load_session(connection)

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend)
    client = TestClient(app)
    assert client.get('/', cookies={'session': 'session_id'}).json() == {}


def test_loads_existing_session(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await backend.write('session_id', b'{"key": "value"}')
        await load_session(connection)

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend)
    client = TestClient(app)
    assert client.get('/', cookies={'session': 'session_id'}).json() == {'key': 'value'}


def test_send_cookie_if_session_created(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)

        connection.session["key"] = "value"
        response = Response('')
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend)
    client = TestClient(app)
    response = client.get('/')
    assert 'session' in response.headers.get('set-cookie')


def test_send_cookie_if_session_updated(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await backend.write('session_id', b'{"key2": "value2"}')
        await load_session(connection)

        connection.session["key"] = "value"
        response = Response('')
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend)
    client = TestClient(app)
    response = client.get('/')
    assert 'session' in response.headers.get('set-cookie')


def test_send_cookie_if_session_destroyed(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await backend.write('session_id', b'{"key2": "value2"}')
        await load_session(connection)

        connection.session.clear()
        response = Response('')
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend)
    client = TestClient(app)
    response = client.get('/', cookies={'session': 'session_id'})
    assert 'session' in response.headers.get('set-cookie')
    assert '01 Jan 1970 00:00:00 GMT' in response.headers.get('set-cookie')


@pytest.mark.asyncio
async def test_will_clear_storage_if_session_destroyed(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        await backend.write('session_id', b'{"key2": "value2"}')
        await load_session(connection)

        connection.session.clear()
        response = Response('')
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend)
    client = TestClient(app)
    client.get('/', cookies={'session': 'session_id'})
    assert not await backend.exists('session_id')


def test_will_not_send_cookie_if_initially_empty_session_destroyed(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)

        connection.session.clear()
        response = Response('')
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend)
    client = TestClient(app)
    response = client.get('/', cookies={'session': 'session_id'})
    assert 'set-cookie' not in response.headers


def test_will_not_send_cookie_if_session_was_not_loaded(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)

        connection.session.clear()
        response = Response('')
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend)
    client = TestClient(app)
    response = client.get('/', cookies={'session': 'session_id'})
    assert 'set-cookie' not in response.headers


def test_max_age_argument_set_in_cookie(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session['key'] = 'value'

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend, max_age=-1)
    client = TestClient(app)
    response = client.get('/')

    # requests removes expired cookies from response.cookies,
    assert 'max-age' in response.headers.get('set-cookie').lower()


def test_same_site_argument_set_in_cookie(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session['key'] = 'value'

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend, same_site='none')
    client = TestClient(app)
    response = client.get('/')

    assert 'samesite=none' in response.headers['set-cookie']


def test_path_argument_set_in_cookie(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session['key'] = 'value'

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend, path='/admin')
    client = TestClient(app)
    response = client.get('/')

    assert 'path=/admin' in response.headers['set-cookie'].lower()


def test_domain_argument_set_in_cookie(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session['key'] = 'value'

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend, domain='example.com')
    client = TestClient(app)
    response = client.get('/')

    assert 'domain=example.com' in response.headers['set-cookie'].lower()


def test_set_secure_cookie(backend: SessionBackend) -> None:
    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session['key'] = 'value'

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend, https_only=True)
    client = TestClient(app)
    response = client.get('/')

    assert 'secure' in response.headers['set-cookie'].lower()


def test_session_only_cookies(backend: SessionBackend) -> None:
    """
    When max-age is 0 then we set up a session-only cookie.

    This cookie will expire immediately after closing browser.
    """

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        connection.session['key'] = 'value'

        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, backend=backend, max_age=0)
    client = TestClient(app)
    response = client.get('/')
    assert 'max-age' not in response.headers['set-cookie'].lower()
