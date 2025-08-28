# guapy.exceptions

Comprehensive exception hierarchy for structured error handling in Guapy.

## Base Exception

### GuapyError

Base exception class for all Guapy-related errors with structured error information.

**Constructor:**
```python
def __init__(
    self,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    cause: Optional[Exception] = None,
    **kwargs: Any,
) -> None:
```

**Attributes:**
- `message`: Human-readable error message
- `error_code`: Structured error code for programmatic handling
- `details`: Dictionary of additional error context
- `cause`: Original exception that caused this error

**Features:**
- Structured error information for better debugging
- Automatic error code assignment for each exception type
- Additional context through details dictionary
- String representation includes all error information

## Configuration Exceptions

### GuapyConfigurationError
Raised when configuration is invalid or missing.
- **Error Code**: `CONFIGURATION_ERROR`

## Connection Exceptions

### GuapyConnectionError
Base exception for connection-related errors.
- **Error Code**: `CONNECTION_ERROR`

### GuapyTimeoutError
Raised when an operation times out.
- **Error Code**: `TIMEOUT_ERROR`

### GuacdConnectionError
Raised when the initial connection to the guacd daemon fails.
- **Error Code**: `GUACD_CONNECTION_FAILED`

### WebSocketConnectionError
Raised for WebSocket-specific connection issues.
- **Error Code**: `WEBSOCKET_ERROR`

## Protocol Exceptions

### GuapyProtocolError
Base exception for Guacamole protocol errors.
- **Error Code**: `PROTOCOL_ERROR`

### ProtocolParsingError
Raised when a Guacamole protocol instruction is malformed.
- **Error Code**: `PROTOCOL_PARSE_ERROR`

### HandshakeError
Raised when the Guacamole protocol handshake fails due to an unexpected sequence.
- **Error Code**: `HANDSHAKE_FAILED`

## Authentication Exceptions

### GuapyAuthenticationError
Base for authentication or authorization failures.
- **Error Code**: `AUTHENTICATION_FAILED`

### GuapyCryptoError
Base for cryptographic operation failures.
- **Error Code**: `CRYPTO_ERROR`

### TokenDecryptionError
Raised when token decryption fails.
- **Error Code**: `TOKEN_DECRYPT_FAILED`

### TokenEncryptionError
Raised when token encryption fails.
- **Error Code**: `TOKEN_ENCRYPT_FAILED`

## Guacamole Status Code Exceptions

These exceptions correspond to specific Guacamole protocol status codes:

### Server Errors (0x02xx)
- **GuapyUnsupportedError** (0x0100): The requested operation is unsupported
- **GuapyServerError** (0x0200): Generic server error for internal failures
- **GuapyServerBusyError** (0x0201): The server is busy
- **GuapyUpstreamTimeoutError** (0x0202): The upstream server is not responding
- **GuapyUpstreamError** (0x0203): The upstream server returned an error
- **GuapyResourceNotFoundError** (0x0204): The requested resource does not exist
- **GuapyResourceConflictError** (0x0205): The requested resource is already in use
- **GuapyResourceClosedError** (0x0206): A resource or stream has been closed
- **GuapyUpstreamNotFoundError** (0x0207): The upstream host cannot be reached
- **GuapyUpstreamUnavailableError** (0x0208): The upstream is refusing connections
- **GuapySessionConflictError** (0x0209): The session conflicted with another session
- **GuapySessionTimeoutError** (0x020A): The session appeared to be inactive
- **GuapySessionClosedError** (0x020B): The session was forcibly terminated

### Client Errors (0x03xx)
- **GuapyClientBadRequestError** (0x0300): Bad parameters provided
- **GuapyUnauthorizedError** (0x0301): Permission was denied
- **GuapyForbiddenError** (0x0303): The operation is forbidden
- **GuapyClientTimeoutError** (0x0308): Client timed out or gave no response
- **GuapyClientOverrunError** (0x030D): Client sent excessive data
- **GuapyClientBadTypeError** (0x030F): Client sent unsupported data type
- **GuapyClientTooManyError** (0x031D): Client is using too many resources

## Usage Examples

### Basic Error Handling
```python
from guapy.exceptions import GuapyError, GuacdConnectionError

try:
    # Guapy operations
    pass
except GuacdConnectionError as e:
    print(f"Failed to connect to guacd: {e}")
    print(f"Error code: {e.error_code}")
    print(f"Details: {e.details}")
except GuapyError as e:
    print(f"Guapy error: {e}")
```

### Structured Error Information
```python
try:
    # Operation that might fail
    pass
except GuapyError as e:
    # Access structured error information
    error_info = {
        "message": e.message,
        "code": e.error_code,
        "details": e.details,
        "cause": str(e.cause) if e.cause else None
    }
    # Log or handle structured error
```

### Protocol Error Handling
```python
from guapy.exceptions import GuapyUnauthorizedError, GuapyProtocolError

try:
    # Protocol operations
    pass
except GuapyUnauthorizedError as e:
    # Handle authentication failure
    print(f"Authentication failed: {e}")
    # Check guacd status code
    status_code = e.details.get("guacd_status_code")
except GuapyProtocolError as e:
    # Handle other protocol errors
    print(f"Protocol error: {e}")
```

**Description:**
The exception hierarchy provides structured error handling with specific exception types for different failure modes. Each exception includes an error code, detailed context, and maintains the original cause for better debugging and error reporting.

---

See [../api.md](../api.md) for module index.