import pytest

from starsessions import InMemoryBackend, JsonSerializer


@pytest.fixture()
def serializer() -> JsonSerializer:
    return JsonSerializer()


@pytest.fixture()
def backend() -> InMemoryBackend:
    return InMemoryBackend()
