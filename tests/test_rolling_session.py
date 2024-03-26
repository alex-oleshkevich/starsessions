import pytest
import time
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.types import Receive, Scope, Send
from unittest import mock

from starsessions import SessionMiddleware, SessionStore, load_session
from starsessions.session import get_session_remaining_seconds


@pytest.mark.asyncio
async def test_rolling_session_must_extend_duration(store: SessionStore) -> None:
    session_lifetime = 10
    await store.write("session_id", b'{"id": 42}', lifetime=session_lifetime, ttl=session_lifetime)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        connection = HTTPConnection(scope, receive)
        await load_session(connection)
        response = JSONResponse(connection.session)
        await response(scope, receive, send)
        # the session has been rolled again to last for another 10 seconds
        assert get_session_remaining_seconds(connection) == session_lifetime

    app = SessionMiddleware(app, store=store, lifetime=10, rolling=True)
    client = TestClient(app)

    current_time = time.time()

    with mock.patch("time.time", lambda: current_time):
        response = client.get("/", cookies={"session": "session_id"})
        first_expiration_date = next(cookie for cookie in response.cookies if cookie.name == "session").expires

    # fast forward 2 seconds
    with mock.patch("time.time", lambda: current_time + 2):
        response = client.get("/", cookies={"session": "session_id"})
        second_expiration_date = next(cookie for cookie in response.cookies if cookie.name == "session").expires

    # the expiration date of the cooke in the second response must be extended by 2 seconds
    assert second_expiration_date - first_expiration_date == 2
