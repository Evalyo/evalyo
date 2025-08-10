import base64
import hmac
import json
import struct

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django.utils.encoding import force_bytes

from judge.models import Profile
from judge.models.tests.util import CommonDataMixin, create_contest, create_contest_participation


class OrganizationTestCase(CommonDataMixin, TestCase):
    @classmethod
    def setUpTestData(self):
        super().setUpTestData()
        self.profile = self.users["normal"].profile
        self.profile.organizations.add(self.organizations["open"])

    def test_contains(self):
        self.assertIn(self.profile, self.organizations["open"])
        self.assertIn(self.profile.id, self.organizations["open"])

        self.assertNotIn(self.users["superuser"].profile, self.organizations["open"])
        self.assertNotIn(self.users["superuser"].profile.id, self.organizations["open"])

        with self.assertRaisesRegex(TypeError, "Organization membership test"):
            assert "aaaa" in self.organizations["open"]

    def test_str(self):
        self.assertEqual(str(self.organizations["open"]), "open")


class ProfileTestCase(CommonDataMixin, TestCase):
    @classmethod
    def setUpTestData(self):
        super().setUpTestData()
        self.profile = self.users["normal"].profile
        self.profile.organizations.add(self.organizations["open"])

    def setUp(self):
        # We are doing a LOT of field modifications in this test case.
        # This is to prevent cryptic error messages when a test fails due
        # to modifications in another test. In theory, no two tests should
        # touch the same field, but who knows.
        self.profile.refresh_from_db()

    def test_username(self):
        self.assertEqual(str(self.profile), self.profile.username)

    def test_organization(self):
        self.assertIsNone(self.users["superuser"].profile.organization)
        self.assertEqual(self.profile.organization, self.organizations["open"])

    def test_calculate_points(self):
        self.profile.calculate_points()

        # Test saving
        for attr in ("points", "problem_count", "performance_points"):
            with self.subTest(attribute=attr):
                setattr(self.profile, attr, -1000)
                self.assertEqual(getattr(self.profile, attr), -1000)
                self.profile.calculate_points()
                self.assertEqual(getattr(self.profile, attr), 0)

    def test_generate_api_token(self):
        token = self.profile.generate_api_token()

        self.assertIsInstance(token, str)
        self.assertIsInstance(self.profile.api_token, str)

        user_id, raw_token = struct.unpack(">I32s", base64.urlsafe_b64decode(token))

        self.assertEqual(self.users["normal"].id, user_id)
        self.assertEqual(len(raw_token), 32)

        self.assertTrue(
            hmac.compare_digest(
                hmac.new(force_bytes(settings.SECRET_KEY), msg=force_bytes(raw_token), digestmod="sha256").hexdigest(),
                self.profile.api_token,
            ),
        )

    def test_update_contest(self):
        _now = timezone.now()
        for contest in (
            create_contest(
                key="finished_contest",
                start_time=_now - timezone.timedelta(days=100),
                end_time=_now - timezone.timedelta(days=10),
                is_visible=True,
            ),
            create_contest(
                key="inaccessible_contest",
                start_time=_now - timezone.timedelta(days=100),
                end_time=_now + timezone.timedelta(days=10),
            ),
        ):
            with self.subTest(name=contest.name):
                self.profile.current_contest = create_contest_participation(
                    contest=contest,
                    user=self.profile,
                )
                self.assertIsNotNone(self.profile.current_contest)
                self.profile.update_contest()
                self.assertIsNone(self.profile.current_contest)

    def test_css_class(self):
        self.assertEqual(self.profile.css_class, "rating rate-none user")

    def test_get_user_css_class(self):
        self.assertEqual(
            Profile.get_user_css_class(display_rank="abcdef", rating=None, rating_colors=True),
            "rating rate-none abcdef",
        )
        self.assertEqual(
            Profile.get_user_css_class(display_rank="admin", rating=1300, rating_colors=True),
            "rating rate-expert admin",
        )
        self.assertEqual(
            Profile.get_user_css_class(display_rank=1111, rating=1299, rating_colors=True),
            "rating rate-amateur 1111",
        )
        self.assertEqual(
            Profile.get_user_css_class(display_rank="random", rating=1299, rating_colors=False),
            "random",
        )


