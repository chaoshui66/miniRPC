import pickle
from abc import ABCMeta, abstractmethod
from typing import Any


class Serializer(metaclass=ABCMeta):

    @abstractmethod
    def encode(self, data: Any) -> bytes:
        pass

    @abstractmethod
    def decode(self, data: bytes) -> Any:
        pass


class PickleSerializer(Serializer):

    def encode(self, data: Any) -> bytes:
        return pickle.dumps(data)

    def decode(self, data: bytes) -> Any:
        return pickle.loads(data)
