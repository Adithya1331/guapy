# guapy.filter

Filter system for processing Guacamole protocol instructions.

## GuacamoleFilter (Abstract Base Class)

Abstract base class for filtering Guacamole instructions, mirroring the GuacamoleFilter.java interface.

**Method:**
```python
@abstractmethod
def filter(self, instruction: list[str]) -> Optional[list[str]]:
    """Applies a filter to the given instruction.

    Args:
        instruction: The parsed instruction as a list of strings.

    Returns:
        - The original or a modified instruction if it's allowed to pass.
        - `None` if the instruction should be silently dropped.

    Raises:
        GuapyError: If the instruction should be denied and the
                    connection terminated. The specific exception raised
                    determines the nature of the error.
    """
```

## ErrorFilter

A specific filter that checks for 'error' instructions from guacd and raises the appropriate specific exception based on the status code.

**Features:**
- **Automatic Error Handling**: Converts guacd error instructions into Python exceptions
- **Status Code Mapping**: Maps Guacamole status codes to specific exception types
- **Success Handling**: Treats 0x0000 SUCCESS status as non-error, passes through
- **Defensive Handling**: Unknown status codes > 0x00FF are treated as errors

**Status Code Mappings:**
- `0x0100`: `GuapyUnsupportedError` - Unsupported operation
- `0x0200`: `GuapyServerError` - Generic server error
- `0x0201`: `GuapyServerBusyError` - Server is busy
- `0x0202`: `GuapyUpstreamTimeoutError` - Upstream server timeout
- `0x0203`: `GuapyUpstreamError` - Upstream server error
- `0x0204`: `GuapyResourceNotFoundError` - Resource not found
- `0x0205`: `GuapyResourceConflictError` - Resource conflict
- `0x0206`: `GuapyResourceClosedError` - Resource closed
- `0x0207`: `GuapyUpstreamNotFoundError` - Upstream not found
- `0x0208`: `GuapyUpstreamUnavailableError` - Upstream unavailable
- `0x0209`: `GuapySessionConflictError` - Session conflict
- `0x020A`: `GuapySessionTimeoutError` - Session timeout
- `0x020B`: `GuapySessionClosedError` - Session closed
- `0x0300`: `GuapyClientBadRequestError` - Bad request
- `0x0301`: `GuapyUnauthorizedError` - Unauthorized
- `0x0303`: `GuapyForbiddenError` - Forbidden
- `0x0308`: `GuapyClientTimeoutError` - Client timeout
- `0x030D`: `GuapyClientOverrunError` - Client overrun
- `0x030F`: `GuapyClientBadTypeError` - Client bad type
- `0x031D`: `GuapyClientTooManyError` - Too many resources

## Custom Filters

You can create custom filters by extending `GuacamoleFilter`:

```python
from guapy.filter import GuacamoleFilter
from typing import Optional

class LoggingFilter(GuacamoleFilter):
    """Example filter that logs all instructions."""
    
    def filter(self, instruction: list[str]) -> Optional[list[str]]:
        print(f"Instruction: {instruction}")
        return instruction  # Pass through unchanged

class BlockingFilter(GuacamoleFilter):
    """Example filter that blocks specific instructions."""
    
    def filter(self, instruction: list[str]) -> Optional[list[str]]:
        if instruction and instruction[0] == "clipboard":
            return None  # Block clipboard instructions
        return instruction
```

**Description:**
The filter system provides a clean way to process, modify, or block Guacamole protocol instructions. Filters are applied in sequence and can transform instructions, drop them silently, or raise exceptions to terminate connections.

---

See [../api.md](../api.md) for module index.