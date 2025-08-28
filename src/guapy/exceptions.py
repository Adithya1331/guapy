"""Custom exceptions for the Guapy package.

This module defines a comprehensive exception hierarchy for Guapy, providing
clear error handling and debugging capabilities for WebSocket proxy operations.
"""

from typing import Any, Optional


class GuapyError(Exception):
    """Base exception class for all Guapy-related errors.

    This is the root exception that all other Guapy exceptions inherit from.
    It provides common functionality for error handling and debugging.

    Args:
        message: Human-readable error description
        error_code: Optional error code for programmatic handling
        details: Optional dictionary containing additional error context
        cause: Optional underlying exception that caused this error
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize the GuapyError with comprehensive error information."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause

    def __str__(self) -> str:
        """Return a comprehensive string representation of the error."""
        error_str = self.message
        if self.error_code:
            error_str = f"[{self.error_code}] {error_str}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            error_str = f"{error_str} (details: {details_str})"
        return error_str

    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r}, "
            f"cause={self.cause!r})"
        )


class GuapyCryptoError(GuapyError):
    """Base exception for cryptographic operations.

    Raised when encryption, decryption, or token processing fails.
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        token_info: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with crypto-specific context."""
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation
        if token_info:
            details.update(token_info)
        super().__init__(message, details=details, **kwargs)


class TokenDecryptionError(GuapyCryptoError):
    """Raised when token decryption fails.

    This can occur due to:
    - Invalid base64 encoding
    - Incorrect encryption key
    - Corrupted token data
    - Unsupported cipher algorithm
    """

    def __init__(
        self,
        message: str,
        token_length: Optional[int] = None,
        cipher_info: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with token-specific information."""
        details = kwargs.pop("details", {})
        if token_length is not None:
            details["token_length"] = token_length
        if cipher_info:
            details["cipher"] = cipher_info
        super().__init__(
            message,
            operation="decrypt",
            error_code="TOKEN_DECRYPT_FAILED",
            details=details,
            **kwargs,
        )


class TokenEncryptionError(GuapyCryptoError):
    """Raised when token encryption fails.

    This can occur due to:
    - Invalid data format
    - Encryption key issues
    - Cipher initialization problems
    """

    def __init__(
        self, message: str, data_size: Optional[int] = None, **kwargs: Any
    ) -> None:
        """Initialize with encryption-specific information."""
        details = kwargs.pop("details", {})
        if data_size is not None:
            details["data_size"] = data_size
        super().__init__(
            message,
            operation="encrypt",
            error_code="TOKEN_ENCRYPT_FAILED",
            details=details,
            **kwargs,
        )


