import os
import pytest

from starsessions import CookieBackend, InMemoryBackend, Session, SessionBackend
from starsessions.backends.redis import RedisBackend


@pytest.fixture()
def session_payload() -> dict:
    return {"key": "value"}


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


@pytest.fixture()
def redis() -> SessionBackend:
    url = os.environ.get("REDIS_URL", "redis://localhost")
    return RedisBackend(url)


@pytest.fixture()
def redis_session(redis: SessionBackend) -> Session:
    session = Session(redis)
    session.is_loaded = True
    return session
