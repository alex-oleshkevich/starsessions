import os
import pytest
import typing
from _pytest.fixtures import SubRequest
from typing import Dict, Tuple

from starsessions import CookieBackend, InMemoryBackend, Session, SessionBackend
from starsessions.backends.redis import RedisBackend


@pytest.fixture()  # type: ignore[misc]
def session_payload() -> typing.Dict[str, typing.Any]:
    return {"key": "value"}


def redis_key_callable(session_id: str) -> str:
    return f"this:is:a:redis:key:{session_id}"


def redis_key_callable_wrong_arg_name(wrong_arg: str) -> str:
    return f"this:is:a:redis:key:{wrong_arg}"


@pytest.fixture()  # type: ignore[misc]
def in_memory() -> SessionBackend:
    return InMemoryBackend()


@pytest.fixture()  # type: ignore[misc]
def in_memory_session(in_memory: SessionBackend) -> Session:
    session = Session(in_memory)
    session.is_loaded = True
    return session


@pytest.fixture()  # type: ignore[misc]
def cookie() -> SessionBackend:
    return CookieBackend("key", 14)


@pytest.fixture(params=[None, redis_key_callable], ids=["default", "using redis_key_callable"])  # type: ignore[misc]
def redis_session_payload(request: SubRequest) -> Tuple[SessionBackend, Dict[str, str]]:
    redis_key = request.param
    url = os.environ.get("REDIS_URL", "redis://localhost")
    return RedisBackend(url, redis_key_func=redis_key), {"key": "value"} if redis_key is None else {
        redis_key_callable("key"): "value"
    }


@pytest.fixture()  # type: ignore[misc]
def redis_session(redis_session_payload: typing.Tuple[SessionBackend, typing.Dict[str, typing.Any]]) -> Session:
    redis, _ = redis_session_payload
    session = Session(redis)
    session.is_loaded = True
    return session
