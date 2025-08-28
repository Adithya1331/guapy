"""Tests for guapy.crypto module.

This module tests cryptographic functionality including token encryption,
decryption, and key management.
"""

import base64
import json
from unittest.mock import patch

import pytest

from guapy.crypto import GuacamoleCrypto
from guapy.exceptions import (
    GuapyConfigurationError,
    TokenDecryptionError,
    TokenEncryptionError,
)


class TestGuacamoleCrypto:
    """Test GuacamoleCrypto class initialization and configuration."""

    def test_init_with_valid_aes_256_key(self, test_encryption_key):
        """Test initialization with valid AES-256-CBC key."""
        crypto = GuacamoleCrypto("AES-256-CBC", test_encryption_key)
        assert crypto.cipher_name == "AES-256-CBC"
        assert crypto.key == test_encryption_key.encode()

    def test_init_with_bytes_key(self, test_encryption_key):
        """Test initialization with key as bytes."""
        key_bytes = test_encryption_key.encode()
        crypto = GuacamoleCrypto("AES-256-CBC", key_bytes)
        assert crypto.key == key_bytes

    def test_init_with_invalid_key_length(self):
        """Test initialization fails with invalid key length."""
        with pytest.raises(GuapyConfigurationError) as exc_info:
            GuacamoleCrypto("AES-256-CBC", "short_key")

        error = exc_info.value
        assert "32-byte key" in str(error)
        # Check that error details contain configuration info
        assert error.details.get("config_section") == "crypto"
        assert error.details.get("config_key") == "key"

    def test_init_with_unsupported_cipher(self, test_encryption_key):
        """Test initialization fails with unsupported cipher."""
        with pytest.raises(GuapyConfigurationError) as exc_info:
            GuacamoleCrypto("UNSUPPORTED-CIPHER", test_encryption_key)

        error = exc_info.value
        assert "Unsupported cipher" in str(error)
        assert error.details.get("config_section") == "crypto"
        assert error.details.get("config_key") == "cipher_name"

    @pytest.mark.parametrize(
        "key_data,should_succeed",
        [
            ("", False),
            ("a" * 31, False),
            ("a" * 32, True),
            ("a" * 33, False),
        ],
    )
    def test_key_length_validation(self, key_data, should_succeed):
        """Test key length validation with various key lengths."""
        if should_succeed:
            crypto = GuacamoleCrypto("AES-256-CBC", key_data)
            assert crypto.key == key_data.encode()
        else:
            with pytest.raises(GuapyConfigurationError):
                GuacamoleCrypto("AES-256-CBC", key_data)


class TestTokenEncryption:
    """Test token encryption functionality."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for encryption testing."""
        return {
            "connection": {
                "protocol": "rdp",
                "hostname": "test.example.com",
                "port": 3389,
                "username": "testuser",
                "password": "testpass",  # nosec
                "width": 1920,
                "height": 1080,
                "dpi": 96,
            }
        }

    def test_encrypt_data_success(self, test_crypto, sample_data):
        """Test successful data encryption."""
        encrypted_token = test_crypto.encrypt(sample_data)

        assert isinstance(encrypted_token, str)
        assert len(encrypted_token) > 0
        # Encrypted token should be base64 encoded
        assert base64.b64decode(encrypted_token.encode())

    def test_encrypt_data_with_none_values(self, test_crypto):
        """Test data encryption with None values."""
        data = {
            "connection": {
                "protocol": "rdp",
                "hostname": None,
                "port": None,
                "username": None,
                "password": None,
                "width": 1920,
                "height": 1080,
                "dpi": 96,
            }
        }

        encrypted_token = test_crypto.encrypt(data)
        assert isinstance(encrypted_token, str)
        assert len(encrypted_token) > 0

    def test_encrypt_large_data(self, test_crypto):
        """Test encryption of large data."""
        large_data = {
            "connection": {
                "protocol": "rdp",
                "hostname": "x" * 1000,
                "port": 3389,
                "username": "x" * 1000,
                "password": "x" * 1000,
                "width": 1920,
                "height": 1080,
                "dpi": 96,
            }
        }

        encrypted_token = test_crypto.encrypt(large_data)
        assert isinstance(encrypted_token, str)
        assert len(encrypted_token) > 0

    def test_encrypt_produces_different_results(self, test_crypto, sample_data):
        """Test that encryption produces different results due to random IV."""
        encrypted1 = test_crypto.encrypt(sample_data)
        encrypted2 = test_crypto.encrypt(sample_data)

        # Should be different due to random IV
        assert encrypted1 != encrypted2

    def test_encrypt_with_encryption_error(self, test_crypto, sample_data):
        """Test handling of encryption errors."""
        with patch.object(test_crypto, "algorithm") as mock_algorithm:
            mock_algorithm.side_effect = Exception("Encryption failed")

            with pytest.raises(TokenEncryptionError) as exc_info:
                test_crypto.encrypt(sample_data)

            error = exc_info.value
            assert "Token encryption failed" in str(error)


