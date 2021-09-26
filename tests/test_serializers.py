from starsessions.serializers import JsonSerializer


def test_json_serializer() -> None:
    serializer = JsonSerializer()
    expected = {"key": "value"}
    serialized = serializer.serialize(expected)
    assert serializer.deserialize(serialized) == expected
