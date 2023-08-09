import asyncio
from typing import Any, Generator
from logging import Logger, getLogger

from miniRPC.data import _Call, _Exception
from miniRPC.packet import PacketReader, PacketWriter
from miniRPC.serializer import PickleSerializer, Serializer


class Client:

    def __init__(
        self,
        host: str,
        port: int = 4321,
        serializer: Serializer = PickleSerializer(),
        logger: Logger = getLogger(__name__)
    ):
        self._host = host
        self._port = port
        self._serializer = serializer
        self._reader = None
        self._writer = None
        self.packet_reader = None
        self.packet_writer = None
        self.logger = logger
        self._call_dict = {}
        self._cid_generator = self.cid_generator()
        self._read_loop_task = None
        self._write_lock = asyncio.Lock()

    @staticmethod
    def cid_generator() -> Generator[int, None, None]:
        cid = 0
        while True:
            cid += 1
            yield cid

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def connect(self):
        if self._reader and self._writer:
            return
        self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
        self.packet_reader = PacketReader(self._reader)
        self.packet_writer = PacketWriter(self._writer)
        await self._start_read_loop()

    async def close(self):
        if self._read_loop_task:
            self._read_loop_task.cancel()
        if self._reader and self._writer:
            self._writer.close()
            await self._writer.wait_closed()

    async def _start_read_loop(self):
        self._read_loop_task = asyncio.create_task(self.read_loop())

    def _stop_read_loop(self):
        self._read_loop_task.cancel()

    async def read_loop(self):

        while True:
            try:
                packet = await self.packet_reader.read_packet()
                result = self._serializer.decode(packet)

                future = self._call_dict.pop(result.cid)
                if not future:
                    continue

                if isinstance(result, _Exception):
                    future.set_exception(result.value())
                else:
                    future.set_result(result.value())
            except Exception as e:
                self.logger.exception("read_loop error: %s", e)
                break

    async def _call(self, func_name: str, *args, **kwargs) -> asyncio.Future:
        cid = next(self._cid_generator)

        _call = _Call(func_name, cid, *args, **kwargs)
        packet = self._serializer.encode(_call)

        await self._write_lock.acquire()
        await self.packet_writer.write(packet)
        self._write_lock.release()

        self.logger.debug(f'{_call} sent')

        future = asyncio.Future()
        self._call_dict[cid] = future
        return future

    async def call(self, func_name: str, *args, **kwargs) -> Any:
        future = await self._call(func_name, *args, **kwargs)
        await future
        return future.result()
