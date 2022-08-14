import os
import pytest
import typing
from _pytest.fixtures import SubRequest

from starsessions import CookieBackend, InMemoryBackend, JsonSerializer, Session, SessionBackend
from starsessions.backends.redis import RedisBackend


@pytest.fixture()
def session_payload() -> typing.Dict[str, typing.Any]:
    return {"key": "value"}


def redis_key_callable(session_id: str) -> str:
    return f"this:is:a:redis:key:{session_id}"


def redis_key_callable_wrong_arg_name(wrong_arg: str) -> str:
    return f"this:is:a:redis:key:{wrong_arg}"


@pytest.fixture()
def in_memory() -> SessionBackend:
    backend = InMemoryBackend()
    setattr(backend, 'serializer', JsonSerializer())  # FIXME: remove after #27
    return backend


@pytest.fixture()
def in_memory_session(in_memory: SessionBackend) -> Session:
    session = Session(in_memory)
    session.is_loaded = True
    return session


@pytest.fixture()
def cookie() -> SessionBackend:
    return CookieBackend("key", 14)


@pytest.fixture(params=[None, redis_key_callable], ids=["default", "using redis_key_callable"])
def redis_backend(request: SubRequest) -> SessionBackend:
    redis_key = request.param
    url = os.environ.get("REDIS_URL", "redis://localhost")
    return RedisBackend(url, redis_key_func=redis_key)


@pytest.fixture()
def redis_session(redis_backend: SessionBackend) -> Session:
    session = Session(redis_backend)
    session.is_loaded = True
    return session
