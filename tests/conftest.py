import pytest

from starsessions import InMemoryStore, JsonSerializer
from starsessions.encryptors import Encryptor, NoopEncryptor


@pytest.fixture
def serializer() -> JsonSerializer:
    return JsonSerializer()


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def encryptor() -> Encryptor:
    return NoopEncryptor()