class GuapyConnectionError(GuapyError):
    """Base exception for connection-related errors.

    Covers WebSocket connections, guacd connections, and network issues.
    """

    def __init__(
        self,
        message: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        connection_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with connection-specific context."""
        details = kwargs.pop("details", {})
        if host:
            details["host"] = host
        if port is not None:
            details["port"] = port
        if connection_id:
            details["connection_id"] = connection_id
        super().__init__(message, details=details, **kwargs)


class GuacdConnectionError(GuapyConnectionError):
    """Raised when connection to guacd daemon fails.

    This can occur due to:
    - guacd daemon not running
    - Network connectivity issues
    - Firewall blocking connection
    - Incorrect host/port configuration
    """

    def __init__(
        self,
        message: str,
        guacd_host: Optional[str] = None,
        guacd_port: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with guacd-specific information."""
        super().__init__(
            message,
            host=guacd_host,
            port=guacd_port,
            error_code="GUACD_CONNECTION_FAILED",
            **kwargs,
        )


class WebSocketConnectionError(GuapyConnectionError):
    """Raised when WebSocket connection issues occur.

    This can occur due to:
    - Client disconnection
    - Protocol violations
    - Message transmission failures
    """

    def __init__(
        self,
        message: str,
        websocket_state: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with WebSocket-specific information."""
        details = kwargs.pop("details", {})
        if websocket_state:
            details["websocket_state"] = websocket_state
        super().__init__(
            message,
            error_code="WEBSOCKET_CONNECTION_ERROR",
            details=details,
            **kwargs,
        )


class GuapyConfigurationError(GuapyError):
    """Raised when configuration is invalid or missing.

    This can occur due to:
    - Missing required configuration values
    - Invalid configuration format
    - Conflicting configuration options
    - Environment setup issues
    """

    def __init__(
        self,
        message: str,
        config_section: Optional[str] = None,
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_value: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with configuration-specific context."""
        details = kwargs.pop("details", {})
        if config_section:
            details["config_section"] = config_section
        if config_key:
            details["config_key"] = config_key
        if expected_type:
            details["expected_type"] = expected_type
        if actual_value is not None:
            details["actual_value"] = str(actual_value)
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            **kwargs,
        )


class GuapyProtocolError(GuapyError):
    """Base exception for Guacamole protocol-related errors.

    Covers protocol parsing, instruction formatting, and communication issues.
    """

    def __init__(
        self,
        message: str,
        instruction: Optional[str] = None,
        protocol_state: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with protocol-specific context."""
        details = kwargs.pop("details", {})
        if instruction:
            details["instruction"] = instruction
        if protocol_state:
            details["protocol_state"] = protocol_state
        super().__init__(message, details=details, **kwargs)


class ProtocolParsingError(GuapyProtocolError):
    """Raised when Guacamole protocol parsing fails.

    This can occur due to:
    - Malformed instructions
    - Invalid instruction format
    - Unexpected protocol sequences
    """

    def __init__(
        self,
        message: str,
        raw_data: Optional[str] = None,
        expected_format: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with parsing-specific information."""
        details = kwargs.pop("details", {})
        if raw_data:
            details["raw_data"] = raw_data[:100]  # Truncate for safety
        if expected_format:
            details["expected_format"] = expected_format
        super().__init__(
            message,
            error_code="PROTOCOL_PARSE_ERROR",
            details=details,
            **kwargs,
        )


class HandshakeError(GuapyProtocolError):
    """Raised when Guacamole protocol handshake fails.

    This can occur during:
    - Initial protocol negotiation
    - Parameter exchange
    - Connection establishment
    """

    def __init__(
        self,
        message: str,
        handshake_phase: Optional[str] = None,
        expected_instruction: Optional[str] = None,
        received_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with handshake-specific information."""
        details = kwargs.pop("details", {})
        if handshake_phase:
            details["handshake_phase"] = handshake_phase
        if expected_instruction:
            details["expected_instruction"] = expected_instruction
        if received_instruction:
            details["received_instruction"] = received_instruction
        super().__init__(
            message,
            error_code="HANDSHAKE_FAILED",
            details=details,
            **kwargs,
        )


class GuapyAuthenticationError(GuapyError):
    """Raised when authentication or authorization fails.

    This can occur due to:
    - Invalid credentials
    - Expired tokens
    - Insufficient permissions
    - Authentication service unavailable
    """

    def __init__(
        self,
        message: str,
        auth_method: Optional[str] = None,
        user_info: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with authentication-specific context."""
        details = kwargs.pop("details", {})
        if auth_method:
            details["auth_method"] = auth_method
        if user_info:  # Only include non-sensitive user information
            safe_user_info = {
                k: v
                for k, v in user_info.items()
                if k not in ["password", "token", "secret"]
            }
            details["user_info"] = safe_user_info
        super().__init__(
            message,
            error_code="AUTHENTICATION_FAILED",
            details=details,
            **kwargs,
        )





class GuapyTimeoutError(GuapyError):
    """Raised when operations exceed timeout limits.

    This can occur during:
    - Connection establishment
    - Message transmission
    - Protocol handshakes
    - Long-running operations
    """

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with timeout-specific information."""
        details = kwargs.pop("details", {})
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        super().__init__(
            message,
            error_code="OPERATION_TIMEOUT",
            details=details,
            **kwargs,
        )
