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
