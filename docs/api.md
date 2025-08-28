# API Reference

This section documents the public APIs of Guapy.

## Modules

### `guapy.server`
Main WebSocket server for handling Guacamole connections.
- `GuapyServer`: Main FastAPI-based server class. Handles initialization, configurable CORS security, and WebSocket endpoints.

### `guapy.client_connection`
Handles individual WebSocket client connections with proper state management.
- `ClientConnection`: Manages WebSocket lifecycle, authentication, and state.

### `guapy.guacd_client`
Guacamole protocol handling and guacd client implementation.
- `GuacamoleProtocol`: Static methods for formatting/parsing Guacamole protocol instructions.
- `GuacdClient`: Manages the TCP connection to the `guacd` daemon, including the protocol handshake and message relay.

### `guapy.crypto`
Cryptographic functions for token encryption and decryption.
- `GuacamoleCrypto`: Handles encryption/decryption of connection tokens (e.g., AES-256-CBC).

### `guapy.config`
Configuration management for guapy server.
- `ConfigManager`: Loads config from file, env, and CLI. Provides unified config access.

### `guapy.models`
Pydantic models for configuration and data validation.
- `ConnectionType`, `ScreenSize`, `CryptConfig`, etc.: Typed models for all config/data structures.
- `ClientOptions`: Now includes configurable CORS security settings for production-ready deployments.

### `guapy.filter`
Filter system for processing Guacamole protocol instructions.
- `GuacamoleFilter`: Abstract base class for creating custom instruction filters.
- `ErrorFilter`: Built-in filter that handles error instructions and raises appropriate exceptions.

### `guapy.exceptions`
Comprehensive exception hierarchy for error handling.
- `GuapyError`: Base exception class with structured error information.
- Protocol-specific exceptions: `GuapyProtocolError`, `HandshakeError`, `ProtocolParsingError`.
- Connection exceptions: `GuacdConnectionError`, `WebSocketConnectionError`, `GuapyTimeoutError`.
- Authentication exceptions: `GuapyAuthenticationError`, `TokenDecryptionError`, `TokenEncryptionError`.
- Guacamole status code exceptions: Maps guacd error codes to specific Python exceptions.

### `guapy.cli`
Command-line interface for running and configuring Guapy.
- `run`: Start the Guapy server with configurable options.
- `show_config`: Display the current server configuration.

See [guapy.cli](api_cli.md) for detailed CLI documentation.

### `guapy.filter`
Filter system for processing Guacamole protocol instructions.
- `GuacamoleFilter`: Abstract base class for creating custom instruction filters.
- `ErrorFilter`: Built-in filter that handles error instructions and raises appropriate exceptions.

See [guapy.filter](api_filter.md) for detailed filter documentation.

### `guapy.exceptions`
Comprehensive exception hierarchy for error handling.
- `GuapyError`: Base exception class with structured error information.
- Protocol-specific exceptions: `GuapyProtocolError`, `HandshakeError`, `ProtocolParsingError`.
- Connection exceptions: `GuacdConnectionError`, `WebSocketConnectionError`, `GuapyTimeoutError`.
- Authentication exceptions: `GuapyAuthenticationError`, `TokenDecryptionError`, `TokenEncryptionError`.
- Guacamole status code exceptions: Maps guacd error codes to specific Python exceptions.

See [guapy.exceptions](api_exceptions.md) for detailed exception documentation.

## Security Features

### CORS Configuration
Guapy now provides configurable CORS settings through `ClientOptions`:
- **Secure by default**: No wildcard origins in production
- **Environment-aware**: Easy development vs production configuration
- **Fully configurable**: All CORS settings can be customized

---

For detailed usage, see [Examples & Tutorials](examples.md).
