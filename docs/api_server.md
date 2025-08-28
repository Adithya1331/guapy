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

**Description:**
Initializes the FastAPI app, sets up configurable CORS middleware, and prepares WebSocket endpoints for Guacamole protocol connections.

---

See [../api.md](../api.md) for module index.
