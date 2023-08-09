import pickle
import unittest

from miniRPC.packet import PacketReader, PacketWriter


class SomeUser:
    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender

    def __eq__(self, other):
        return self.name == other.name and self.age == other.age and self.gender == other.gender


class TestPacket(unittest.TestCase):

    def setUp(self) -> None:
        self.packet_writer = PacketWriter(None)
        self.packet_reader = PacketReader(None)

        self.bytes_list = [
            b'hello world',
            b'I have some bytes'
        ]

        self.object_list = [
            SomeUser('Darcy', 24, 'male'),
            SomeUser('Nevermore', -1, 'unknown')
        ]

    def test_bytes(self):
        for bytes_data in self.bytes_list:
            packet = self.packet_writer.generate_length_bytes(len(bytes_data)) + bytes_data

            for i in range(5):
                self.packet_reader.read_buffer += packet
                self.assertEqual(self.packet_reader._try_read_packet(), bytes_data)

    def test_object(self):
        for obj in self.object_list:
            obj_bytes = pickle.dumps(obj)
            packet = self.packet_writer.generate_length_bytes(len(obj_bytes)) + obj_bytes

            for i in range(5):
                self.packet_reader.read_buffer += packet
                read_packet = self.packet_reader._try_read_packet()
                read_obj = pickle.loads(read_packet)
                self.assertEqual(read_obj, obj)
