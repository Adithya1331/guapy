"""Tests for guapy.exceptions module.

This module tests the custom exception hierarchy and error handling.
"""

from guapy.exceptions import (
    GuapyAuthenticationError,
    GuapyConfigurationError,
    GuapyConnectionError,
    GuapyCryptoError,
    GuapyError,
    GuapyProtocolError,
    GuapyTimeoutError,
    HandshakeError,
    ProtocolParsingError,
    TokenDecryptionError,
    TokenEncryptionError,
    WebSocketConnectionError,
)


class TestGuapyErrorBase:
    """Test the base GuapyError exception class."""

    def test_basic_error_creation(self):
        """Test basic error creation with message only."""
        error = GuapyError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code is None
        assert error.details == {}
        assert error.cause is None

    def test_error_with_error_code(self):
        """Test error creation with error code."""
        error = GuapyError("Test error", error_code="TEST001")
        assert str(error) == "[TEST001] Test error"
        assert error.error_code == "TEST001"
        assert error.message == "Test error"

    def test_error_with_details(self):
        """Test error creation with details dictionary."""
        details = {"field": "value", "count": 42}
        error = GuapyError("Test error", details=details)

        error_str = str(error)
        assert "Test error" in error_str
        assert "details:" in error_str
        assert "field=value" in error_str
        assert "count=42" in error_str
        assert error.details == details

    def test_error_with_cause(self):
        """Test error creation with underlying cause."""
        cause = ValueError("Original error")
        error = GuapyError("Wrapper error", cause=cause)

        assert error.cause == cause
        assert error.message == "Wrapper error"

    def test_error_with_all_parameters(self):
        """Test error creation with all parameters."""
        cause = ValueError("Original error")
        details = {"key": "value"}
        error = GuapyError(
            "Test error", error_code="TEST001", details=details, cause=cause
        )

        assert error.message == "Test error"
        assert error.error_code == "TEST001"
        assert error.details == details
        assert error.cause == cause

        error_str = str(error)
        assert "[TEST001]" in error_str
        assert "Test error" in error_str
        assert "details:" in error_str

    def test_error_inheritance(self):
        """Test that GuapyError inherits from Exception."""
        error = GuapyError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, GuapyError)

    def test_error_repr(self):
        """Test error representation."""
        error = GuapyError("Test error", error_code="TEST001")
        repr_str = repr(error)
        assert "GuapyError" in repr_str

    def test_empty_details_handling(self):
        """Test handling of empty details."""
        error = GuapyError("Test error", details={})
        error_str = str(error)
        assert "details:" not in error_str  # Empty details should not appear

    def test_none_details_handling(self):
        """Test handling of None details."""
        error = GuapyError("Test error", details=None)
        assert error.details == {}
        error_str = str(error)
        assert "details:" not in error_str


class TestSpecificExceptions:
    """Test specific exception classes."""

    def test_crypto_exceptions(self):
        """Test crypto-related exceptions."""
        # Test GuapyCryptoError
        crypto_error = GuapyCryptoError("Crypto operation failed")
        assert isinstance(crypto_error, GuapyError)
        assert isinstance(crypto_error, GuapyCryptoError)

        # Test TokenEncryptionError
        encrypt_error = TokenEncryptionError("Encryption failed")
        assert isinstance(encrypt_error, GuapyCryptoError)
        assert isinstance(encrypt_error, TokenEncryptionError)

        # Test TokenDecryptionError
        decrypt_error = TokenDecryptionError("Decryption failed")
        assert isinstance(decrypt_error, GuapyCryptoError)
        assert isinstance(decrypt_error, TokenDecryptionError)

    def test_connection_exceptions(self):
        """Test connection-related exceptions."""
        # Test GuapyConnectionError
        conn_error = GuapyConnectionError("Connection failed")
        assert isinstance(conn_error, GuapyError)
        assert isinstance(conn_error, GuapyConnectionError)

        # Test WebSocketConnectionError
        ws_error = WebSocketConnectionError("WebSocket error")
        assert isinstance(ws_error, GuapyConnectionError)
        assert isinstance(ws_error, WebSocketConnectionError)

    def test_protocol_exceptions(self):
        """Test protocol-related exceptions."""
        # Test GuapyProtocolError
        protocol_error = GuapyProtocolError("Protocol error")
        assert isinstance(protocol_error, GuapyError)
        assert isinstance(protocol_error, GuapyProtocolError)

        # Test HandshakeError
        handshake_error = HandshakeError("Handshake failed")
        assert isinstance(handshake_error, GuapyProtocolError)
        assert isinstance(handshake_error, HandshakeError)

        # Test ProtocolParsingError
        parsing_error = ProtocolParsingError("Parsing failed")
        assert isinstance(parsing_error, GuapyProtocolError)
        assert isinstance(parsing_error, ProtocolParsingError)

    def test_configuration_exceptions(self):
        """Test configuration-related exceptions."""
        config_error = GuapyConfigurationError("Config error")
        assert isinstance(config_error, GuapyError)
        assert isinstance(config_error, GuapyConfigurationError)

    def test_authentication_exceptions(self):
        """Test authentication-related exceptions."""
        auth_error = GuapyAuthenticationError("Auth failed")
        assert isinstance(auth_error, GuapyError)
        assert isinstance(auth_error, GuapyAuthenticationError)

    def test_timeout_exceptions(self):
        """Test timeout-related exceptions."""
        timeout_error = GuapyTimeoutError("Operation timed out")
        assert isinstance(timeout_error, GuapyError)
        assert isinstance(timeout_error, GuapyTimeoutError)


