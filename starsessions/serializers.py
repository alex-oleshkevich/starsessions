import abc
import json
import typing as t


class Serializer(abc.ABC):  # pragma: no cover
    @abc.abstractmethod
    def serialize(self, data: t.Any) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    def deserialize(self, data: str) -> t.Dict:
        raise NotImplementedError()


class JsonSerializer(Serializer):
    def __init__(
        self,
        json_encoder: t.Type[json.JSONEncoder] = json.JSONEncoder,
        json_decoder: t.Type[json.JSONDecoder] = json.JSONDecoder,
    ) -> None:
        self._json_encoder = json_encoder
        self._json_decoder = json_decoder

    def serialize(self, data: t.Any) -> str:
        return json.dumps(data, cls=self._json_encoder)

    def deserialize(self, data: str) -> t.Dict:
        return json.loads(data, cls=self._json_decoder)
