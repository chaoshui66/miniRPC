import asyncio
from asyncio import StreamReader, StreamWriter, start_server, iscoroutinefunction
from typing import Callable, Union

from miniRPC.data import _Exception, _Return
from miniRPC.packet import PacketReader, PacketWriter
from miniRPC.serializer import PickleSerializer, Serializer


class _TaskRing:

    def __init__(self, task: Union[asyncio.Task, None]):
        self._task = task
        self._next = None

    @classmethod
    def init_task_ring(cls, num: int = 8):
        head = cls(None)
        node = head
        for _ in range(num - 1):
            node._next = cls(None)
            node = node._next
        node._next = head
        return head

    def empty(self) -> bool:
        if self._task is None:
            return True
        if self._task.done():
            self._task = None
            return True
        return False

    def set_task(self, task: asyncio.Task):
        if self.empty():
            self._task = task
        else:
            raise RuntimeError("Task is not empty")

    def get_next(self) -> "_TaskRing":
        return self._next

    async def wait(self):
        if self.empty():
            return
        await self._task

    async def wait_all(self):
        node = self._next
        while node != self:
            await node.wait()
            node = node.get_next()


class Server:

    def __init__(
        self, 
        host: str,
        port: int = 4321,
        serializer: Serializer = PickleSerializer()
    ):
        self._host = host
        self._port = port
        self._func_map = {}
        self._serializer = serializer
    
    def register(self, func: Callable, name: str = None):
        if name is None:
            name = func.__name__
        self._func_map[name] = func

    async def serve(self, reader: StreamReader, writer: StreamWriter):        
        packet_reader = PacketReader(reader)
        packet_writer = PacketWriter(writer)
        task_ring = _TaskRing.init_task_ring()

        while True:
            packet = await packet_reader.read_packet()
            if not packet:
                break

            async def handle_func(packet_: bytes):

                try:
                    call_ = self._serializer.decode(packet_)
                except Exception as e:
                    await self._write_result(packet_writer, _Exception(e))
                    return

                func = self._func_map.get(call_.method)
                if not func:
                    await self._write_result(packet_writer, _Exception(AttributeError(f'No such method: {call_.method}')))  # noqa
                    return

                try:
                    if iscoroutinefunction(func):
                        result = await func(*call_.args, **call_.kwargs)
                    else:
                        result = func(*call_.args, **call_.kwargs)
                except Exception as e:
                    await self._write_result(packet_writer, _Exception(e))
                else:
                    await self._write_result(packet_writer, _Return(result))

            if not task_ring.empty():
                await task_ring.wait()

            task = asyncio.create_task(handle_func(packet))
            task_ring.set_task(task)
            task_ring = task_ring.get_next()

    async def _write_result(self, packet_writer: PacketWriter, return_: Union[_Return, _Exception]):
        packet = self._serializer.encode(return_)
        await packet_writer.write(packet)
    
    async def run(self):
        server = await start_server(self.serve, self._host, self._port)
        await server.serve_forever()
