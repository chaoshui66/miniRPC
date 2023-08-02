import unittest

from miniRPC import Client
from test.test_server.server import TestServer

test_host = 'localhost'
test_port = 43211


class TestRpc(unittest.IsolatedAsyncioTestCase):

    async def test_rpc(self):

        test_server = TestServer(test_host, test_port)
        test_server.start()

        async with Client(test_host, test_port) as client:
            self.assertEqual(await client.call('say_hello', 'World'), 'Hello World')
            self.assertEqual(await client.call('add', 1, 2), 3)
            self.assertEqual(await client.call('divide', 1, 2), 0.5)

        test_server.stop()
