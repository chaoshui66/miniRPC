import asyncio
from typing import Any

from miniRPC.data import _Call, _Exception
from miniRPC.packet import PacketReader, PacketWriter
from miniRPC.serializer import PickleSerializer, Serializer


class Client:

    def __init__(
        self, 
        host: str,
        port: int = 4321,
        serializer: Serializer = PickleSerializer()
    ):
        self._host = host
        self._port = port
        self._serializer = serializer
        self._reader = None
        self._writer = None
        self.packet_reader = None
        self.packet_writer = None
        self._lock = asyncio.Lock()

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

    async def close(self):
        if self._reader and self._writer:
            self._writer.close()
            await self._writer.wait_closed()

    async def call(self, func: str, *args, **kwargs) -> Any:
        _call = _Call(func, *args, **kwargs)
        packet = self._serializer.encode(_call)

        await self._lock.acquire()

        try:
            await self.packet_writer.write(packet)
            result_packet = await self.packet_reader.read_packet()
        except Exception as e:
            raise e
        finally:
            self._lock.release()

        result = self._serializer.decode(result_packet)

        if isinstance(result, _Exception):
            raise result.value()
        
        return result.value()
