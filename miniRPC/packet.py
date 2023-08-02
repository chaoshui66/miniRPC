from asyncio import StreamReader, StreamWriter
from typing import Union

"""
TCP 分包
使用若干个字节作为长度标识
字节的最高位作为是否结束的标识
1 代表结束
0 代表未结束
"""


class PacketWriter:

    def __init__(self, writer: StreamWriter) -> None:
        self.writer = writer

    async def write(self, data: bytes):
        length_bytes = self.generate_length_bytes(len(data))
        res_data = length_bytes + data
        self.writer.write(res_data)
        await self.writer.drain()

    @staticmethod
    def generate_length_bytes(length: int) -> bytes:
        length_bytes = []
        while True:
            length_bytes.insert(0, length & 0x7f)
            length >>= 7
            if length == 0:
                break
        length_bytes[-1] |= 0x80
        return bytes(length_bytes)


class PacketReader:

    def __init__(self, reader: StreamReader) -> None:
        self.reader = reader
        self.read_buffer = bytes()

    async def read_packet(self) -> Union[bytes, None]:

        while True:
            data = await self.reader.read(1024)
            if not data:
                return

            self.read_buffer += data
            packet = self._try_read_packet()
            if packet:
                return packet

    def _try_read_packet(self):
        length = 0
        byte_num = 0

        for i in self.read_buffer:
            length <<= 7
            length |= i & 0x7f
            byte_num += 1
            if i & 0x80 != 0:
                break

        if len(self.read_buffer) >= length:
            packet = self.read_buffer[:length + byte_num]
            self.read_buffer = self.read_buffer[length + byte_num:]
            packet = packet[byte_num:]
            return packet
        return None