class TestConfigurationError:
    """Test GuapyConfigurationError specific functionality."""

    def test_configuration_error_basic(self):
        """Test basic configuration error."""
        error = GuapyConfigurationError("Invalid configuration")
        assert error.message == "Invalid configuration"

    def test_configuration_error_with_section(self):
        """Test configuration error with section information."""
        error = GuapyConfigurationError(
            "Invalid value",
            config_section="database",
            config_key="host",
            expected_type="string",
            actual_value="None",
        )

        assert error.details["config_section"] == "database"
        assert error.details["config_key"] == "host"
        assert error.details["expected_type"] == "string"
        assert error.details["actual_value"] == "None"

    def test_configuration_error_inheritance(self):
        """Test that GuapyConfigurationError properly inherits."""
        error = GuapyConfigurationError("Config error")
        assert isinstance(error, GuapyError)
        assert isinstance(error, GuapyConfigurationError)


class TestConnectionError:
    """Test GuapyConnectionError specific functionality."""

    def test_connection_error_basic(self):
        """Test basic connection error."""
        error = GuapyConnectionError("Connection failed")
        assert error.message == "Connection failed"

    def test_connection_error_with_details(self):
        """Test connection error with connection details."""
        error = GuapyConnectionError("Connection refused", host="127.0.0.1", port=4822)

        assert error.details["host"] == "127.0.0.1"
        assert error.details["port"] == 4822

    def test_websocket_connection_error(self):
        """Test WebSocket specific connection error."""
        error = WebSocketConnectionError(
            "WebSocket handshake failed",
            websocket_state="closed",
        )

        assert error.details["websocket_state"] == "closed"
        assert isinstance(error, GuapyConnectionError)


class TestProtocolError:
    """Test GuapyProtocolError specific functionality."""

    def test_protocol_error_basic(self):
        """Test basic protocol error."""
        error = GuapyProtocolError("Protocol violation")
        assert error.message == "Protocol violation"

    def test_handshake_error(self):
        """Test handshake specific error."""
        error = HandshakeError(
            "Handshake failed",
            handshake_phase="authentication",
            expected_instruction="ready",
            received_instruction="error",
        )

        assert error.details["handshake_phase"] == "authentication"
        assert error.details["expected_instruction"] == "ready"
        assert error.details["received_instruction"] == "error"
        assert isinstance(error, GuapyProtocolError)

    def test_protocol_parsing_error(self):
        """Test protocol parsing specific error."""
        error = ProtocolParsingError(
            "Invalid instruction format",
            raw_data="malformed;data",
            expected_format="instruction;params",
        )

        assert error.details["raw_data"] == "malformed;data"
        assert error.details["expected_format"] == "instruction;params"
        assert isinstance(error, GuapyProtocolError)


class TestCryptoError:
    """Test GuapyCryptoError specific functionality."""

    def test_crypto_error_basic(self):
        """Test basic crypto error."""
        error = GuapyCryptoError("Cryptographic operation failed")
        assert error.message == "Cryptographic operation failed"

    def test_token_encryption_error(self):
        """Test token encryption specific error."""
        error = TokenEncryptionError("Failed to encrypt token", data_size=32)

        assert error.details["data_size"] == 32
        assert isinstance(error, GuapyCryptoError)

    def test_token_decryption_error(self):
        """Test token decryption specific error."""
        error = TokenDecryptionError(
            "Failed to decrypt token", token_length=128, cipher_info="AES-256-CBC"
        )

        assert error.details["token_length"] == 128
        assert error.details["cipher_info"] == "AES-256-CBC"
        assert isinstance(error, GuapyCryptoError)


