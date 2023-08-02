import asyncio
from threading import Thread

from miniRPC import Server


def say_hello(name: str) -> str:
    return f"Hello {name}"


def add(x: int, y: int) -> int:
    return x + y


def divide(x: int, y: int) -> float:
    return x / y


class TestServer(Thread):

    def __init__(self, host: str, port: int):
        super().__init__()
        self._server = Server(host, port)
        self._server.register(say_hello)
        self._server.register(add)
        self._server.register(divide)
        self.task = None

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        self.task = loop.create_task(self._server.run())

        try:
            loop.run_until_complete(self.task)
        except asyncio.CancelledError:
            pass

    def stop(self):
        self.task.cancel()
        self.join()
