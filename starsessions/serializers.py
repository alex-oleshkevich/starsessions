import abc
import json
import typing


class Serializer(abc.ABC):  # pragma: no cover
    @abc.abstractmethod
    def serialize(self, data: typing.Any) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def deserialize(self, data: str) -> typing.Dict[str, typing.Any]:
        raise NotImplementedError()


class JsonSerializer(Serializer):
    def __init__(
        self,
        json_encoder: typing.Type[json.JSONEncoder] = json.JSONEncoder,
        json_decoder: typing.Type[json.JSONDecoder] = json.JSONDecoder,
    ) -> None:
        self._json_encoder = json_encoder
        self._json_decoder = json_decoder

    def serialize(self, data: typing.Any) -> str:
        return json.dumps(data, cls=self._json_encoder)

    def deserialize(self, data: str) -> typing.Dict[str, typing.Any]:
        return json.loads(data, cls=self._json_decoder)  # type: ignore[no-any-return]
