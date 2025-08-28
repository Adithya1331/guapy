# guapy.server

## GuapyServer
Main FastAPI-based WebSocket server for Guacamole connections.

**Constructor:**
```python
def __init__(
    self,
    client_options: ClientOptions,
    guacd_options: Optional[GuacdOptions] = None,
    process_connection_settings_callback: Optional[Callable] = None,
):
    """Initialize the Guapy server.
    Args:
        client_options: Client configuration options (including CORS settings)
        guacd_options: guacd connection options
        process_connection_settings_callback: Optional callback for processing connection settings
    """
```

**Attributes:**
- `app`: FastAPI application instance
- `client_options`: ClientOptions (includes CORS configuration)
- `guacd_options`: GuacdOptions
- `process_connection_settings_callback`: Optional callback

**CORS Security:**
The server now uses configurable CORS settings from `client_options` instead of hardcoded wildcard permissions. This provides:
- Secure defaults (localhost origins only)
- Production-ready configuration options
- Development-friendly utility methods

## create_server Function

**Function:**
```python
def create_server(
    client_options: ClientOptions,
    guacd_options: Optional[GuacdOptions] = None,
    process_connection_settings_callback: Optional[Callable] = None,
) -> GuapyServer:
    """Create a configured Guapy server instance.
    
    Args:
        client_options: Client configuration options (including CORS settings)
        guacd_options: guacd connection options (defaults to localhost:4822)
        process_connection_settings_callback: Optional callback for processing connection settings
        
    Returns:
        Configured GuapyServer instance ready to run
    """
```

**Description:**
Initializes the FastAPI app, sets up configurable CORS middleware, and prepares WebSocket endpoints for Guacamole protocol connections.

## WebSocket Endpoints

- **`/webSocket`**: Main WebSocket endpoint for Guacamole protocol connections
  - Requires `token` query parameter with encrypted connection details
  - Handles bidirectional communication between web clients and guacd daemon
  
## REST Endpoints

- **`/`**: Root endpoint returning basic server information
- **`/health`**: Health check endpoint for monitoring
- **`/stats`**: Server statistics and connection information

---

See [../api.md](../api.md) for module index.