class TestExceptionHierarchy:
    """Test the exception hierarchy and inheritance."""

    def test_inheritance_chain(self):
        """Test that the inheritance chain is correct."""
        # Test crypto hierarchy
        assert issubclass(TokenEncryptionError, GuapyCryptoError)
        assert issubclass(TokenDecryptionError, GuapyCryptoError)
        assert issubclass(GuapyCryptoError, GuapyError)

        # Test connection hierarchy
        assert issubclass(WebSocketConnectionError, GuapyConnectionError)
        assert issubclass(GuapyConnectionError, GuapyError)

        # Test protocol hierarchy
        assert issubclass(HandshakeError, GuapyProtocolError)
        assert issubclass(ProtocolParsingError, GuapyProtocolError)
        assert issubclass(GuapyProtocolError, GuapyError)

        # Test other exceptions
        assert issubclass(GuapyConfigurationError, GuapyError)
        assert issubclass(GuapyAuthenticationError, GuapyError)
        assert issubclass(GuapyTimeoutError, GuapyError)

    def test_all_exceptions_inherit_from_base(self):
        """Test that all exceptions inherit from GuapyError."""
        exceptions = [
            GuapyConfigurationError,
            GuapyConnectionError,
            GuapyCryptoError,
            GuapyProtocolError,
            GuapyAuthenticationError,
            GuapyTimeoutError,
            WebSocketConnectionError,
            HandshakeError,
            ProtocolParsingError,
            TokenEncryptionError,
            TokenDecryptionError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, GuapyError)
            assert issubclass(exc_class, Exception)

    def test_exception_catching(self):
        """Test that exceptions can be caught properly."""
        # Test catching specific exception
        try:
            raise TokenEncryptionError("Test error")
        except TokenEncryptionError as e:
            assert isinstance(e, TokenEncryptionError)

        # Test catching parent exception
        try:
            raise TokenEncryptionError("Test error")
        except GuapyCryptoError as e:
            assert isinstance(e, TokenEncryptionError)

        # Test catching base exception
        try:
            raise TokenEncryptionError("Test error")
        except GuapyError as e:
            assert isinstance(e, TokenEncryptionError)


class TestExceptionUsage:
    """Test practical exception usage scenarios."""

    def test_exception_chaining(self):
        """Test exception chaining with cause."""
        original = ValueError("Original error")

        try:
            raise original
        except ValueError as e:
            wrapped = GuapyError("Wrapped error", cause=e)
            assert wrapped.cause == original

    def test_exception_details_formatting(self):
        """Test that exception details are formatted correctly."""
        details = {
            "hostname": "test.example.com",
            "port": 3389,
            "protocol": "RDP",
            "timeout": 30.5,
        }

        error = GuapyConnectionError(
            "Connection failed", error_code="CONN001", details=details
        )

        error_str = str(error)
        assert "[CONN001]" in error_str
        assert "Connection failed" in error_str
        assert "hostname=test.example.com" in error_str
        assert "port=3389" in error_str

    def test_exception_without_optional_params(self):
        """Test exceptions work without optional parameters."""
        # Test that all exceptions can be created with just a message
        # Some exceptions have default error codes, so we test the message
        # attribute directly
        exceptions = [
            GuapyError,
            GuapyConfigurationError,
            GuapyConnectionError,
            GuapyCryptoError,
            GuapyProtocolError,
            GuapyAuthenticationError,
            GuapyTimeoutError,
            WebSocketConnectionError,
            HandshakeError,
            ProtocolParsingError,
            TokenEncryptionError,
            TokenDecryptionError,
        ]

        for exc_class in exceptions:
            error = exc_class("Test message")
            assert error.message == "Test message"
            # Check that Test message appears in str representation
            assert "Test message" in str(error)

    def test_exception_with_unicode_message(self):
        """Test exceptions with unicode messages."""
        error = GuapyError("错误信息: 连接失败")
        assert "错误信息: 连接失败" in str(error)
        assert error.message == "错误信息: 连接失败"

    def test_exception_with_empty_message(self):
        """Test exceptions with empty messages."""
        error = GuapyError("")
        assert str(error) == ""
        assert error.message == ""

    def test_exception_pickling(self):
        """Test that exceptions can be pickled and unpickled."""
        import pickle

        error = GuapyError("Test error", error_code="TEST001", details={"key": "value"})

        # Pickle and unpickle (safe for testing with known data)
        pickled = pickle.dumps(error)
        unpickled = pickle.loads(pickled)  # noqa: S301 # Safe for tests

        assert unpickled.message == error.message
        assert unpickled.error_code == error.error_code
        assert unpickled.details == error.details

    def test_exception_equality(self):
        """Test exception equality comparison."""
        error1 = GuapyError("Test", error_code="001", details={"a": 1})
        error2 = GuapyError("Test", error_code="001", details={"a": 1})
        error3 = GuapyError("Different", error_code="001", details={"a": 1})

        # Note: Exception equality is by identity, not content
        assert error1 != error2  # Different instances
        assert error1 != error3  # Different content


class TestExceptionDocumentation:
    """Test that exceptions have proper documentation."""

    def test_base_exception_docstring(self):
        """Test that GuapyError has proper docstring."""
        assert GuapyError.__doc__ is not None
        assert len(GuapyError.__doc__.strip()) > 0
        assert "Base exception" in GuapyError.__doc__

    def test_specific_exceptions_have_docstrings(self):
        """Test that specific exceptions have docstrings."""
        exceptions = [
            GuapyConfigurationError,
            GuapyConnectionError,
            GuapyCryptoError,
            GuapyProtocolError,
            TokenEncryptionError,
            TokenDecryptionError,
        ]

        for exc_class in exceptions:
            assert exc_class.__doc__ is not None
            assert len(exc_class.__doc__.strip()) > 0
