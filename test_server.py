import asyncio

from miniRPC import Server


def say_hello(name: str):
    return f'Hello, {name}!'


def add(a: int, b: int):
    return a + b


def divide(a: int, b: int):
    return a / b


if __name__ == '__main__':
    server = Server('localhost', 43211)
    server.register(say_hello)
    server.register(add)
    server.register(divide)
    asyncio.run(server.run())
