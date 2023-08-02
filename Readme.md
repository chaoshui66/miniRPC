# miniRPC

A simple RPC Lib based on asyncio

## Basic usage
server 
```python
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

```

client
```python
import asyncio

from miniRPC import Client


async def main():
    async with Client('localhost', 43211) as client:
        for i in range(100):
            print(await client.call('add', i, i))
            print(await client.call('say_hello', 'world'))
            print(await client.call('divide', 0, 0))


if __name__ == '__main__':
    asyncio.run(main())

```
