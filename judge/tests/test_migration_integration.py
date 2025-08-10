"""Integration tests for Python 2/3 migration edge cases.

This module tests the interaction between different utility functions
to ensure they work correctly together after migration to Python 3.
"""

import json
import unittest

from judge.utils.camo import CamoClient
from judge.utils.two_factor import WebAuthnJSONEncoder, webauthn_decode, webauthn_encode
from judge.utils.unicode import utf8bytes, utf8text


class MigrationIntegrationTest(unittest.TestCase):
    """Test integration between various utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.camo_client = CamoClient("http://localhost:8080", "test-key", excluded=("localhost", "example.com"))

    def test_unicode_with_webauthn_encoding(self):
        """Test that Unicode data can be encoded/decoded through WebAuthn functions."""
        # Test data with various Unicode characters
        test_strings = [
            "Hello, 世界!",
            "Ελληνικά",
            "🚀 Emoji test",
            "Mixed: ASCII + 中文 + العربية",
            "Special chars: \u0000\u001f\u007f\u0080\u00ff",
        ]

        for test_str in test_strings:
            with self.subTest(test_str=test_str):
                # Convert to bytes using our unicode utility
                test_bytes = utf8bytes(test_str)

                # Encode with WebAuthn
                encoded = webauthn_encode(test_bytes)

                # Decode back
                decoded = webauthn_decode(encoded)

                # Convert back to text
                result_str = utf8text(decoded)

                self.assertEqual(test_str, result_str)

    def test_webauthn_json_with_unicode_utils(self):
        """Test WebAuthn JSON encoder with data processed by unicode utilities."""
        test_data = {
            "name": "Test User 测试用户",
            "challenge": utf8bytes("Challenge: 挑战"),
            "allowCredentials": [
                {
                    "id": utf8bytes("credential-id-中文"),
                    "type": "public-key",
                }
            ],
            "unicode_field": "🔐 Security test",
        }

        # Encode to JSON
        encoder = WebAuthnJSONEncoder()
        json_str = encoder.encode(test_data)

        # Should be valid JSON
        parsed = json.loads(json_str)

        # Check that bytes were properly encoded
        self.assertEqual(parsed["name"], "Test User 测试用户")
        self.assertIn("_bytes", parsed["challenge"])  # WebAuthn format
        self.assertIn("_bytes", parsed["allowCredentials"][0]["id"])  # WebAuthn format
        self.assertEqual(parsed["unicode_field"], "🔐 Security test")

    def test_camo_with_unicode_urls(self):
        """Test Camo client with URLs containing Unicode characters."""
        # Unicode URLs that need proper encoding
        unicode_urls = [
            "https://example.com/image-中文.jpg",
            "https://測試.com/emoji-🖼️.png",
            "https://example.com/path/with spaces and 中文.gif",
        ]

        for url in unicode_urls:
            with self.subTest(url=url):
                # Convert URL to bytes first
                url_bytes = utf8bytes(url)
                url_text = utf8text(url_bytes)  # Ensure proper UTF-8

                # Generate Camo URL
                camo_url = self.camo_client.image_url(url_text)

                # Should start with the server URL
                self.assertTrue(camo_url.startswith("http://localhost:8080/"))

                # Should contain hex-encoded data
                self.assertRegex(camo_url, r"/[0-9a-f]+/[0-9a-f]+$")

    def test_cross_function_error_handling(self):
        """Test error handling when functions are chained together."""
        # Test with None that webauthn_decode can handle
        try:
            result = webauthn_decode(None)
            # If it doesn't raise an error, result should be None or empty
            self.assertIn(result, [None, b""])
        except (TypeError, ValueError):
            # This is acceptable - the function should handle None gracefully
            pass

        # Test empty string handling
        empty_encoded = webauthn_encode(utf8bytes(""))
        self.assertEqual(utf8text(webauthn_decode(empty_encoded)), "")

        # Test with invalid UTF-8 bytes
        invalid_bytes = b"\xff\xfe"
        with self.assertRaises(UnicodeDecodeError):
            utf8text(invalid_bytes, errors="strict")

        # But should work with error handling
        result = utf8text(invalid_bytes, errors="replace")
        self.assertIsInstance(result, str)

    def test_data_consistency_across_functions(self):
        """Test that data remains consistent when passed through multiple functions."""
        original_data = {
            "text": "Original message with 中文",
            "binary": b"Binary data \x00\x01\x02",
            "unicode": "🚀 Space rocket",
        }

        # Process text through unicode utilities
        text_as_bytes = utf8bytes(original_data["text"])
        text_back = utf8text(text_as_bytes)

        # Process binary through WebAuthn encoding
        encoded_binary = webauthn_encode(original_data["binary"])
        decoded_binary = webauthn_decode(encoded_binary)

        # Create URL with unicode text
        unicode_url = f"https://example.com/{original_data['unicode']}.jpg"
        camo_url = self.camo_client.image_url(unicode_url)

        # Verify consistency
        self.assertEqual(original_data["text"], text_back)
        self.assertEqual(original_data["binary"], decoded_binary)
        self.assertIsInstance(camo_url, str)
        self.assertTrue(len(camo_url) > len(unicode_url))

    def test_large_data_integration(self):
        """Test integration with large data volumes."""
        # Create large Unicode string
        large_text = "测试数据 " * 10000

        # Process through multiple functions
        as_bytes = utf8bytes(large_text)
        encoded = webauthn_encode(as_bytes)
        decoded = webauthn_decode(encoded)
        back_to_text = utf8text(decoded)

        # Should be identical
        self.assertEqual(large_text, back_to_text)

        # Memory usage should be reasonable (no excessive copying)
        import sys

        text_size = sys.getsizeof(large_text)
        bytes_size = sys.getsizeof(as_bytes)

        # Bytes should not be dramatically larger than text
        self.assertLess(bytes_size, text_size * 2)

    def test_encoding_roundtrip_with_special_cases(self):
        """Test encoding roundtrip with special Unicode cases."""
        special_cases = [
            "\x00",  # Null byte
            "\u0001\u001f",  # Control characters
            "\u007f\u0080",  # ASCII boundary
            "\ufffd",  # Replacement character
            "\U0001f600",  # Emoji outside BMP
            "a\u0300",  # Combining character
        ]

        for test_case in special_cases:
            with self.subTest(test_case=repr(test_case)):
                # Round trip through all our functions
                step1 = utf8bytes(test_case)
                step2 = webauthn_encode(step1)
                step3 = webauthn_decode(step2)
                step4 = utf8text(step3)

                self.assertEqual(test_case, step4)

    def test_json_serialization_with_mixed_data(self):
        """Test JSON serialization with mixed Unicode and binary data."""
        mixed_data = {
            "user_name": utf8text(utf8bytes("用户名")),
            "session_id": webauthn_encode(b"session_12345"),
            "profile_image": self.camo_client.image_url("https://example.com/头像.jpg"),
            "metadata": {
                "created": "2024-01-01",
                "challenge": utf8bytes("challenge_data"),
                "description": "User profile with 中文 description",
            },
        }

        # Should serialize to JSON without errors
        encoder = WebAuthnJSONEncoder()
        json_str = encoder.encode(mixed_data)

        # Should be valid JSON
        parsed = json.loads(json_str)

        # Verify structure is preserved
        self.assertEqual(parsed["user_name"], "用户名")
        self.assertIsInstance(parsed["session_id"], str)
        self.assertTrue(parsed["profile_image"].startswith("http://localhost:8080/"))
        self.assertEqual(parsed["metadata"]["description"], "User profile with 中文 description")
        self.assertIn("_bytes", parsed["metadata"]["challenge"])  # WebAuthn format
