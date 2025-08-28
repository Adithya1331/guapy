"""Tests for filter.py."""

import pytest

from guapy.exceptions import (
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
from guapy.filter import GUACD_ERROR_MAP, ErrorFilter, GuacamoleFilter


class TestGuacamoleFilter:
    """Test suite for GuacamoleFilter abstract base class."""

    def test_filter_is_abstract(self):
        """Test that GuacamoleFilter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            GuacamoleFilter()


class TestErrorFilter:
    """Test suite for ErrorFilter class."""

    @pytest.fixture
    def error_filter(self):
        """Create ErrorFilter instance."""
        return ErrorFilter()

    def test_non_error_instruction_passes_through(self, error_filter):
        """Test that non-error instructions pass through unchanged."""
        instruction = ["ready", "connection_id"]
        result = error_filter.filter(instruction)
        assert result == instruction

    def test_sync_instruction_passes_through(self, error_filter):
        """Test that sync instructions pass through unchanged."""
        instruction = ["sync", "123456"]
        result = error_filter.filter(instruction)
        assert result == instruction

    def test_mouse_instruction_passes_through(self, error_filter):
        """Test that mouse instructions pass through unchanged."""
        instruction = ["mouse", "100", "200", "1"]
        result = error_filter.filter(instruction)
        assert result == instruction

    def test_error_instruction_with_known_status_code(self, error_filter):
        """Test that error instructions with known status codes raise appropriate exceptions."""
        # Test unauthorized error (0x0301 = 769)
        with pytest.raises(GuapyUnauthorizedError) as exc_info:
            error_filter.filter(["error", "Access denied", "769"])

        assert "guacd error: Access denied" in str(exc_info.value)
        assert exc_info.value.details["guacd_status_code"] == 769

    def test_error_instruction_with_unknown_status_code(self, error_filter):
        """Test that error instructions with unknown status codes raise generic protocol error."""
        with pytest.raises(GuapyProtocolError) as exc_info:
            error_filter.filter(["error", "Unknown error", "999"])

        assert "guacd error: Unknown error" in str(exc_info.value)
        assert exc_info.value.details["guacd_status_code"] == 999

    def test_error_instruction_minimal_format(self, error_filter):
        """Test error instruction with minimal format (no message, no status code)."""
        instruction = ["error"]
        result = error_filter.filter(instruction)
        # Minimal format with no status code defaults to 0 (SUCCESS), should pass through
        assert result == instruction

    def test_error_instruction_no_status_code(self, error_filter):
        """Test error instruction with message but no status code."""
        instruction = ["error", "Some error"]
        result = error_filter.filter(instruction)
        # No status code defaults to 0 (SUCCESS), should pass through
        assert result == instruction

    def test_error_instruction_success_status(self, error_filter):
        """Test error instruction with SUCCESS status (0x0000) should pass through."""
        instruction = ["error", "Success message", "0"]
        result = error_filter.filter(instruction)
        # SUCCESS status should pass through without raising an exception
        assert result == instruction

    def test_unknown_status_code_defensive_handling(self, error_filter):
        """Test that unknown status codes fall back to GuapyProtocolError."""
        # Test with a non-zero status code not in the map
        unknown_status = 0x9999
        with pytest.raises(GuapyProtocolError) as exc_info:
            error_filter.filter(["error", "Unknown error type", str(unknown_status)])

        assert "guacd error: Unknown error type" in str(exc_info.value)
        assert exc_info.value.details["guacd_status_code"] == unknown_status

    def test_all_mapped_error_codes(self, error_filter):
        """Test that all mapped error codes raise the correct exception types."""
        test_cases = [
            # Unsupported operations
            (0x0100, GuapyUnsupportedError),
            # Server errors (0x02xx)
            (0x0200, GuapyServerError),
            (0x0201, GuapyServerBusyError),
            (0x0202, GuapyUpstreamTimeoutError),
            (0x0203, GuapyUpstreamError),
            (0x0204, GuapyResourceNotFoundError),
            (0x0205, GuapyResourceConflictError),
            (0x0206, GuapyResourceClosedError),
            (0x0207, GuapyUpstreamNotFoundError),
            (0x0208, GuapyUpstreamUnavailableError),
            (0x0209, GuapySessionConflictError),
            (0x020A, GuapySessionTimeoutError),
            (0x020B, GuapySessionClosedError),
            # Client errors (0x03xx)
            (0x0300, GuapyClientBadRequestError),
            (0x0301, GuapyUnauthorizedError),
            (0x0303, GuapyForbiddenError),
            (0x0308, GuapyClientTimeoutError),
            (0x030D, GuapyClientOverrunError),
            (0x030F, GuapyClientBadTypeError),
            (0x031D, GuapyClientTooManyError),
        ]

        for status_code, expected_exception in test_cases:
            with pytest.raises(expected_exception) as exc_info:
                error_filter.filter(
                    ["error", f"Test error {status_code}", str(status_code)]
                )

            assert f"guacd error: Test error {status_code}" in str(exc_info.value)
            assert exc_info.value.details["guacd_status_code"] == status_code


class TestGuacdErrorMap:
    """Test suite for GUACD_ERROR_MAP."""

    def test_error_map_completeness(self):
        """Test that GUACD_ERROR_MAP contains all expected status codes."""
        expected_codes = {
            # Note: 0x0000 SUCCESS is intentionally not included as it's not an error
            # Unsupported operations
            0x0100,
            # Server errors (0x02xx)
            0x0200,
            0x0201,
            0x0202,
            0x0203,
            0x0204,
            0x0205,
            0x0206,
            0x0207,
            0x0208,
            0x0209,
            0x020A,
            0x020B,
            # Client errors (0x03xx)
            0x0300,
            0x0301,
            0x0303,
            0x0308,
            0x030D,
            0x030F,
            0x031D,
        }

        assert set(GUACD_ERROR_MAP.keys()) == expected_codes

    def test_error_map_values_are_exception_classes(self):
        """Test that all values in GUACD_ERROR_MAP are exception classes."""
        for exception_class in GUACD_ERROR_MAP.values():
            assert issubclass(exception_class, Exception)
            assert hasattr(exception_class, "__init__")

    def test_unauthorized_vs_forbidden_mapping(self):
        """Test that 0x0301 maps to Unauthorized and 0x0303 maps to Forbidden."""
        assert GUACD_ERROR_MAP[0x0301] == GuapyUnauthorizedError
        assert GUACD_ERROR_MAP[0x0303] == GuapyForbiddenError
