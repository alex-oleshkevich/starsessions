import time
from unittest import mock

import pytest
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.types import Receive, Scope, Send

from starsessions import SessionMiddleware, SessionStore, load_session


@pytest.mark.asyncio
async def test_expiring_session_must_not_extend_duration(store: SessionStore) -> None:
    session_lifetime = 10
    await store.write("session_id", b'{"id": 42}', lifetime=60, ttl=session_lifetime)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        response = JSONResponse(connection.session)
        await response(scope, receive, send)

    app = SessionMiddleware(app, store=store, lifetime=10, rolling=False)
    client = TestClient(app, cookies={"session": "session_id"})

    current_time = time.time()

    # it must set max-age = 10
    with mock.patch("time.time", lambda: current_time):
        response = client.get("/")
        first_max_age = next(cookie for cookie in response.cookies.jar if cookie.name == "session").expires

    # it must set the same max-age as the first response
    with mock.patch("time.time", lambda: current_time + 2):
        response = client.get("/")
        second_max_age = next(cookie for cookie in response.cookies.jar if cookie.name == "session").expires

    # the expiry date must be the same for both responses
    assert second_max_age == first_max_age
