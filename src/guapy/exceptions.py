"""Custom exceptions for the Guapy package.

This module defines a comprehensive exception hierarchy for Guapy, providing
clear error handling and debugging capabilities for WebSocket proxy operations.
"""

from typing import Any, Optional


class GuapyError(Exception):
    """Base exception class for all Guapy-related errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        # Add any additional keyword arguments to details
        self.details.update(kwargs)
        self.cause = cause

    def __str__(self) -> str:
        error_str = self.message
        if self.error_code:
            error_str = f"[{self.error_code}] {error_str}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            error_str = f"{error_str} (details: {details_str})"
        return error_str


# Configuration Errors
class GuapyConfigurationError(GuapyError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "CONFIGURATION_ERROR")
        super().__init__(message, **kwargs)


# Connection Errors
class GuapyConnectionError(GuapyError):
    """Base exception for connection-related errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "CONNECTION_ERROR")
        super().__init__(message, **kwargs)


class GuapyTimeoutError(GuapyConnectionError):
    """Raised when an operation times out."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "TIMEOUT_ERROR")
        super().__init__(message, **kwargs)


class GuacdConnectionError(GuapyConnectionError):
    """Raised when the initial connection to the guacd daemon fails."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "GUACD_CONNECTION_FAILED")
        super().__init__(message, **kwargs)


class WebSocketConnectionError(GuapyConnectionError):
    """Raised for WebSocket-specific connection issues."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "WEBSOCKET_ERROR")
        super().__init__(message, **kwargs)


# Protocol Errors
class GuapyProtocolError(GuapyError):
    """Base exception for Guacamole protocol errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "PROTOCOL_ERROR")
        super().__init__(message, **kwargs)


class ProtocolParsingError(GuapyProtocolError):
    """Raised when a Guacamole protocol instruction is malformed."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "PROTOCOL_PARSE_ERROR")
        super().__init__(message, **kwargs)


class HandshakeError(GuapyProtocolError):
    """Raised when the Guacamole protocol handshake fails due to an unexpected sequence."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "HANDSHAKE_FAILED")
        super().__init__(message, **kwargs)


# Authentication and Security Errors
class GuapyAuthenticationError(GuapyError):
    """Base for authentication or authorization failures."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "AUTHENTICATION_FAILED")
        super().__init__(message, **kwargs)


class GuapyCryptoError(GuapyAuthenticationError):
    """Base for cryptographic operation failures."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "CRYPTO_ERROR")
        super().__init__(message, **kwargs)


class TokenDecryptionError(GuapyCryptoError):
    """Raised when token decryption fails."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "TOKEN_DECRYPT_FAILED")
        super().__init__(message, **kwargs)


class TokenEncryptionError(GuapyCryptoError):
    """Raised when token encryption fails."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "TOKEN_ENCRYPT_FAILED")
        super().__init__(message, **kwargs)


# Specific guacd Status Exceptions
class GuapyUnsupportedError(GuapyProtocolError):
    """The requested operation is unsupported (Status: 0x0100)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "UNSUPPORTED")
        super().__init__(message, **kwargs)


class GuapyServerBusyError(GuapyConnectionError):
    """The operation could not be performed as the server is busy (Status: 0x0201)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "SERVER_BUSY")
        super().__init__(message, **kwargs)


class GuapyUpstreamTimeoutError(GuapyConnectionError):
    """The upstream server is not responding (Status: 0x0202)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "UPSTREAM_TIMEOUT")
        super().__init__(message, **kwargs)


class GuapyUpstreamError(GuapyConnectionError):
    """The upstream server returned an error (Status: 0x0203)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "UPSTREAM_ERROR")
        super().__init__(message, **kwargs)


class GuapyResourceNotFoundError(GuapyProtocolError):
    """The requested resource does not exist (Status: 0x0204)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "RESOURCE_NOT_FOUND")
        super().__init__(message, **kwargs)


class GuapyResourceConflictError(GuapyProtocolError):
    """The requested resource is already in use (Status: 0x0205)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "RESOURCE_CONFLICT")
        super().__init__(message, **kwargs)


class GuapySessionConflictError(GuapyConnectionError):
    """The session conflicted with another session (Status: 0x0209)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "SESSION_CONFLICT")
        super().__init__(message, **kwargs)


class GuapySessionTimeoutError(GuapyConnectionError):
    """The session appeared to be inactive (Status: 0x020A)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "SESSION_TIMEOUT")
        super().__init__(message, **kwargs)


class GuapySessionClosedError(GuapyConnectionError):
    """The session was forcibly terminated (Status: 0x020B)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "SESSION_CLOSED")
        super().__init__(message, **kwargs)


class GuapyClientBadRequestError(GuapyProtocolError):
    """The operation could not be performed due to bad parameters (Status: 0x0300)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "CLIENT_BAD_REQUEST")
        super().__init__(message, **kwargs)


class GuapyUnauthorizedError(GuapyAuthenticationError):
    """Permission was denied to perform the operation (Status: 0x0301)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "CLIENT_UNAUTHORIZED")
        super().__init__(message, **kwargs)


class GuapyForbiddenError(GuapyAuthenticationError):
    """The operation is forbidden (Status: 0x0303)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "CLIENT_FORBIDDEN")
        super().__init__(message, **kwargs)


class GuapyClientTooManyError(GuapyProtocolError):
    """The client is already using too many resources (Status: 0x031D)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "CLIENT_TOO_MANY")
        super().__init__(message, **kwargs)


class GuapyServerError(GuapyConnectionError):
    """Generic server error for internal failures (Status: 0x0200)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "SERVER_ERROR")
        super().__init__(message, **kwargs)


class GuapyResourceClosedError(GuapyConnectionError):
    """A resource or stream has been closed (Status: 0x0206)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "RESOURCE_CLOSED")
        super().__init__(message, **kwargs)


class GuapyUpstreamNotFoundError(GuapyConnectionError):
    """The upstream host cannot be reached or resolved (Status: 0x0207)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "UPSTREAM_NOT_FOUND")
        super().__init__(message, **kwargs)


class GuapyUpstreamUnavailableError(GuapyConnectionError):
    """The upstream is refusing or unavailable to service connections (Status: 0x0208)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "UPSTREAM_UNAVAILABLE")
        super().__init__(message, **kwargs)


class GuapyClientTimeoutError(GuapyConnectionError):
    """Client timed out or gave no response (Status: 0x0308)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "CLIENT_TIMEOUT")
        super().__init__(message, **kwargs)


class GuapyClientOverrunError(GuapyProtocolError):
    """Client sent excessive data (Status: 0x030D)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "CLIENT_OVERRUN")
        super().__init__(message, **kwargs)


class GuapyClientBadTypeError(GuapyProtocolError):
    """Client sent unsupported or unexpected data type (Status: 0x030F)."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        kwargs.setdefault("error_code", "CLIENT_BAD_TYPE")
        super().__init__(message, **kwargs)
