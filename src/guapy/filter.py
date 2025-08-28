"""Provides a filter-based mechanism for processing Guacamole instructions.

This allows for a clean separation of concerns for tasks like error handling,
session recording, or analytics.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .exceptions import (
    GuapyClientBadRequestError,
    GuapyClientBadTypeError,
    GuapyClientOverrunError,
    GuapyClientTimeoutError,
    GuapyClientTooManyError,
    GuapyForbiddenError,
    GuapyProtocolError,
    GuapyResourceClosedError,
    GuapyResourceConflictError,
    GuapyResourceNotFoundError,
    GuapyServerBusyError,
    GuapyServerError,
    GuapySessionClosedError,
    GuapySessionConflictError,
    GuapySessionTimeoutError,
    GuapyUnauthorizedError,
    GuapyUnsupportedError,
    GuapyUpstreamError,
    GuapyUpstreamNotFoundError,
    GuapyUpstreamTimeoutError,
    GuapyUpstreamUnavailableError,
)

# It maps the numeric status codes from guacd to our specific exception classes.
# Based on Guacamole's canonical status enumeration used by guacd.
GUACD_ERROR_MAP = {
    # Note: 0x0000 SUCCESS is intentionally omitted - it should not raise an exception
    # Unsupported operations
    0x0100: GuapyUnsupportedError,
    # Server errors (0x02xx)
    0x0200: GuapyServerError,
    0x0201: GuapyServerBusyError,
    0x0202: GuapyUpstreamTimeoutError,
    0x0203: GuapyUpstreamError,
    0x0204: GuapyResourceNotFoundError,
    0x0205: GuapyResourceConflictError,
    0x0206: GuapyResourceClosedError,
    0x0207: GuapyUpstreamNotFoundError,
    0x0208: GuapyUpstreamUnavailableError,
    0x0209: GuapySessionConflictError,
    0x020A: GuapySessionTimeoutError,
    0x020B: GuapySessionClosedError,
    # Client errors (0x03xx)
    0x0300: GuapyClientBadRequestError,
    0x0301: GuapyUnauthorizedError,
    0x0303: GuapyForbiddenError,
    0x0308: GuapyClientTimeoutError,
    0x030D: GuapyClientOverrunError,
    0x030F: GuapyClientBadTypeError,
    0x031D: GuapyClientTooManyError,
}


class GuacamoleFilter(ABC):
    """An abstract base class for filtering Guacamole instructions,
    mirroring the GuacamoleFilter.java interface.
    """

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
        pass


class ErrorFilter(GuacamoleFilter):
    """A specific filter that checks for 'error' instructions from guacd
    and raises the appropriate specific exception based on the status code.
    """

    def filter(self, instruction: list[str]) -> Optional[list[str]]:
        """Checks for the 'error' opcode and raises a mapped exception.
        Lets all other instructions pass through untouched.

        Special handling:
        - 0x0000 SUCCESS: treated as non-error, passes through
        - Unknown status codes > 0x00FF: treated as errors (defensive handling)
        """
        if not instruction or instruction[0] != "error":
            return instruction  # Not an error, pass through

        error_msg = instruction[1] if len(instruction) > 1 else "Unknown guacd error"
        status_code = int(instruction[2]) if len(instruction) > 2 else 0

        # Handle SUCCESS status (0x0000) - should not raise an exception
        if status_code == 0x0000:
            return instruction  # SUCCESS status, pass through as non-error

        # Look up the specific exception from our map.
        # Fall back to a generic GuapyProtocolError if the code is unknown.
        # Defensive handling: treat any status code > 0x00FF as an error by default
        exception_class = GUACD_ERROR_MAP.get(status_code, GuapyProtocolError)

        # Raise the specific exception to terminate the connection
        raise exception_class(
            f"guacd error: {error_msg}", details={"guacd_status_code": status_code}
        )
