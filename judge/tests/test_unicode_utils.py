"""
Tests for judge.utils.unicode module.

This module tests critical Python 2/3 migration edge cases for Unicode handling,
ensuring proper bytes/str conversion and encoding behavior.
"""

import unittest

from judge.utils.unicode import utf8bytes, utf8text


class UnicodeUtilsTest(unittest.TestCase):
    """Test utf8bytes and utf8text functions with various edge cases."""

    def test_utf8bytes_with_none(self):
        """Test utf8bytes handles None input correctly."""
        self.assertIsNone(utf8bytes(None))

    def test_utf8bytes_with_str(self):
        """Test utf8bytes converts string to bytes correctly."""
        # Basic ASCII string
        result = utf8bytes("hello")
        self.assertEqual(result, b"hello")
        self.assertIsInstance(result, bytes)

        # Unicode string with special characters
        cafe_str = "café"
        result = utf8bytes(cafe_str)
        expected_bytes = cafe_str.encode("utf-8")  # Testing UTF-8 encoding specifically
        self.assertEqual(result, expected_bytes)
        self.assertIsInstance(result, bytes)

        # Empty string
        result = utf8bytes("")
        self.assertEqual(result, b"")
        self.assertIsInstance(result, bytes)

    def test_utf8bytes_with_bytes(self):
        """Test utf8bytes returns bytes unchanged."""
        # Basic bytes
        input_bytes = b"hello"
        result = utf8bytes(input_bytes)
        self.assertEqual(result, input_bytes)
        self.assertIs(result, input_bytes)  # Should be the same object

        # Unicode bytes
        cafe_str = "café"
        input_bytes = cafe_str.encode("utf-8")  # Testing UTF-8 encoding specifically
        result = utf8bytes(input_bytes)
        self.assertEqual(result, input_bytes)
        self.assertIs(result, input_bytes)

        # Empty bytes
        input_bytes = b""
        result = utf8bytes(input_bytes)
        self.assertEqual(result, input_bytes)
        self.assertIs(result, input_bytes)

    def test_utf8bytes_with_unicode_edge_cases(self):
        """Test utf8bytes with various Unicode edge cases."""
        test_cases = [
            # Emoji
            "🚀🌟",
            # Mathematical symbols
            "∑∏∆√",
            # Various scripts
            "中文测试",  # Chinese
            "العربية",  # Arabic
            "русский",  # Russian
            "日本語",  # Japanese
            # Combining characters
            "é",  # e + combining acute accent
            # Control characters
            "\x00\x01\x02",
            # High Unicode codepoints
            "𝕌𝕟𝕚𝕔𝕠𝕕𝕖",
        ]

        for test_str in test_cases:
            with self.subTest(string=test_str):
                result = utf8bytes(test_str)
                self.assertEqual(result, test_str.encode("utf-8"))
                self.assertIsInstance(result, bytes)

    def test_utf8text_with_none(self):
        """Test utf8text handles None input correctly."""
        self.assertIsNone(utf8text(None))
        self.assertIsNone(utf8text(None, errors="ignore"))

    def test_utf8text_with_str(self):
        """Test utf8text returns string unchanged."""
        # Basic ASCII string
        input_str = "hello"
        result = utf8text(input_str)
        self.assertEqual(result, input_str)
        self.assertIs(result, input_str)  # Should be the same object

        # Unicode string
        input_str = "café"
        result = utf8text(input_str)
        self.assertEqual(result, input_str)
        self.assertIs(result, input_str)

        # Empty string
        input_str = ""
        result = utf8text(input_str)
        self.assertEqual(result, input_str)
        self.assertIs(result, input_str)

    def test_utf8text_with_bytes(self):
        """Test utf8text converts bytes to string correctly."""
        # Basic ASCII bytes
        result = utf8text(b"hello")
        self.assertEqual(result, "hello")
        self.assertIsInstance(result, str)

        # Unicode bytes
        cafe_str = "café"
        utf8_bytes = cafe_str.encode("utf-8")  # Testing UTF-8 encoding specifically
        result = utf8text(utf8_bytes)
        self.assertEqual(result, cafe_str)
        self.assertIsInstance(result, str)

        # Empty bytes
        result = utf8text(b"")
        self.assertEqual(result, "")
        self.assertIsInstance(result, str)

    def test_utf8text_with_error_handling(self):
        """Test utf8text error handling modes."""
        # Invalid UTF-8 bytes
        invalid_bytes = b"\xff\xfe"

        # Strict mode (default) should raise
        with self.assertRaises(UnicodeDecodeError):
            utf8text(invalid_bytes)

        with self.assertRaises(UnicodeDecodeError):
            utf8text(invalid_bytes, errors="strict")

        # Ignore mode should skip invalid bytes
        result = utf8text(invalid_bytes, errors="ignore")
        self.assertIsInstance(result, str)
        self.assertEqual(result, "")

        # Replace mode should replace with replacement character
        result = utf8text(invalid_bytes, errors="replace")
        self.assertIsInstance(result, str)
        self.assertIn("�", result)

        # Test with mixed valid/invalid bytes
        mixed_bytes = b"hello\xff\xfeworld"
        result = utf8text(mixed_bytes, errors="ignore")
        self.assertEqual(result, "helloworld")

        result = utf8text(mixed_bytes, errors="replace")
        self.assertTrue(result.startswith("hello"))
        self.assertTrue(result.endswith("world"))
        self.assertIn("�", result)

    def test_utf8text_with_unicode_edge_cases(self):
        """Test utf8text with various Unicode edge cases."""
        test_cases = [
            # Emoji
            "🚀🌟",
            # Mathematical symbols
            "∑∏∆√",
            # Various scripts
            "中文测试",  # Chinese
            "العربية",  # Arabic
            "русский",  # Russian
            "日本語",  # Japanese
            # Combining characters
            "é",  # e + combining acute accent
            # Control characters
            "\x00\x01\x02",
            # High Unicode codepoints
            "𝕌𝕟𝕚𝕔𝕠𝕕𝕖",
        ]

        for test_str in test_cases:
            with self.subTest(string=test_str):
                utf8_bytes = test_str.encode("utf-8")
                result = utf8text(utf8_bytes)
                self.assertEqual(result, test_str)
                self.assertIsInstance(result, str)

    def test_roundtrip_conversion(self):
        """Test that utf8bytes and utf8text are inverse operations."""
        test_cases = [
            "hello",
            "café",
            "🚀🌟",
            "中文测试",
            "العربية",
            "русский",
            "日本語",
            "",
            "\x00\x01\x02",
            "𝕌𝕟𝕚𝕔𝕠𝕕𝕖",
        ]

        for test_str in test_cases:
            with self.subTest(string=test_str):
                # str -> bytes -> str
                bytes_result = utf8bytes(test_str)
                str_result = utf8text(bytes_result)
                self.assertEqual(str_result, test_str)

                # bytes -> str -> bytes
                original_bytes = test_str.encode("utf-8")
                str_result = utf8text(original_bytes)
                bytes_result = utf8bytes(str_result)
                self.assertEqual(bytes_result, original_bytes)

    def test_type_preservation_with_none(self):
        """Test that None values are properly preserved through conversions."""
        self.assertIsNone(utf8bytes(None))
        self.assertIsNone(utf8text(None))
        self.assertIsNone(utf8text(None, errors="ignore"))
        self.assertIsNone(utf8text(None, errors="replace"))

    def test_memory_efficiency(self):
        """Test that functions don't unnecessarily copy data."""
        # utf8bytes should return the same bytes object
        original_bytes = b"test data"
        result = utf8bytes(original_bytes)
        self.assertIs(result, original_bytes)

        # utf8text should return the same string object
        original_str = "test data"
        result = utf8text(original_str)
        self.assertIs(result, original_str)

    def test_large_data_handling(self):
        """Test handling of large data volumes."""
        # Large string
        large_str = "x" * 100000
        result = utf8bytes(large_str)
        self.assertEqual(len(result), 100000)
        self.assertIsInstance(result, bytes)

        # Large bytes
        large_bytes = b"x" * 100000
        result = utf8text(large_bytes)
        self.assertEqual(len(result), 100000)
        self.assertIsInstance(result, str)

    def test_edge_case_empty_and_whitespace(self):
        """Test edge cases with empty strings and whitespace."""
        test_cases = [
            "",
            " ",
            "\t",
            "\n",
            "\r\n",
            "   \t\n  ",
        ]

        for test_str in test_cases:
            with self.subTest(string=repr(test_str)):
                # Test utf8bytes
                bytes_result = utf8bytes(test_str)
                self.assertEqual(bytes_result, test_str.encode("utf-8"))
                self.assertIsInstance(bytes_result, bytes)

                # Test utf8text
                str_result = utf8text(bytes_result)
                self.assertEqual(str_result, test_str)
                self.assertIsInstance(str_result, str)

    def test_boundary_value_unicode_codepoints(self):
        """Test boundary Unicode codepoints."""
        # Test various Unicode boundary conditions
        test_cases = [
            "\u0000",  # NULL
            "\u007f",  # DEL (last ASCII)
            "\u0080",  # First non-ASCII
            "\u00ff",  # Last Latin-1
            "\u0100",  # First extended Latin
            "\uffff",  # Last Basic Multilingual Plane
            "\U00010000",  # First supplementary plane
            "\U0010ffff",  # Last valid Unicode codepoint
        ]

        for test_char in test_cases:
            with self.subTest(codepoint=ord(test_char)):
                # Test roundtrip conversion
                bytes_result = utf8bytes(test_char)
                str_result = utf8text(bytes_result)
                self.assertEqual(str_result, test_char)

    def test_invalid_input_types(self):
        """Test behavior with invalid input types."""
        invalid_inputs = [
            123,
            [],
            {},
            object(),
        ]

        for invalid_input in invalid_inputs:
            with self.subTest(input_type=type(invalid_input).__name__):
                # utf8bytes should raise AttributeError for non-string/bytes/None
                with self.assertRaises(AttributeError):
                    utf8bytes(invalid_input)

                # utf8text should raise AttributeError for non-string/bytes/None
                with self.assertRaises(AttributeError):
                    utf8text(invalid_input)


if __name__ == "__main__":
    unittest.main()
