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

## Security Features

### CORS Configuration
Guapy now provides configurable CORS settings through `ClientOptions`:
- **Secure by default**: No wildcard origins in production
- **Environment-aware**: Easy development vs production configuration
- **Fully configurable**: All CORS settings can be customized

---

For detailed usage, see [Examples & Tutorials](examples.md).
