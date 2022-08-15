import pytest
import re
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.types import Receive, Scope, Send

from starsessions import SessionAutoloadMiddleware, SessionBackend, SessionMiddleware


@pytest.mark.asyncio
async def test_always_loads_session(backend: SessionBackend) -> None:
    await backend.write('session_id', b'{"key": "value"}', lifetime=60)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(SessionAutoloadMiddleware(app), backend=backend)
    client = TestClient(app)
    assert client.get('/', cookies={'session': 'session_id'}).json() == {'key': 'value'}


@pytest.mark.asyncio
async def test_loads_for_string_paths(backend: SessionBackend) -> None:
    await backend.write('session_id', b'{"key": "value"}', lifetime=60)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(SessionAutoloadMiddleware(app, paths=['/admin', '/app']), backend=backend)
    client = TestClient(app)
    assert client.get('/', cookies={'session': 'session_id'}).json() == {}
    assert client.get('/app', cookies={'session': 'session_id'}).json() == {'key': 'value'}
    assert client.get('/admin', cookies={'session': 'session_id'}).json() == {'key': 'value'}
    assert client.get('/app/1/users', cookies={'session': 'session_id'}).json() == {'key': 'value'}
    assert client.get('/admin/settings', cookies={'session': 'session_id'}).json() == {'key': 'value'}


@pytest.mark.asyncio
async def test_loads_for_regex_paths(backend: SessionBackend) -> None:
    await backend.write('session_id', b'{"key": "value"}', lifetime=60)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    rx_app = re.compile('/app*')
    rx_admin = re.compile('/admin*')

    app = SessionMiddleware(SessionAutoloadMiddleware(app, paths=[rx_admin, rx_app]), backend=backend)
    client = TestClient(app)
    assert client.get('/', cookies={'session': 'session_id'}).json() == {}
    assert client.get('/app', cookies={'session': 'session_id'}).json() == {'key': 'value'}
    assert client.get('/admin', cookies={'session': 'session_id'}).json() == {'key': 'value'}
    assert client.get('/app/1/users', cookies={'session': 'session_id'}).json() == {'key': 'value'}
    assert client.get('/admin/settings', cookies={'session': 'session_id'}).json() == {'key': 'value'}
