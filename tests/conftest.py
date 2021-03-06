import os
import pytest
from _pytest.fixtures import SubRequest
from typing import Dict, Tuple

from starsessions import CookieBackend, InMemoryBackend, Session, SessionBackend
from starsessions.backends.redis import RedisBackend


@pytest.fixture()
def session_payload() -> dict:
    return {"key": "value"}


def redis_key_callable(session_id: str) -> str:
    return f"this:is:a:redis:key:{session_id}"


def redis_key_callable_wrong_arg_name(wrong_arg: str) -> str:
    return f"this:is:a:redis:key:{wrong_arg}"


@pytest.fixture()
def in_memory() -> SessionBackend:
    return InMemoryBackend()


@pytest.fixture()
def in_memory_session(in_memory: SessionBackend) -> Session:
    session = Session(in_memory)
    session.is_loaded = True
    return session


@pytest.fixture()
def cookie() -> SessionBackend:
    return CookieBackend("key", 14)


@pytest.fixture(params=[None, redis_key_callable], ids=["default", "using redis_key_callable"])
def redis_session_payload(request: SubRequest) -> Tuple[SessionBackend, Dict[str, str]]:
    redis_key = request.param
    url = os.environ.get("REDIS_URL", "redis://localhost")
    return RedisBackend(url, redis_key_func=redis_key), {"key": "value"} if redis_key is None else {
        redis_key_callable("key"): "value"
    }


@pytest.fixture()
def redis_session(redis_session_payload: Tuple[SessionBackend, Dict[str, str]]) -> Session:
    redis, _ = redis_session_payload
    session = Session(redis)
    session.is_loaded = True
    return session
