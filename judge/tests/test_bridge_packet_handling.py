"""Tests for judge/bridge/ packet handling and network protocol functionality.

This module tests packet compression, network protocols, and binary data handling
in the bridge modules to ensure Python 2/3 migration compatibility.
"""

import json
import unittest
import zlib
from io import BytesIO
from unittest.mock import MagicMock

from netaddr import IPSet

from judge.bridge.base_handler import (
    MAX_ALLOWED_PACKET_SIZE,
    Disconnect,
    ZlibPacketHandler,
    proxy_list,
    size_pack,
)


class MockSocket:
    """Mock socket for testing packet handling."""

    def __init__(self, data=b''):
        self.data = BytesIO(data)
        self.timeout = None
        self.sent_data = BytesIO()

    def recv(self, size):
        return self.data.read(size)

    def sendall(self, data):
        self.sent_data.write(data)

    def gettimeout(self):
        return self.timeout

    def settimeout(self, timeout):
        self.timeout = timeout

    def shutdown(self, how):
        pass


class ProxyListTest(unittest.TestCase):
    """Test proxy list functionality."""

    def test_proxy_list_basic(self):
        """Test basic proxy list creation."""
        human_readable = ['192.168.1.1', '10.0.0.0/8']
        result = proxy_list(human_readable)

        self.assertIsInstance(result, IPSet)

    def test_proxy_list_with_globs(self):
        """Test proxy list with IP globs."""
        human_readable = ['192.168.1.*', '10.0.0.*']
        result = proxy_list(human_readable)

        self.assertIsInstance(result, IPSet)

    def test_proxy_list_empty(self):
        """Test proxy list with empty input."""
        result = proxy_list([])
        self.assertIsInstance(result, IPSet)
        self.assertEqual(len(result), 0)

    def test_proxy_list_mixed_formats(self):
        """Test proxy list with mixed IP formats."""
        human_readable = [
            '192.168.1.1',  # Single IP
            '10.0.0.*',     # Glob pattern
            '172.16.0.0/24',  # CIDR
            '127.0.0.0/8',  # CIDR
        ]
        result = proxy_list(human_readable)
        self.assertIsInstance(result, IPSet)


