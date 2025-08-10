"""
Tests for judge.utils.two_factor module.

This module tests base64 encoding/decoding and JSON serialization for WebAuthn,
covering Python 2/3 migration edge cases for binary data handling.
"""
import base64
import json
import unittest

from judge.utils.two_factor import WebAuthnJSONEncoder, webauthn_decode, webauthn_encode


class TwoFactorUtilsTest(unittest.TestCase):
    """Test WebAuthn encoding/decoding and JSON serialization."""

    def test_webauthn_encode_basic(self):
        """Test basic webauthn_encode functionality."""
        # Basic binary data
        test_data = b"hello world"
        result = webauthn_encode(test_data)

        # Should be URL-safe base64 without padding
        self.assertIsInstance(result, str)
        self.assertNotIn("=", result)  # No padding
        self.assertNotIn("+", result)  # URL-safe
        self.assertNotIn("/", result)  # URL-safe

        # Verify it's valid base64
        # Add padding back for verification
        padded = result + "=" * (-len(result) % 4)
        decoded = base64.urlsafe_b64decode(padded)
        self.assertEqual(decoded, test_data)

    def test_webauthn_encode_empty(self):
        """Test webauthn_encode with empty data."""
        result = webauthn_encode(b"")
        self.assertEqual(result, "")

    def test_webauthn_encode_various_binary_data(self):
        """Test webauthn_encode with various binary data patterns."""
        test_cases = [
            b"\x00",  # NULL byte
            b"\x00\x01\x02\x03",  # Sequential bytes
            b"\xff" * 10,  # All high bits
            b"\x00" * 10,  # All NULL bytes
            bytes(range(256)),  # All possible byte values
            b"A" * 100,  # Large ASCII data
            "🚀🌟".encode(),  # UTF-8 encoded Unicode
        ]

        for test_data in test_cases:
            with self.subTest(data_len=len(test_data)):
                result = webauthn_encode(test_data)
                self.assertIsInstance(result, str)

                # Verify roundtrip through standard base64
                padded = result + "=" * (-len(result) % 4)
                decoded = base64.urlsafe_b64decode(padded)
                self.assertEqual(decoded, test_data)

    def test_webauthn_decode_basic(self):
        """Test basic webauthn_decode functionality."""
        # Test with data that doesn't need padding
        original = b"hello"
        encoded = webauthn_encode(original)
        decoded = webauthn_decode(encoded)
        self.assertEqual(decoded, original)

    def test_webauthn_decode_with_padding_needed(self):
        """Test webauthn_decode when padding is needed."""
        # Create test cases that will need different amounts of padding
        test_cases = [
            b"a",  # 1 byte -> needs 3 padding chars
            b"ab",  # 2 bytes -> needs 2 padding chars
            b"abc",  # 3 bytes -> needs 1 padding char
            b"abcd",  # 4 bytes -> needs 0 padding chars
        ]

        for test_data in test_cases:
            with self.subTest(data=test_data):
                # Encode without padding
                encoded = base64.urlsafe_b64encode(test_data).decode("ascii").rstrip("=")

                # Decode should add padding automatically
                decoded = webauthn_decode(encoded)
                self.assertEqual(decoded, test_data)

    def test_webauthn_decode_empty(self):
        """Test webauthn_decode with empty string."""
        result = webauthn_decode("")
        self.assertEqual(result, b"")

    def test_webauthn_decode_malformed(self):
        """Test webauthn_decode with malformed input."""
        # Test case that should raise an error (incorrect padding)
        with self.subTest(input="abc!"), self.assertRaises(base64.binascii.Error):
            webauthn_decode("abc!")

        # Test cases that are technically invalid but get handled gracefully
        graceful_cases = [
            "!@#$",  # Invalid characters are ignored by base64
        ]

        for case in graceful_cases:
            with self.subTest(input=case):
                # These should not raise errors, but return some result
                result = webauthn_decode(case)
                self.assertIsInstance(result, bytes)

    def test_webauthn_roundtrip(self):
        """Test that webauthn_encode and webauthn_decode are inverse operations."""
        test_cases = [
            b"",
            b"hello",
            b"hello world",
            b"\x00\x01\x02\x03\x04",
            b"\xff" * 20,
            bytes(range(256)),
            "测试数据".encode(),
            "🚀🌟🎯".encode(),
        ]

        for test_data in test_cases:
            with self.subTest(data_len=len(test_data)):
                encoded = webauthn_encode(test_data)
                decoded = webauthn_decode(encoded)
                self.assertEqual(decoded, test_data)

    def test_webauthn_json_encoder_basic(self):
        """Test WebAuthnJSONEncoder with basic types."""
        encoder = WebAuthnJSONEncoder()

        # Non-bytes objects should use default encoding
        self.assertEqual(encoder.encode("hello"), '"hello"')
        self.assertEqual(encoder.encode(123), "123")
        self.assertEqual(encoder.encode([1, 2, 3]), "[1, 2, 3]")

    def test_webauthn_json_encoder_bytes(self):
        """Test WebAuthnJSONEncoder with bytes objects."""
        encoder = WebAuthnJSONEncoder()

        # Bytes should be encoded as {"_bytes": "base64_data"}
        test_bytes = b"hello world"
        result = encoder.encode(test_bytes)

        # Parse the JSON to verify structure
        parsed = json.loads(result)
        self.assertIsInstance(parsed, dict)
        self.assertIn("_bytes", parsed)
        self.assertIsInstance(parsed["_bytes"], str)

        # Verify the encoded data is correct
        encoded_data = parsed["_bytes"]
        decoded = webauthn_decode(encoded_data)
        self.assertEqual(decoded, test_bytes)

    def test_webauthn_json_encoder_complex_structure(self):
        """Test WebAuthnJSONEncoder with complex data structures containing bytes."""
        encoder = WebAuthnJSONEncoder()

        # Complex structure with nested bytes
        test_data = {
            "user_id": b"user123",
            "challenge": b"\x00\x01\x02\x03",
            "metadata": {
                "name": "test user",
                "key": b"secret_key",
                "number": 42
            },
            "list_with_bytes": [
                "string",
                b"bytes_data",
                123
            ]
        }

        result = encoder.encode(test_data)
        parsed = json.loads(result)

        # Verify structure is preserved
        self.assertEqual(parsed["metadata"]["name"], "test user")
        self.assertEqual(parsed["metadata"]["number"], 42)
        self.assertEqual(parsed["list_with_bytes"][0], "string")
        self.assertEqual(parsed["list_with_bytes"][2], 123)

        # Verify bytes are properly encoded
        self.assertIn("_bytes", parsed["user_id"])
        self.assertIn("_bytes", parsed["challenge"])
        self.assertIn("_bytes", parsed["metadata"]["key"])
        self.assertIn("_bytes", parsed["list_with_bytes"][1])

        # Verify bytes can be decoded back
        decoded_user_id = webauthn_decode(parsed["user_id"]["_bytes"])
        self.assertEqual(decoded_user_id, b"user123")

        decoded_challenge = webauthn_decode(parsed["challenge"]["_bytes"])
        self.assertEqual(decoded_challenge, b"\x00\x01\x02\x03")

    def test_webauthn_json_encoder_empty_bytes(self):
        """Test WebAuthnJSONEncoder with empty bytes."""
        encoder = WebAuthnJSONEncoder()

        result = encoder.encode(b"")
        parsed = json.loads(result)

        self.assertEqual(parsed, {"_bytes": ""})

    def test_webauthn_json_encoder_large_bytes(self):
        """Test WebAuthnJSONEncoder with large byte arrays."""
        encoder = WebAuthnJSONEncoder()

        # Large random-like data
        large_bytes = bytes(range(256)) * 10  # 2560 bytes
        result = encoder.encode(large_bytes)
        parsed = json.loads(result)

        # Verify structure
        self.assertIn("_bytes", parsed)

        # Verify data integrity
        decoded = webauthn_decode(parsed["_bytes"])
        self.assertEqual(decoded, large_bytes)

    def test_webauthn_json_encoder_unicode_in_bytes(self):
        """Test WebAuthnJSONEncoder with UTF-8 encoded bytes."""
        encoder = WebAuthnJSONEncoder()

        # Various Unicode strings encoded as bytes
        test_cases = [
            "Hello, 世界",
            "🚀🌟🎯💎",
            "Café résumé naïve",
            "Тест на русском",
            "عربي",
        ]

        for unicode_str in test_cases:
            with self.subTest(string=unicode_str):
                utf8_bytes = unicode_str.encode("utf-8")
                result = encoder.encode(utf8_bytes)
                parsed = json.loads(result)

                # Verify encoding
                self.assertIn("_bytes", parsed)

                # Verify roundtrip
                decoded = webauthn_decode(parsed["_bytes"])
                self.assertEqual(decoded, utf8_bytes)

                # Verify we can get back the original string
                recovered_str = decoded.decode("utf-8")
                self.assertEqual(recovered_str, unicode_str)

    def test_webauthn_json_encoder_edge_cases(self):
        """Test WebAuthnJSONEncoder with edge cases."""
        encoder = WebAuthnJSONEncoder()

        # Test with special byte sequences
        edge_cases = [
            b"\x00",  # NULL
            b"\xff",  # High bit
            b"\x00\xff\x00\xff",  # Alternating
            b"=" * 10,  # Base64 padding characters as data
            b"+" * 10,  # Base64 special characters as data
            b"/" * 10,  # Base64 special characters as data
        ]

        for test_bytes in edge_cases:
            with self.subTest(data=test_bytes.hex()):
                result = encoder.encode(test_bytes)
                parsed = json.loads(result)

                # Verify proper encoding
                self.assertIn("_bytes", parsed)

                # Verify data integrity
                decoded = webauthn_decode(parsed["_bytes"])
                self.assertEqual(decoded, test_bytes)

    def test_json_encoder_inheritance(self):
        """Test that WebAuthnJSONEncoder properly inherits from json.JSONEncoder."""
        encoder = WebAuthnJSONEncoder()

        # Should handle all standard JSON types normally
        test_cases = [
            None,
            True,
            False,
            42,
            3.14,
            "string",
            [],
            {},
            [1, "two", 3.0, None, True],
            {"key": "value", "number": 42, "nested": {"inner": "data"}},
        ]

        for test_data in test_cases:
            with self.subTest(data=type(test_data).__name__):
                # Our encoder should produce the same result as the default encoder
                our_result = encoder.encode(test_data)
                default_result = json.JSONEncoder().encode(test_data)

                # Parse both to compare (order might differ for dicts)
                our_parsed = json.loads(our_result)
                default_parsed = json.loads(default_result)
                self.assertEqual(our_parsed, default_parsed)

    def test_compatibility_with_standard_base64(self):
        """Test compatibility with standard base64 encoding/decoding."""
        test_data = b"test data for base64 compatibility"

        # Our encoding should be compatible with standard base64
        our_encoded = webauthn_encode(test_data)

        # Add padding and decode with standard library
        padded = our_encoded + "=" * (-len(our_encoded) % 4)
        standard_decoded = base64.urlsafe_b64decode(padded)

        self.assertEqual(standard_decoded, test_data)

        # Standard encoding should be compatible with our decoder
        # (after removing padding)
        standard_encoded = base64.urlsafe_b64encode(test_data).decode("ascii").rstrip("=")
        our_decoded = webauthn_decode(standard_encoded)

        self.assertEqual(our_decoded, test_data)


if __name__ == "__main__":
    unittest.main()
