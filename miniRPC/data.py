from typing import Any


class _Call:

    def __init__(self, method: str, *args, **kwargs) -> None:
        self.method = method
        self.args = args
        self.kwargs = kwargs


class _Return:

    def __init__(self, value: Any) -> None:
        self._value = value

    def value(self):
        return self._value


class _Exception:

    def __init__(self, value: Any):
        self.value = value

    def __repr__(self):
        return repr(object)
    
    def value(self):
        raise self.value
