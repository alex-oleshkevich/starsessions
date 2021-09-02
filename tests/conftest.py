import os

import pytest

from starsessions import CookieBackend, InMemoryBackend, Session
from starsessions.backends.redis import RedisBackend


@pytest.fixture()
def session_payload():
    return {"key": "value"}


@pytest.fixture()
def in_memory():
    return InMemoryBackend()


@pytest.fixture()
def in_memory_session(in_memory):
    session = Session(in_memory)
    session.is_loaded = True
    return session


@pytest.fixture()
def cookie():
    return CookieBackend("key", 14)


@pytest.fixture()
def redis():
    url = os.environ.get("REDIS_URL", "redis://localhost")
    return RedisBackend(url)


@pytest.fixture()
def redis_session(redis):
    session = Session(redis)
    session.is_loaded = True
    return session
