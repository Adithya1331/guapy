"""Cryptographic functions for token encryption and decryption."""

import base64
import json
import logging
import os
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .exceptions import (
    GuapyConfigurationError,
    TokenDecryptionError,
    TokenEncryptionError,
)


class GuacamoleCrypto:
    """Handles encryption and decryption of connection tokens."""

    def __init__(self, cipher_name: str, key: str):
        """Initialize crypto handler.

        Args:
            cipher_name: Name of the cipher (e.g., 'AES-256-CBC')
            key: Encryption key
        """
        self.cipher_name = cipher_name
        self.key = key.encode() if isinstance(key, str) else key
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"Initialized crypto with cipher: {cipher_name}")

        if cipher_name == "AES-256-CBC":
            if len(self.key) != 32:
                raise GuapyConfigurationError(
                    f"AES-256-CBC requires a 32-byte key, got {len(self.key)} bytes",
                    config_section="crypto",
                    config_key="key",
                    expected_type="32-byte key",
                    actual_value=f"{len(self.key)} bytes",
                )
            self.algorithm = algorithms.AES(self.key)
        else:
            raise GuapyConfigurationError(
                f"Unsupported cipher: {cipher_name}",
                config_section="crypto",
                config_key="cipher_name",
                expected_type="AES-256-CBC",
                actual_value=cipher_name,
            )

    def encrypt(self, data: dict[str, Any]) -> str:
        """Encrypt data and return base64 encoded token.

        Args:
            data: Dictionary to encrypt

        Returns:
            Base64 encoded encrypted token
        """
        try:
            # Convert to JSON
            json_data = json.dumps(data, separators=(",", ":")).encode("utf-8")

            # Generate random IV
            iv = os.urandom(16)

            # Pad data
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(json_data)
            padded_data += padder.finalize()

            # Encrypt
            cipher = Cipher(self.algorithm, modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

            # Create token structure
            token_data = {
                "iv": base64.b64encode(iv).decode("utf-8"),
                "value": base64.b64encode(encrypted_data).decode("utf-8"),
            }  # Encode token
            token_json = json.dumps(token_data, separators=(",", ":"))
            self.logger.debug("Token encrypted successfully")
            return base64.b64encode(token_json.encode()).decode("utf-8")
        except Exception as e:
            self.logger.error(f"Token encryption failed: {e}")
            raise TokenEncryptionError(f"Token encryption failed: {e}") from e

    def decrypt(self, token: str) -> dict[str, Any]:
        """Decrypt base64 encoded token and return data.

        Args:
            token: Base64 encoded encrypted token

        Returns:
            Decrypted data as dictionary
        """
        try:
            self.logger.debug("Starting token decryption")
            # Decode base64 token
            try:
                token_data = base64.b64decode(token)
                self.logger.debug(f"Base64 decoded token length: {len(token_data)}")
            except Exception as e:
                self.logger.error(f"Failed to base64 decode token: {e}")
                raise TokenDecryptionError(f"Invalid base64 encoding: {e}") from e

            # Parse token JSON
            try:
                token_json = json.loads(token_data.decode("utf-8"))
                self.logger.debug(f"Parsed token JSON: {token_json}")
            except Exception as e:
                self.logger.error(f"Failed to parse token JSON: {e}")
                raise TokenDecryptionError(f"Invalid token JSON: {e}") from e

            # Extract IV and encrypted data
            if "iv" not in token_json or "value" not in token_json:
                self.logger.error(
                    f"Missing required fields in token JSON: {token_json.keys()}"
                )
                raise TokenDecryptionError("Token missing required fields")

            try:
                iv = base64.b64decode(token_json["iv"])
                encrypted_data = base64.b64decode(token_json["value"])
                self.logger.debug(f"Encrypted data len: {len(encrypted_data)}")
            except Exception as e:
                self.logger.error(f"Failed to decode IV or encrypted data: {e}")
                raise TokenDecryptionError(f"Invalid IV or encrypted data: {e}") from e

            # Create cipher
            cipher = Cipher(self.algorithm, modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()

            # Decrypt data
            try:
                decrypted_padded = (
                    decryptor.update(encrypted_data) + decryptor.finalize()
                )
                self.logger.debug(
                    f"Decrypted padded data length: {len(decrypted_padded)}"
                )
            except Exception as e:
                self.logger.error(f"Decryption failed: {e}")
                raise TokenDecryptionError(f"Decryption failed: {e}") from e

            # Remove padding
            unpadder = padding.PKCS7(128).unpadder()
            try:
                decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
                self.logger.debug(f"Unpadded data length: {len(decrypted)}")
            except Exception as e:
                self.logger.error(f"Failed to remove padding: {e}")
                raise TokenDecryptionError(f"Invalid padding: {e}") from e

            # Parse JSON data
            try:
                data: dict[str, Any] = json.loads(decrypted.decode("utf-8"))
                self.logger.debug(f"Decrypted data: {json.dumps(data, indent=2)}")
                self.logger.debug("Token decrypted successfully")
                return data
            except Exception as e:
                self.logger.error(f"Failed to parse decrypted JSON: {e}")
                raise TokenDecryptionError(f"Invalid decrypted JSON: {e}") from e

        except TokenDecryptionError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during decryption: {e}")
            raise TokenDecryptionError(f"Decryption failed: {e}") from e

    @staticmethod
    def base64_decode(string: str, encoding: str = "utf-8") -> bytes:
        """Decode base64 string.

        Args:
            string: Base64 encoded string
            encoding: Character encoding

        Returns:
            Decoded bytes
        """
        return base64.b64decode(string)

    @staticmethod
    def base64_encode(data: bytes) -> str:
        """Encode bytes to base64 string.

        Args:
            data: Bytes to encode

        Returns:
            Base64 encoded string
        """
        return base64.b64encode(data).decode("utf-8")
