# miniRPC

A simple RPC lib based on asyncio

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
        
        # Concurrency Call
        # Actually, if there are multiple requests, the client will not wait for the result of 
        # the previous request, it will send subsequent requests before the response arrives. 
        # The client has a background loop that reads the server's response and sets the 
        # Future object with the result.
        tasks = list()
        tasks.append(client.call('add', i, i))
        tasks.append(client.call('say_hello', 'world'))
        tasks.append(client.call('divide', 0, 0))
        
        results = await asyncio.gather(*tasks)
        print(results)
        

if __name__ == '__main__':
    asyncio.run(main())

```
