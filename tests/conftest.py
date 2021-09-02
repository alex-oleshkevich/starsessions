import pytest

from starsessions import CookieBackend, InMemoryBackend, Session


@pytest.fixture()
def in_memory():
    return InMemoryBackend()


@pytest.fixture()
def cookie():
    return CookieBackend("key", 14)


@pytest.fixture()
def in_memory_session(in_memory):
    session = Session(in_memory)
    session.is_loaded = True
    return session


@pytest.fixture()
def session_payload():
    return {"key": "value"}
