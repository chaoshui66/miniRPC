from asyncio import StreamReader, StreamWriter, start_server
from typing import Callable, Union

from miniRPC.data import _Exception, _Return
from miniRPC.packet import PacketReader, PacketWriter
from miniRPC.serializer import PickleSerializer, Serializer


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

        while True:
            packet = await packet_reader.read_packet()
            if not packet:
                break
            try:
                call_ = self._serializer.decode(packet)
            except Exception as e:
                await self._write_result(packet_writer, _Exception(e))
                continue

            func = self._func_map.get(call_.method)
            if not func:
                await self._write_result(packet_writer, _Exception(AttributeError(f'No such method: {call_.method}')))
                continue

            try:
                result = func(*call_.args, **call_.kwargs)
            except Exception as e:
                await self._write_result(packet_writer, _Exception(e))
            else:
                await self._write_result(packet_writer, _Return(result))

    async def _write_result(self, packet_writer: PacketWriter, return_: Union[_Return, _Exception]):
        packet = self._serializer.encode(return_)
        await packet_writer.write(packet)
    
    async def run(self):
        server = await start_server(self.serve, self._host, self._port)
        await server.serve_forever()