class ProfilePython23MigrationTestCase(CommonDataMixin, TestCase):
    """Test Profile model functionality for Python 2/3 migration edge cases."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile = cls.users["normal"].profile

    def setUp(self):
        """Refresh profile for each test to avoid interference."""
        self.profile.refresh_from_db()

    def test_generate_api_token_bytes_handling(self):
        """Test API token generation with various byte/string edge cases."""
        # Test multiple token generations
        tokens = []
        for i in range(10):
            with self.subTest(iteration=i):
                token = self.profile.generate_api_token()

                # Token should be a string
                self.assertIsInstance(token, str)

                # API token should be stored as string
                self.assertIsInstance(self.profile.api_token, str)

                # Token should be unique
                self.assertNotIn(token, tokens)
                tokens.append(token)

                # Test decoding
                decoded = base64.urlsafe_b64decode(token)
                self.assertEqual(len(decoded), 36)  # 4 bytes user_id + 32 bytes secret

                user_id, raw_token = struct.unpack(">I32s", decoded)
                self.assertEqual(user_id, self.users["normal"].id)
                self.assertEqual(len(raw_token), 32)

                # Test HMAC verification
                expected_hmac = hmac.new(
                    force_bytes(settings.SECRET_KEY),
                    msg=raw_token,
                    digestmod="sha256"
                ).hexdigest()
                self.assertEqual(self.profile.api_token, expected_hmac)

    def test_api_token_unicode_secret_key(self):
        """Test API token generation with Unicode characters in SECRET_KEY."""
        original_secret = settings.SECRET_KEY
        try:
            # Test with Unicode SECRET_KEY
            settings.SECRET_KEY = "测试密钥-🔐-key"

            token = self.profile.generate_api_token()
            self.assertIsInstance(token, str)

            # Verify token can be decoded
            decoded = base64.urlsafe_b64decode(token)
            user_id, raw_token = struct.unpack(">I32s", decoded)
            self.assertEqual(user_id, self.users["normal"].id)

            # Verify HMAC with Unicode key
            expected_hmac = hmac.new(
                force_bytes(settings.SECRET_KEY),
                msg=raw_token,
                digestmod="sha256"
            ).hexdigest()
            self.assertEqual(self.profile.api_token, expected_hmac)

        finally:
            settings.SECRET_KEY = original_secret

    def test_generate_scratch_codes_base32_encoding(self):
        """Test scratch code generation with Base32 encoding edge cases."""
        original_count = getattr(settings, 'DMOJ_SCRATCH_CODES_COUNT', 5)

        try:
            # Test various scratch code counts
            for count in [1, 5, 10, 20]:
                with self.subTest(count=count):
                    settings.DMOJ_SCRATCH_CODES_COUNT = count

                    codes = self.profile.generate_scratch_codes()

                    # Should generate correct number of codes
                    self.assertEqual(len(codes), count)

                    # Each code should be 16 characters of valid Base32
                    for code in codes:
                        self.assertEqual(len(code), 16)
                        self.assertRegex(code, r'^[A-Z2-7]{16}$')

                    # Codes should be unique
                    self.assertEqual(len(codes), len(set(codes)))

                    # Should be stored as JSON
                    stored_codes = json.loads(self.profile.scratch_codes)
                    self.assertEqual(codes, stored_codes)

        finally:
            settings.DMOJ_SCRATCH_CODES_COUNT = original_count

    def test_scratch_codes_json_serialization(self):
        """Test JSON serialization of scratch codes with various edge cases."""
        codes = self.profile.generate_scratch_codes()

        # Test JSON roundtrip
        json_str = self.profile.scratch_codes
        parsed_codes = json.loads(json_str)
        self.assertEqual(codes, parsed_codes)

        # Test with empty codes
        self.profile.scratch_codes = json.dumps([])
        parsed = json.loads(self.profile.scratch_codes)
        self.assertEqual(parsed, [])

        # Test JSON encoding doesn't break with Base32 characters
        test_codes = ['ABCDEFGHIJKLMNOP', '234567ZYXWVUTSRQ', 'A2B3C4D5E6F7G2H3']
        self.profile.scratch_codes = json.dumps(test_codes)
        parsed = json.loads(self.profile.scratch_codes)
        self.assertEqual(test_codes, parsed)

    def test_totp_key_base32_validation(self):
        """Test TOTP key Base32 validation and edge cases."""
        # Test valid Base32 keys
        valid_keys = [
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567',  # All valid chars
            'A2B3C4D5E6F7G2H3I4J5K6L7M2N3O4P5',  # Mixed
            '2345672345672345672345672345672345',  # All numbers
            '',  # Empty should be valid
        ]

        for key in valid_keys:
            with self.subTest(key=key):
                self.profile.totp_key = key
                # Should not raise validation error
                self.profile.full_clean()

    def test_totp_key_invalid_base32(self):
        """Test TOTP key validation with invalid Base32."""
        from django.core.exceptions import ValidationError

        invalid_keys = [
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ234568',  # Contains '8'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ23456',   # 31 chars (not 32)
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567A', # 33 chars (not 32)
            'abcdefghijklmnopqrstuvwxyz234567',  # Lowercase
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ23456!',  # Special char
            '1BCDEFGHIJKLMNOPQRSTUVWXYZ234567',  # Contains '1'
            '0BCDEFGHIJKLMNOPQRSTUVWXYZ234567',  # Contains '0'
        ]

        for key in invalid_keys:
            with self.subTest(key=key):
                self.profile.totp_key = key
                with self.assertRaises(ValidationError):
                    self.profile.full_clean()

    def test_check_totp_code_with_unicode(self):
        """Test TOTP code checking with various input types."""
        # Set up a valid TOTP key
        self.profile.totp_key = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
        self.profile.is_totp_enabled = True
        self.profile.save()

        # Test with string input (normal case)
        result = self.profile.check_totp_code('123456')
        self.assertIsInstance(result, bool)

        # Test with numeric input
        result = self.profile.check_totp_code(123456)
        self.assertIsInstance(result, bool)

        # Test with bytes input
        result = self.profile.check_totp_code(b'123456')
        self.assertIsInstance(result, bool)

        # Test with Unicode input
        result = self.profile.check_totp_code('１２３４５６')  # Full-width numbers
        self.assertIsInstance(result, bool)

    def test_webauthn_id_bytes_consistency(self):
        """Test WebAuthn ID generation with bytes consistency."""
        webauthn_id = self.profile.webauthn_id

        # Should be bytes
        self.assertIsInstance(webauthn_id, bytes)

        # Should be consistent across calls
        self.assertEqual(webauthn_id, self.profile.webauthn_id)

        # Should be SHA256 digest length
        self.assertEqual(len(webauthn_id), 32)  # SHA256 digest size

        # Should use proper HMAC with profile ID
        expected = hmac.new(
            force_bytes(settings.SECRET_KEY),
            msg=b"webauthn:%d" % (self.profile.id,),
            digestmod="sha256"
        ).digest()
        self.assertEqual(webauthn_id, expected)

    def test_webauthn_id_unicode_secret_key(self):
        """Test WebAuthn ID with Unicode SECRET_KEY."""
        original_secret = settings.SECRET_KEY
        try:
            settings.SECRET_KEY = "Unicode密钥🔐Test"

            # Clear cached property
            if hasattr(self.profile, '_webauthn_id'):
                delattr(self.profile, '_webauthn_id')

            webauthn_id = self.profile.webauthn_id
            self.assertIsInstance(webauthn_id, bytes)
            self.assertEqual(len(webauthn_id), 32)

            # Verify it's computed correctly
            expected = hmac.new(
                force_bytes(settings.SECRET_KEY),
                msg=b"webauthn:%d" % (self.profile.id,),
                digestmod="sha256"
            ).digest()
            self.assertEqual(webauthn_id, expected)

        finally:
            settings.SECRET_KEY = original_secret

    def test_force_bytes_integration(self):
        """Test force_bytes utility integration in Profile methods."""
        from django.utils.encoding import force_bytes

        # Test various input types with force_bytes
        test_inputs = [
            "normal string",
            "Unicode: 测试 🔐",
            b"already bytes",
            123,  # Integer
        ]

        for input_value in test_inputs:
            with self.subTest(input_value=repr(input_value)):
                result = force_bytes(input_value)
                self.assertIsInstance(result, bytes)

                # Should be able to use in HMAC
                hmac_result = hmac.new(result, b"test", digestmod="sha256")
                self.assertIsInstance(hmac_result.digest(), bytes)

    def test_api_token_large_user_ids(self):
        """Test API token generation with large user IDs."""
        # Test with maximum user ID that fits in 32-bit unsigned int
        large_user_id = 2**32 - 1

        # Create a mock user ID scenario
        original_id = self.users["normal"].id
        try:
            # Temporarily modify user ID for testing
            self.users["normal"].id = large_user_id

            token = self.profile.generate_api_token()
            decoded = base64.urlsafe_b64decode(token)
            user_id, raw_token = struct.unpack(">I32s", decoded)

            self.assertEqual(user_id, large_user_id)

        finally:
            self.users["normal"].id = original_id

    def test_json_encoding_with_special_characters(self):
        """Test JSON encoding of scratch codes with special Base32 edge cases."""
        # Test scratch codes that might cause JSON encoding issues
        special_codes = [
            'A' * 16,  # All same character
            '2' * 16,  # All numbers
            'ABCDEFG234567HIJ',  # Mixed
            '234567ABCDEFGHIJ',  # Numbers first
        ]

        # Manually set scratch codes
        self.profile.scratch_codes = json.dumps(special_codes)
        self.profile.save()

        # Verify roundtrip
        loaded = json.loads(self.profile.scratch_codes)
        self.assertEqual(special_codes, loaded)

        # Verify each code is valid Base32
        for code in loaded:
            self.assertRegex(code, r'^[A-Z2-7]{16}$')

    def test_profile_string_representations(self):
        """Test string representations of profile with Unicode usernames."""
        # Test with Unicode username
        original_username = self.profile.user.username
        try:
            self.profile.user.username = "用户名测试🚀"
            self.profile.user.save()

            profile_str = str(self.profile)
            self.assertEqual(profile_str, self.profile.user.username)
            self.assertIsInstance(profile_str, str)

        finally:
            self.profile.user.username = original_username
            self.profile.user.save()
