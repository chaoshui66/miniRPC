from typing import Any


class _Trace:

    def __init__(self, cid: int):
        self.cid = cid


class _Call(_Trace):

    def __init__(self, method: str, cid: int, *args, **kwargs) -> None:
        super().__init__(cid)
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return f'Call {self.method}, cid: {self.cid}'


class _Return(_Trace):

    def __init__(self, value: Any, cid: int) -> None:
        super().__init__(cid)
        self._value = value

    def value(self):
        return self._value


class _Exception(_Trace):

    def __init__(self, value: Exception, cid: int) -> None:
        super().__init__(cid)
        self._value = value

    def __repr__(self):
        return repr(object)

    def value(self):
        raise self._value
