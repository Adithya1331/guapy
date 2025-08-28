# guapy.models

Pydantic models for configuration and data validation.

## Main Models

### Core Configuration Models
- `ConnectionType`: Enum of supported connection types (RDP, VNC, SSH, TELNET)
- `ScreenSize`: Screen size configuration (width, height, dpi)
- `CryptConfig`: Encryption configuration (cypher, key)
- `ClientOptions`: Client configuration including CORS settings (see CORS Configuration below)
- `GuacdOptions`: Configuration for guacd daemon connection (host, port)
- `ServerConfig`: Server configuration (host, port, secret_key, max_connections, etc.)

### Connection Models
- `ConnectionConfig`: Complete connection configuration with protocol and settings
- `TokenData`: Structured data for connection tokens
- `ConnectionSettings`: Base class for connection-specific settings with dynamic attributes

### Settings Classes
Connection-specific settings that extend `ConnectionSettings`:
- RDP settings: hostname, port, username, password, domain, security, drive options
- SSH settings: hostname, port, username, password, font configuration
- VNC settings: hostname, port, username, password
- Telnet settings: hostname, port, username, password

## CORS Configuration

### ClientOptions CORS Fields
- `cors_allow_origins`: List of allowed origins for CORS requests. Defaults to localhost addresses for security.
- `cors_allow_credentials`: Whether to allow credentials in CORS requests (default: True)
- `cors_allow_methods`: List of allowed HTTP methods (default: common REST methods)
- `cors_allow_headers`: List of allowed headers (default: ["*"])

### Utility Methods
- `ClientOptions.create_with_development_cors(crypt, **kwargs)`: Creates permissive CORS config for development (WARNING: allows all origins)
- `ClientOptions.create_with_production_cors(crypt, allowed_origins, **kwargs)`: Creates secure CORS config for production

**Description:**
All configuration and data structures in Guapy are defined as Pydantic models for type safety and validation. CORS settings are now configurable for enhanced security.

---

See [../api.md](../api.md) for module index.
