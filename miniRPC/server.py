import asyncio
import logging
from logging import Logger, getLogger
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
        node.set_next(head)
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

    def set_next(self, node: "_TaskRing"):
        self._next = node

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
    """
    Server
    serve 方法是提供给 asyncio.start_server 的回调函数
    把接收到的数据反序列化为 _Call 对象，然后调用对应的函数，最后把结果序列化为 _Return 对象返回
    接收到请求以后，会创建一个 task 来处理请求，如果 task_ring 中有空闲的 task，就会把 task 放入 task_ring 中
    如果 task_ring 中没有空闲的 task，就会等待 task_ring 中的 task 完成
    这样就可以支持多个请求同时处理
    """

    def __init__(
        self,
        host: str,
        port: int = 4321,
        serializer: Serializer = PickleSerializer(),
        logger: Logger = getLogger(__name__)
    ):
        self._host = host
        self._port = port
        self._func_map = {}
        self._serializer = serializer
        self._write_lock = asyncio.Lock()
        self.logger = logger

    def register(self, func: Callable, name: str = None):
        if name is None:
            name = func.__name__
        self._func_map[name] = func

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        packet_reader = PacketReader(reader)
        packet_writer = PacketWriter(writer)
        task_ring = _TaskRing.init_task_ring()

        while True:
            packet = await packet_reader.read_packet()

            if not packet:
                break

            async def handle_func(packet_: bytes):
                cid = None
                try:
                    call_ = self._serializer.decode(packet_)
                    cid = call_.cid

                except Exception as e:
                    await self._write_result(packet_writer, _Exception(e, cid))
                    return

                func = self._func_map.get(call_.method)
                if not func:
                    await self._write_result(packet_writer, _Exception(AttributeError(f'No such method: {call_.method}'), cid))  # noqa
                    return

                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*call_.args, **call_.kwargs)
                    else:
                        result = func(*call_.args, **call_.kwargs)
                except Exception as e:
                    await self._write_result(packet_writer, _Exception(e, cid))
                else:
                    await self._write_result(packet_writer, _Return(result, cid))
                self.logger.info(f'{call_}, finished')

            task = asyncio.create_task(handle_func(packet))
            if not task_ring.empty():
                await task_ring.wait()

            task_ring.set_task(task)
            task_ring = task_ring.get_next()

    async def _write_result(self, packet_writer: PacketWriter, return_: Union[_Return, _Exception]):
        packet = self._serializer.encode(return_)
        await self._write_lock.acquire()
        await packet_writer.write(packet)
        self._write_lock.release()

    async def run(self):
        self.logger.info(f'Server start at {self._host}:{self._port}')
        server = await asyncio.start_server(self.serve, self._host, self._port)
        await server.serve_forever()