class TestTokenDecryption:
    """Test token decryption functionality."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for decryption testing."""
        return {
            "connection": {
                "protocol": "rdp",
                "hostname": "test.example.com",
                "port": 3389,
                "username": "testuser",
                "password": "testpass",  # nosec
                "width": 1920,
                "height": 1080,
                "dpi": 96,
            }
        }

    def test_decrypt_token_success(self, test_crypto, sample_data):
        """Test successful token decryption."""
        # Encrypt then decrypt
        encrypted_token = test_crypto.encrypt(sample_data)
        decrypted_data = test_crypto.decrypt(encrypted_token)

        assert isinstance(decrypted_data, dict)
        assert decrypted_data["connection"]["protocol"] == "rdp"
        assert decrypted_data["connection"]["hostname"] == "test.example.com"
        assert decrypted_data["connection"]["port"] == 3389

    def test_decrypt_token_with_none_values(self, test_crypto):
        """Test decryption of token with None values."""
        data = {
            "connection": {
                "protocol": "rdp",
                "hostname": None,
                "port": None,
                "username": None,
                "password": None,
                "width": 1920,
                "height": 1080,
                "dpi": 96,
            }
        }

        encrypted_token = test_crypto.encrypt(data)
        decrypted_data = test_crypto.decrypt(encrypted_token)

        assert decrypted_data["connection"]["hostname"] is None
        assert decrypted_data["connection"]["port"] is None
        assert decrypted_data["connection"]["username"] is None
        assert decrypted_data["connection"]["password"] is None

    def test_decrypt_invalid_base64_token(self, test_crypto):
        """Test decryption fails with invalid base64 token."""
        with pytest.raises(TokenDecryptionError) as exc_info:
            test_crypto.decrypt("invalid_base64!")

        error = exc_info.value
        assert "Invalid base64 encoding" in str(error)

    def test_decrypt_token_too_short(self, test_crypto):
        """Test decryption fails with token too short for IV."""
        short_token = base64.b64encode(b"short").decode()

        with pytest.raises(TokenDecryptionError) as exc_info:
            test_crypto.decrypt(short_token)

        error = exc_info.value
        assert "Invalid token JSON" in str(error)

    def test_decrypt_corrupted_token(self, test_crypto):
        """Test decryption fails with corrupted token data."""
        # Create a token with valid base64 but invalid JSON structure
        corrupted_json = json.dumps({"iv": "invalid", "value": "invalid"})
        corrupted_token = base64.b64encode(corrupted_json.encode()).decode()

        with pytest.raises(TokenDecryptionError) as exc_info:
            test_crypto.decrypt(corrupted_token)

        error = exc_info.value
        assert "Invalid IV or encrypted data" in str(error)

    def test_decrypt_token_with_wrong_key(self, sample_data):
        """Test decryption fails when using wrong key."""
        # Encrypt with one key
        crypto1 = GuacamoleCrypto("AES-256-CBC", "a" * 32)
        encrypted_token = crypto1.encrypt(sample_data)

        # Try to decrypt with different key
        crypto2 = GuacamoleCrypto("AES-256-CBC", "b" * 32)

        with pytest.raises(TokenDecryptionError):
            crypto2.decrypt(encrypted_token)


