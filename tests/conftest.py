import pytest

from starsessions import InMemoryStore, JsonSerializer


@pytest.fixture
def serializer() -> JsonSerializer:
    return JsonSerializer()


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()
