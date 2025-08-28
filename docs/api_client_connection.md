# guapy.client_connection

## ClientConnection
Handles individual WebSocket client connections with proper state management.

**Constructor:**
```python
def __init__(
    self,
    websocket: WebSocket,
    connection_id: int,
    client_options: ClientOptions,
    guacd_options: GuacdOptions,
):
    """Initialize client connection.
    Args:
        websocket: FastAPI WebSocket connection
        connection_id: Unique connection identifier
        client_options: Client configuration options
        guacd_options: guacd connection options
    """
```

**Attributes:**
- `websocket`: FastAPI WebSocket
- `connection_id`: int
- `client_options`: ClientOptions
- `guacd_options`: GuacdOptions

**Description:**
Manages the WebSocket lifecycle, authentication, and state for each client. Handles message routing and error management.

---

See [../api.md](../api.md) for module index.