class ZlibPacketHandlerTest(unittest.TestCase):
    """Test ZlibPacketHandler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = MagicMock()
        self.server.server_address = ('localhost', 8080)

    def create_handler(self, socket_data=b''):
        """Create a test handler with mock socket."""
        mock_socket = MockSocket(socket_data)

        # Create handler without triggering metaclass by calling __new__ directly
        handler = ZlibPacketHandler.__new__(ZlibPacketHandler)
        handler.request = mock_socket
        handler.server = self.server
        handler.client_address = ('127.0.0.1', 12345)
        handler.server_address = self.server.server_address
        handler._initial_tag = None
        handler._got_packet = False

        return handler, mock_socket

    def test_handler_initialization(self):
        """Test handler initialization."""
        handler, _ = self.create_handler()

        self.assertEqual(handler.client_address, ('127.0.0.1', 12345))
        self.assertEqual(handler.server_address, ('localhost', 8080))
        self.assertIsNone(handler._initial_tag)
        self.assertFalse(handler._got_packet)

    def test_timeout_property(self):
        """Test timeout property getter and setter."""
        handler, mock_socket = self.create_handler()

        # Test getter
        self.assertEqual(handler.timeout, mock_socket.timeout)

        # Test setter
        handler.timeout = 30
        self.assertEqual(mock_socket.timeout, 30)

        # Test setting None
        handler.timeout = None
        self.assertIsNone(mock_socket.timeout)

    def test_read_size_basic(self):
        """Test reading packet size."""
        # Create a 4-byte size header
        size_data = size_pack.pack(1024)
        handler, _ = self.create_handler(size_data)

        size = handler.read_size()
        self.assertEqual(size, 1024)

    def test_read_size_with_buffer(self):
        """Test reading packet size with partial buffer."""
        # Create a 4-byte size header
        size_data = size_pack.pack(2048)
        handler, _ = self.create_handler(size_data[2:])  # Missing first 2 bytes

        # Should raise Disconnect due to incomplete data
        with self.assertRaises(Disconnect):
            handler.read_size(size_data[:2])

    def test_size_pack_format(self):
        """Test size pack struct format."""
        self.assertEqual(size_pack.size, 4)

        # Test packing and unpacking
        test_size = 12345
        packed = size_pack.pack(test_size)
        unpacked = size_pack.unpack(packed)[0]
        self.assertEqual(test_size, unpacked)

    def test_max_packet_size_limit(self):
        """Test maximum packet size enforcement."""
        handler, _ = self.create_handler()

        # Test with size exceeding limit
        with self.assertRaises(Disconnect):
            handler.read_sized_packet(MAX_ALLOWED_PACKET_SIZE + 1)

    def test_packet_compression_decompression(self):
        """Test packet compression and decompression."""
        test_data = "Hello, 世界! This is a test message with Unicode."

        # Test compression
        compressed = zlib.compress(test_data.encode('utf-8'))

        # Test decompression
        decompressed = zlib.decompress(compressed).decode('utf-8')
        self.assertEqual(test_data, decompressed)

    def test_unicode_in_packets(self):
        """Test Unicode handling in packet data."""
        test_cases = [
            "ASCII only",
            "Unicode: 你好世界",
            "Emoji: 🚀🌟💻",
            "Mixed: Hello 世界 🎉",
            "Special chars: \u0000\u001f\u007f",
        ]

        for test_data in test_cases:
            with self.subTest(test_data=test_data):
                # Encode and compress
                encoded = test_data.encode('utf-8')
                compressed = zlib.compress(encoded)

                # Decompress and decode
                decompressed = zlib.decompress(compressed)
                result = decompressed.decode('utf-8')

                self.assertEqual(test_data, result)

    def test_large_packet_handling(self):
        """Test handling of large packets within limits."""
        # Create a large but acceptable packet
        large_data = "x" * (MAX_ALLOWED_PACKET_SIZE // 2)
        compressed = zlib.compress(large_data.encode('utf-8'))

        # Should not raise an exception
        self.assertLess(len(compressed), MAX_ALLOWED_PACKET_SIZE)

    def test_empty_packet_handling(self):
        """Test handling of empty packets."""
        empty_data = ""
        compressed = zlib.compress(empty_data.encode('utf-8'))
        decompressed = zlib.decompress(compressed).decode('utf-8')

        self.assertEqual(empty_data, decompressed)

    def test_binary_data_in_packets(self):
        """Test handling of binary data in packets."""
        # Create test data with various byte values
        binary_data = bytes(range(256))

        # JSON doesn't handle raw binary, so we'd typically base64 encode it
        import base64
        encoded_data = base64.b64encode(binary_data).decode('ascii')

        # Compress the encoded data
        compressed = zlib.compress(encoded_data.encode('utf-8'))

        # Decompress and decode
        decompressed = zlib.decompress(compressed).decode('utf-8')
        decoded_binary = base64.b64decode(decompressed.encode('ascii'))

        self.assertEqual(binary_data, decoded_binary)

    def test_json_data_packets(self):
        """Test JSON data in packets."""
        test_json = {
            'type': 'test',
            'data': 'Hello 世界',
            'number': 42,
            'unicode_field': '🚀 Test',
            'nested': {
                'inner': 'value',
                'list': [1, 2, '三']
            }
        }

        # Serialize to JSON
        json_str = json.dumps(test_json, ensure_ascii=False)

        # Compress
        compressed = zlib.compress(json_str.encode('utf-8'))

        # Decompress and parse
        decompressed = zlib.decompress(compressed).decode('utf-8')
        parsed = json.loads(decompressed)

        self.assertEqual(test_json, parsed)

    def test_malformed_packet_handling(self):
        """Test handling of malformed packets."""
        # Test invalid zlib data
        invalid_data = b"This is not compressed data"

        with self.assertRaises(zlib.error):
            zlib.decompress(invalid_data)

    def test_proxy_protocol_parsing(self):
        """Test proxy protocol parsing."""
        handler, _ = self.create_handler()

        # Test TCP4 proxy protocol line
        tcp4_line = b"PROXY TCP4 192.168.1.1 192.168.1.2 1234 80"
        handler.parse_proxy_protocol(tcp4_line)

        self.assertEqual(handler.client_address, ('192.168.1.1', '1234'))
        self.assertEqual(handler.server_address, ('192.168.1.2', '80'))

    def test_proxy_protocol_tcp6(self):
        """Test TCP6 proxy protocol parsing."""
        handler, _ = self.create_handler()

        # Test TCP6 proxy protocol line
        tcp6_line = b"PROXY TCP6 2001:db8::1 2001:db8::2 1234 80"
        handler.parse_proxy_protocol(tcp6_line)

        self.assertEqual(handler.client_address, ('2001:db8::1', '1234', 0, 0))
        self.assertEqual(handler.server_address, ('2001:db8::2', '80', 0, 0))

    def test_proxy_protocol_unknown(self):
        """Test UNKNOWN proxy protocol."""
        handler, _ = self.create_handler()

        # Test UNKNOWN proxy protocol line
        unknown_line = b"PROXY UNKNOWN"
        handler.parse_proxy_protocol(unknown_line)

        # Should not change addresses for UNKNOWN
        self.assertEqual(handler.client_address, ('127.0.0.1', 12345))

    def test_proxy_protocol_malformed(self):
        """Test malformed proxy protocol lines."""
        handler, _ = self.create_handler()

        # Test insufficient words
        with self.assertRaises(Disconnect):
            handler.parse_proxy_protocol(b"PROXY")

        # Test invalid TCP4 format
        with self.assertRaises(Disconnect):
            handler.parse_proxy_protocol(b"PROXY TCP4 insufficient args")

        # Test invalid protocol
        with self.assertRaises(Disconnect):
            handler.parse_proxy_protocol(b"PROXY INVALID protocol")

    def test_packet_send_functionality(self):
        """Test sending packets with compression."""
        handler, mock_socket = self.create_handler()

        test_data = "Test message with Unicode: 测试消息"
        handler.send(test_data)

        # Check that data was sent
        sent_data = mock_socket.sent_data.getvalue()
        self.assertGreater(len(sent_data), 4)  # At least size header + compressed data

        # Extract size and compressed data
        size = size_pack.unpack(sent_data[:4])[0]
        compressed_data = sent_data[4:4+size]

        # Decompress and verify
        decompressed = zlib.decompress(compressed_data).decode('utf-8')
        self.assertEqual(test_data, decompressed)

    def test_compression_efficiency(self):
        """Test compression efficiency with repetitive data."""
        # Repetitive data should compress well
        repetitive_data = "Hello world! " * 1000
        compressed = zlib.compress(repetitive_data.encode('utf-8'))

        compression_ratio = len(compressed) / len(repetitive_data.encode('utf-8'))
        self.assertLess(compression_ratio, 0.1)  # Should compress to less than 10%

    def test_utf8_text_integration(self):
        """Test integration with utf8text utility function."""
        from judge.utils.unicode import utf8text

        # Test proxy protocol parsing uses utf8text
        handler, _ = self.create_handler()

        # Simulate proxy protocol with bytes
        tcp4_line = b"PROXY TCP4 192.168.1.1 192.168.1.2 1234 80"
        words = tcp4_line.split()

        # Test that utf8text handles bytes correctly
        client_ip = utf8text(words[2])
        client_port = utf8text(words[4])

        self.assertEqual(client_ip, '192.168.1.1')
        self.assertEqual(client_port, '1234')
        self.assertIsInstance(client_ip, str)
        self.assertIsInstance(client_port, str)

    def test_error_handling_edge_cases(self):
        """Test error handling in various edge cases."""
        # Test with no data
        handler, _ = self.create_handler(b'')

        with self.assertRaises(Disconnect):
            handler.read_size()

        # Test with partial size data
        handler2, _ = self.create_handler(b'\x00\x00')  # Only 2 bytes of 4-byte size

        with self.assertRaises(Disconnect):
            handler2.read_size()

    def test_metaclass_behavior(self):
        """Test RequestHandlerMeta metaclass behavior."""
        # This is more of an integration test - we'll test it differently
        # to avoid the blocking behavior during handler creation

        # Test that the metaclass exists and has the expected call behavior
        from judge.bridge.base_handler import RequestHandlerMeta

        # Create a simple test handler class that doesn't block
        class TestHandler(metaclass=RequestHandlerMeta):
            def __init__(self, *args, **kwargs):
                self.connected = False
                self.handled = False
                self.disconnected = False
                # Don't call super().__init__ to avoid triggering the socket handler

            def on_connect(self):
                self.connected = True

            def handle(self):
                self.handled = True
                # Don't actually handle anything that would block

            def on_disconnect(self):
                self.disconnected = True

        # Create instance - metaclass should call the lifecycle methods
        mock_socket = MockSocket()
        handler = TestHandler(mock_socket, ('127.0.0.1', 12345), self.server)

        # Verify the lifecycle methods were called by the metaclass
        self.assertTrue(handler.connected)
        self.assertTrue(handler.handled)
        self.assertTrue(handler.disconnected)