class TestEncryptionDecryptionRoundTrip:
    """Test encryption/decryption round trip scenarios."""

    def test_round_trip_basic_data(self, test_crypto):
        """Test basic round trip encryption/decryption."""
        original_data = {
            "connection": {
                "protocol": "rdp",
                "hostname": "test.example.com",
                "port": 3389,
                "username": "testuser",
                "password": "testpass",  # nosec
                "width": 1920,
                "height": 1080,
                "dpi": 96,
            }
        }

        encrypted = test_crypto.encrypt(original_data)
        decrypted = test_crypto.decrypt(encrypted)

        assert decrypted == original_data

    def test_round_trip_empty_strings(self, test_crypto):
        """Test round trip with empty string values."""
        data = {
            "connection": {
                "protocol": "rdp",
                "hostname": "",
                "port": 0,
                "username": "",
                "password": "",
                "width": 1920,
                "height": 1080,
                "dpi": 96,
            }
        }

        encrypted = test_crypto.encrypt(data)
        decrypted = test_crypto.decrypt(encrypted)

        assert decrypted["connection"]["hostname"] == ""
        assert decrypted["connection"]["username"] == ""
        assert decrypted["connection"]["password"] == ""

    def test_round_trip_unicode_data(self, test_crypto):
        """Test round trip with unicode characters."""
        data = {
            "connection": {
                "protocol": "rdp",
                "hostname": "服务器.example.com",
                "port": 3389,
                "username": "用户名",
                "password": "密码123",  # nosec
                "width": 1920,
                "height": 1080,
                "dpi": 96,
            }
        }

        encrypted = test_crypto.encrypt(data)
        decrypted = test_crypto.decrypt(encrypted)

        assert decrypted == data

    def test_round_trip_special_characters(self, test_crypto):
        """Test round trip with special characters."""
        data = {
            "connection": {
                "protocol": "ssh",
                "hostname": "test.example.com",
                "port": 22,
                "username": "user@domain.com",
                "password": "pass!@#$%^&*()",  # nosec
                "width": 1920,
                "height": 1080,
                "dpi": 96,
            }
        }

        encrypted = test_crypto.encrypt(data)
        decrypted = test_crypto.decrypt(encrypted)

        assert decrypted == data

    def test_round_trip_multiple_tokens(self, test_crypto):
        """Test encryption/decryption of multiple different tokens."""
        data_list = [
            {
                "connection": {
                    "protocol": "rdp",
                    "hostname": f"host-{i}.example.com",
                    "port": 3389 + i,
                    "username": f"user{i}",
                    "password": f"pass{i}",  # nosec
                    "width": 1920,
                    "height": 1080,
                    "dpi": 96,
                }
            }
            for i in range(10)
        ]

        encrypted_tokens = [test_crypto.encrypt(data) for data in data_list]
        decrypted_data = [test_crypto.decrypt(enc) for enc in encrypted_tokens]

        for original, decrypted in zip(data_list, decrypted_data):
            assert decrypted == original


class TestCryptoLogging:
    """Test crypto module logging functionality."""

    def test_crypto_initialization_logging(self, test_encryption_key, caplog):
        """Test that crypto initialization logs appropriate messages."""
        import logging

        caplog.set_level(logging.DEBUG)

        GuacamoleCrypto("AES-256-CBC", test_encryption_key)

        # Check that initialization was logged
        assert any(
            "Initialized crypto with cipher" in record.message
            for record in caplog.records
        )

    def test_invalid_cipher_logging(self, test_encryption_key, caplog):
        """Test that invalid cipher attempts are logged."""
        import logging

        caplog.set_level(logging.DEBUG)

        with pytest.raises(GuapyConfigurationError):
            GuacamoleCrypto("INVALID-CIPHER", test_encryption_key)

        # Should have debug logs about the attempt
        assert len(caplog.records) > 0


class TestCryptoEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_data_serialization(self, test_crypto):
        """Test encryption of minimal data."""
        minimal_data = {"connection": {}}

        encrypted = test_crypto.encrypt(minimal_data)
        decrypted = test_crypto.decrypt(encrypted)

        assert decrypted == minimal_data

    def test_json_serialization_edge_cases(self, test_crypto):
        """Test JSON serialization with problematic values."""
        # Test with very large numbers
        data = {
            "connection": {
                "protocol": "rdp",
                "hostname": "test.com",
                "port": 999999,
                "username": "user",
                "password": "pass",  # nosec
                "width": 999999,
                "height": 999999,
                "dpi": 999999,
            }
        }

        encrypted = test_crypto.encrypt(data)
        decrypted = test_crypto.decrypt(encrypted)

        assert decrypted["connection"]["port"] == 999999
        assert decrypted["connection"]["width"] == 999999

    def test_memory_usage_with_large_data(self, test_crypto):
        """Test memory usage doesn't explode with large data."""
        # Create data with large string values
        large_value = "x" * 10000
        data = {
            "connection": {
                "protocol": "rdp",
                "hostname": large_value,
                "port": 3389,
                "username": large_value,
                "password": large_value,
                "width": 1920,
                "height": 1080,
                "dpi": 96,
            }
        }

        # This should complete without memory issues
        encrypted = test_crypto.encrypt(data)
        decrypted = test_crypto.decrypt(encrypted)

        assert len(decrypted["connection"]["hostname"]) == 10000
        assert len(decrypted["connection"]["username"]) == 10000


class TestCryptoSecurity:
    """Test security aspects of the crypto implementation."""

    def test_iv_randomness(self, test_crypto):
        """Test that IVs are properly randomized."""
        data = {"connection": {"protocol": "rdp", "hostname": "test.com"}}

        # Encrypt the same data multiple times
        encrypted_tokens = [test_crypto.encrypt(data) for _ in range(10)]

        # All encrypted tokens should be different due to random IVs
        unique_tokens = set(encrypted_tokens)
        assert len(unique_tokens) == len(encrypted_tokens), (
            "IVs are not properly randomized"
        )

    def test_padding_oracle_resistance(self, test_crypto):
        """Test resistance to padding oracle attacks."""
        # Create various malformed tokens
        malformed_tokens = [
            base64.b64encode(b"short").decode(),  # Too short
            base64.b64encode(b"{'invalid': 'json'").decode(),  # Invalid JSON
            # Missing fields
            base64.b64encode(json.dumps({"missing": "fields"}).encode()).decode(),
        ]

        for token in malformed_tokens:
            with pytest.raises(TokenDecryptionError):
                test_crypto.decrypt(token)

    def test_no_key_exposure_in_errors(self, test_encryption_key):
        """Test that encryption keys are not exposed in error messages."""
        try:
            GuacamoleCrypto("AES-256-CBC", "wrong_length")
        except GuapyConfigurationError as e:
            # Error message should not contain the actual key
            assert test_encryption_key not in str(e)
            assert "wrong_length" not in str(e)  # Key shouldn't be in error msg


@pytest.mark.parametrize("cipher_name", ["AES-256-CBC"])
class TestCipherSpecificBehavior:
    """Test behavior specific to different cipher implementations."""

    def test_cipher_specific_initialization(self, cipher_name, test_encryption_key):
        """Test cipher-specific initialization."""
        crypto = GuacamoleCrypto(cipher_name, test_encryption_key)
        assert crypto.cipher_name == cipher_name

    def test_cipher_specific_encryption_properties(
        self, cipher_name, test_encryption_key
    ):
        """Test cipher-specific encryption properties."""
        crypto = GuacamoleCrypto(cipher_name, test_encryption_key)
        data = {"connection": {"protocol": "rdp", "hostname": "test.com"}}

        encrypted = crypto.encrypt(data)

        # Decode the outer base64 layer
        decoded_json = base64.b64decode(encrypted.encode()).decode()
        token_data = json.loads(decoded_json)

        if cipher_name == "AES-256-CBC":
            # Should have iv and value fields
            assert "iv" in token_data
            assert "value" in token_data

            # IV should be 16 bytes when decoded
            iv = base64.b64decode(token_data["iv"])
            assert len(iv) == 16

            # Encrypted value should be properly padded for AES blocks
            encrypted_data = base64.b64decode(token_data["value"])
            assert len(encrypted_data) % 16 == 0  # Proper AES block padding
