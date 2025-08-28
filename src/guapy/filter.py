"""
Provides a filter-based mechanism for processing Guacamole instructions. This allows for
a clean separation of concerns for tasks like error handling, session
recording, or analytics.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .exceptions import (
    GuapyProtocolError, GuapyUpstreamError, GuapyUnauthorizedError,
    GuapyServerBusyError, GuapySessionClosedError, GuapyUnsupportedError,
    GuapyResourceNotFoundError, GuapyResourceConflictError,
    GuapySessionConflictError, GuapySessionTimeoutError,
    GuapyClientBadRequestError, GuapyClientTooManyError,
    GuapyUpstreamTimeoutError
)

# It maps the numeric status codes from guacd to our specific exception classes.
GUACD_ERROR_MAP = {
    0x0100: GuapyUnsupportedError,
    0x0201: GuapyServerBusyError,
    0x0202: GuapyUpstreamTimeoutError,
    0x0203: GuapyUpstreamError,
    0x0204: GuapyResourceNotFoundError,
    0x0205: GuapyResourceConflictError,
    0x0209: GuapySessionConflictError,
    0x020A: GuapySessionTimeoutError,
    0x020B: GuapySessionClosedError,
    0x0300: GuapyClientBadRequestError,
    0x0301: GuapyUnauthorizedError,
    0x0303: GuapyUnauthorizedError, # Also maps to Unauthorized
    0x031D: GuapyClientTooManyError,
}


class GuacamoleFilter(ABC):
    """
    An abstract base class for filtering Guacamole instructions,
    mirroring the GuacamoleFilter.java interface.
    """

    @abstractmethod
    def filter(self, instruction: List[str]) -> Optional[List[str]]:
        """
        Applies a filter to the given instruction.

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
    """
    A specific filter that checks for 'error' instructions from guacd
    and raises the appropriate specific exception based on the status code.
    """
    def filter(self, instruction: List[str]) -> Optional[List[str]]:
        """
        Checks for the 'error' opcode and raises a mapped exception.
        Lets all other instructions pass through untouched.
        """
        if not instruction or instruction[0] != "error":
            return instruction  # Not an error, pass through

        error_msg = instruction[1] if len(instruction) > 1 else "Unknown guacd error"
        status_code = int(instruction[2]) if len(instruction) > 2 else 0

        # Look up the specific exception from our map.
        # Fall back to a generic GuapyProtocolError if the code is unknown.
        ExceptionClass = GUACD_ERROR_MAP.get(status_code, GuapyProtocolError)

        # Raise the specific exception to terminate the connection
        raise ExceptionClass(
            f"guacd error: {error_msg}",
            details={"guacd_status_code": status_code}
        )