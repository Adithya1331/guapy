"""Tests for guacd_client.py."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from guapy.exceptions import GuacdConnectionError, HandshakeError, ProtocolParsingError
from guapy.guacd_client import GuacamoleProtocol, GuacdClient


class TestGuacamoleProtocol:
    """Test suite for GuacamoleProtocol class."""

    def test_format_instruction_basic(self):
        """Test format_instruction with basic input."""
        result = GuacamoleProtocol.format_instruction(["select", "rdp"])
        assert result == "6.select,3.rdp;"

    def test_format_instruction_with_none(self):
        """Test format_instruction with None values."""
        result = GuacamoleProtocol.format_instruction(["select", None, "rdp"])
        assert result == "6.select,0.,3.rdp;"

    def test_format_instruction_with_numbers(self):
        """Test format_instruction with numeric values."""
        result = GuacamoleProtocol.format_instruction(["size", 800, 600])
        assert result == "4.size,3.800,3.600;"

    def test_parse_instruction_basic(self):
        """Test parse_instruction with basic input."""
        result = GuacamoleProtocol.parse_instruction("6.select,3.rdp;")
        assert result == ["select", "rdp"]

    def test_parse_instruction_complex(self):
        """Test parse_instruction with complex input."""
        result = GuacamoleProtocol.parse_instruction("4.size,3.800,3.600;")
        assert result == ["size", "800", "600"]

    def test_parse_instruction_invalid_no_semicolon(self):
        """Test parse_instruction with invalid input - no semicolon."""
        with pytest.raises(
            ProtocolParsingError,
            match="parse_instruction should only be called on a complete, semicolon-terminated instruction",
        ):
            GuacamoleProtocol.parse_instruction("6.select,3.rdp")

    def test_parse_instruction_invalid_format(self):
        """Test parse_instruction with invalid format."""
        with pytest.raises(ValueError):
            GuacamoleProtocol.parse_instruction("select,rdp;")

    def test_parse_instruction_empty(self):
        """Test parse_instruction with empty input."""
        result = GuacamoleProtocol.parse_instruction(";")
        assert result == []

    def test_parse_instruction_with_dots_in_content(self):
        """Test parse_instruction with dots in content."""
        # This tests the alternative parsing path for elements with dots
        result = GuacamoleProtocol.parse_instruction("9.test.data,4.test;")
        assert result == ["test.data", "test"]

    def test_parse_instruction_length_mismatch(self):
        """Test parse_instruction with length mismatch."""
        # This should trigger length mismatch error
        # In "5.test", length is 5 but "test" has length 4
        with pytest.raises(ValueError):
            GuacamoleProtocol.parse_instruction("5.test,4.data;")

    def test_parse_instruction_invalid_length(self):
        """Test parse_instruction with invalid length."""
        # This should trigger the ValueError exception path
        with pytest.raises(ValueError):
            GuacamoleProtocol.parse_instruction("abc.test,4.data;")

    def test_parse_instruction_no_dot_in_element(self):
        """Test parse_instruction with element missing dot."""
        # This should trigger the "no dot" error path
        with pytest.raises(ValueError):
            GuacamoleProtocol.parse_instruction("nodot,4.data;")

    def test_parse_instruction_remaining_length_mismatch(self):
        """Test parse_instruction where remaining content length
        doesn't match expected."""
        # This creates a case where len(remaining) != expected_length
        # "10.test" - expected length is 10 but "test" is only 4 chars
        result = GuacamoleProtocol.parse_instruction("10.test,4.data;")
        # The current implementation doesn't validate length, it just extracts
        assert result == ["test,4.dat"]  # Only extracts 10 chars total
        # This would actually extract 10 characters starting from "test"


class TestGuacdClient:
    """Test suite for GuacdClient class."""

    @pytest.fixture
    def mock_client_connection(self):
        """Create a mock client connection."""
        connection = MagicMock()
        connection.connection_config.protocol.value = "rdp"
        connection.connection_config.settings.width = 800
        connection.connection_config.settings.height = 600
        connection.connection_config.settings.dpi = 96
        connection.connection_config.settings.color_depth = 24
        connection.connection_config.settings.audio = "audio/L8"
        connection.connection_config.settings.video = "video/webm"
        connection.connection_config.connection.hostname = "localhost"
        connection.connection_config.connection.port = 3389
        connection.connection_config.connection.username = "user"
        connection.connection_config.connection.password = "password"
        connection.connection_config.connection.domain = "domain"
        connection.connection_config.connection.security = "any"
        connection.connection_config.connection.ignore_cert = True
        connection.connection_config.connection.disable_auth = False
        connection.connection_id = 1
        connection.send_message = AsyncMock()
        return connection

    @pytest.fixture
    def mock_reader_writer(self):
        """Create mock StreamReader and StreamWriter."""
        reader = AsyncMock()
        writer = AsyncMock()
        writer.write = MagicMock()
        writer.drain = AsyncMock()
        writer.close = MagicMock()
        writer.wait_closed = AsyncMock()
        return reader, writer

    @pytest.fixture
    def guacd_client(self, mock_client_connection):
        """Create GuacdClient instance."""
        return GuacdClient(mock_client_connection)

    def test_init(self, guacd_client, mock_client_connection):
        """Test GuacdClient initialization."""
        assert guacd_client.client_connection == mock_client_connection
        assert guacd_client.state == GuacdClient.STATE_OPENING
        assert guacd_client.reader is None
        assert guacd_client.writer is None
        assert guacd_client._buffer == ""
        # Remove the _activity_check_task assertion since it was removed
        assert hasattr(guacd_client, "logger")
        assert hasattr(guacd_client, "last_activity")
        # Test filter initialization
        assert len(guacd_client.filters) == 1
        assert guacd_client.filters[0].__class__.__name__ == "ErrorFilter"

    def test_apply_filters(self, guacd_client):
        """Test _apply_filters method."""
        # Test normal instruction passes through
        instruction = ["ready", "connection_id"]
        filtered = guacd_client._apply_filters(instruction)
        assert filtered == instruction

        # Test error instruction raises exception
        error_instruction = ["error", "Test error", "769"]  # 0x0301 = 769
        with pytest.raises(Exception):  # Should raise GuapyUnauthorizedError
            guacd_client._apply_filters(error_instruction)

    @pytest.mark.asyncio
    async def test_connect_success(self, guacd_client, mock_reader_writer):
        """Test successful connection to guacd."""
        reader, writer = mock_reader_writer

        # Mock asyncio.open_connection
        with (
            patch("asyncio.open_connection", return_value=(reader, writer)),
            patch.object(guacd_client, "_start_handshake", AsyncMock()),
        ):
            await guacd_client.connect("localhost", 4822)

            assert guacd_client.reader == reader
            assert guacd_client.writer == writer
            assert guacd_client.state == GuacdClient.STATE_OPENING
            guacd_client._start_handshake.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, guacd_client):
        """Test failed connection to guacd."""
        # Mock asyncio.open_connection to raise exception
        with (
            patch(
                "asyncio.open_connection", side_effect=Exception("Connection failed")
            ),
            pytest.raises(GuacdConnectionError),
        ):
            await guacd_client.connect("localhost", 4822)

    @pytest.mark.asyncio
    async def test_send_instruction(self, guacd_client, mock_reader_writer):
        """Test send_instruction."""
        _, writer = mock_reader_writer
        guacd_client.writer = writer
        guacd_client.state = GuacdClient.STATE_OPEN

        await guacd_client.send_instruction(["select", "rdp"])

        # Check that the correct format was written
        writer.write.assert_called_once()
        writer.drain.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_raw_message(self, guacd_client, mock_reader_writer):
        """Test send_raw_message."""
        _, writer = mock_reader_writer
        guacd_client.writer = writer
        guacd_client.state = GuacdClient.STATE_OPEN

        raw_message = "4.size,3.800,3.600;"
        await guacd_client.send_raw_message(raw_message)

        # Check that the raw message was written directly
        writer.write.assert_called_once_with(raw_message.encode())
        writer.drain.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_raw_message_invalid(self, guacd_client, mock_reader_writer):
        """Test send_raw_message with invalid message."""
        _, writer = mock_reader_writer
        guacd_client.writer = writer
        guacd_client.state = GuacdClient.STATE_OPEN

        raw_message = "invalid message"
        await guacd_client.send_raw_message(raw_message)

        # Raw message should be sent as-is, regardless of validity
        writer.write.assert_called_once_with(raw_message.encode())
        writer.drain.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, guacd_client, mock_reader_writer):
        """Test close method."""
        _, writer = mock_reader_writer
        guacd_client.writer = writer
        guacd_client.state = GuacdClient.STATE_OPEN

        await guacd_client.close()

        assert guacd_client.state == GuacdClient.STATE_CLOSED
        writer.close.assert_called_once()
        writer.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_writer(self, guacd_client):
        """Test close method with no writer."""
        guacd_client.state = GuacdClient.STATE_OPEN

        await guacd_client.close()

        assert guacd_client.state == GuacdClient.STATE_CLOSED
        # Should not raise exception even though writer is None

    @pytest.mark.asyncio
    async def test_receive_instruction(self, guacd_client, mock_reader_writer):
        """Test _receive_instruction method."""
        reader, _ = mock_reader_writer
        guacd_client.reader = reader

        # Mock reader.read to return a complete instruction
        reader.read.return_value = b"4.size,3.800,3.600;"

        result = await guacd_client._receive_instruction()
        assert result == ["size", "800", "600"]

    @pytest.mark.asyncio
    async def test_start_handshake_success(self, guacd_client):
        """Test _start_handshake success path."""
        guacd_client.send_instruction = AsyncMock()
        guacd_client._receive_instruction = AsyncMock(
            return_value=["args", "1.0", "width", "height"]
        )

        # Mock a second call for the ready instruction
        guacd_client._receive_instruction.side_effect = [
            ["args", "1.0", "width", "height"],
            ["ready", "connection_id"],
        ]

        await guacd_client._start_handshake()

        # Verify protocol selection was sent
        assert guacd_client.send_instruction.call_count >= 1
        # Verify state is now OPEN
        assert guacd_client.state == GuacdClient.STATE_OPEN

    @pytest.mark.asyncio
    async def test_start_handshake_no_instruction(self, guacd_client):
        """Test _start_handshake with no response."""
        guacd_client.send_instruction = AsyncMock()
        guacd_client._receive_instruction = AsyncMock(return_value=[])

        with pytest.raises(HandshakeError) as exc_info:
            await guacd_client._start_handshake()

        # Check that it's the specific HandshakeError
        assert "Expected 'args' instruction from guacd" in str(exc_info.value)
        guacd_client.send_instruction.assert_called_once()
        guacd_client._receive_instruction.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_handshake_wrong_instruction(self, guacd_client):
        """Test _start_handshake with wrong instruction type."""
        guacd_client.send_instruction = AsyncMock()
        guacd_client._receive_instruction = AsyncMock(return_value=["error", "message"])

        with pytest.raises(HandshakeError) as exc_info:
            await guacd_client._start_handshake()

        # Check that it's the specific HandshakeError
        assert "Expected 'args' instruction from guacd" in str(exc_info.value)
        guacd_client.send_instruction.assert_called_once()
        guacd_client._receive_instruction.assert_called_once()


class TestGuacdClientAdvanced:
    """Advanced test suite for GuacdClient class."""

    @pytest.fixture
    def mock_client_connection(self):
        """Create a mock client connection."""
        connection = MagicMock()
        connection.connection_config.protocol.value = "rdp"
        connection.connection_config.settings.width = 800
        connection.connection_config.settings.height = 600
        connection.connection_config.settings.dpi = 96
        connection.connection_config.settings.color_depth = 24
        connection.connection_config.settings.audio = "audio/L8"
        connection.connection_config.settings.video = "video/webm"
        # Create mock connection settings with various attribute types
        connection.connection_config.settings.hostname = "localhost"
        connection.connection_config.settings.port = 3389
        connection.connection_config.settings.username = "user"
        connection.connection_config.settings.password = "test_pass"
        connection.connection_config.settings.domain = "domain"
        connection.connection_config.settings.security = "any"
        connection.connection_config.settings.ignore_cert = True  # Boolean value
        connection.connection_config.settings.disable_auth = False  # Boolean value
        connection.connection_config.settings.optional_param = None  # None value
        connection.connection_id = 1
        connection.send_message = AsyncMock()
        connection.STATE_OPEN = 1
        connection.state = 1
        return connection

    @pytest.fixture
    def guacd_client(self, mock_client_connection):
        """Create GuacdClient instance."""
        return GuacdClient(mock_client_connection)

    @pytest.mark.asyncio
    async def test_send_instruction_not_connected(self, guacd_client):
        """Test send_instruction when not connected."""
        # Writer is None (not connected)
        with pytest.raises(ConnectionError, match="Not connected to guacd"):
            await guacd_client.send_instruction(["select", "rdp"])

    @pytest.mark.asyncio
    async def test_send_raw_message_not_connected(self, guacd_client):
        """Test send_raw_message when not connected."""
        # Writer is None (not connected)
        with pytest.raises(ConnectionError, match="Not connected to guacd"):
            await guacd_client.send_raw_message("test message")

    @pytest.mark.asyncio
    async def test_receive_instruction_no_reader(self, guacd_client):
        """Test _receive_instruction when no reader available."""
        # Reader is None
        result = await guacd_client._receive_instruction()
        assert result is None

    @pytest.mark.asyncio
    async def test_receive_instruction_connection_closed(self, guacd_client):
        """Test _receive_instruction when connection closed by server."""
        mock_reader = AsyncMock()
        mock_reader.read.return_value = (
            b""  # Empty response indicates closed connection
        )
        guacd_client.reader = mock_reader

        result = await guacd_client._receive_instruction()
        assert result is None

    @pytest.mark.asyncio
    async def test_receive_instruction_chunked_data(self, guacd_client):
        """Test _receive_instruction with chunked data."""
        mock_reader = AsyncMock()
        # Simulate receiving data in chunks
        mock_reader.read.side_effect = [
            b"4.size,3.",  # First chunk
            b"800,3.600;",  # Second chunk
        ]
        guacd_client.reader = mock_reader

        result = await guacd_client._receive_instruction()
        assert result == ["size", "800", "600"]

    @pytest.mark.asyncio
    async def test_start_handshake_error_response(self, guacd_client):
        """Test _start_handshake when guacd returns error during ready phase."""
        guacd_client.send_instruction = AsyncMock()

        # Mock the sequence: args instruction, then error instruction with status code
        guacd_client._receive_instruction = AsyncMock(
            side_effect=[
                ["args", "1.0", "width", "height"],  # First response
                [
                    "error",
                    "Connection failed",
                    "513",
                ],  # Error response with status code 0x0201 (SERVER_BUSY)
            ]
        )

        # The filter will raise GuapyServerBusyError, which will be caught and re-raised as GuacdConnectionError
        with pytest.raises(GuacdConnectionError, match="Unexpected handshake failure"):
            await guacd_client._start_handshake()

        assert guacd_client.state == GuacdClient.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_start_handshake_error_no_message(self, guacd_client):
        """Test _start_handshake when guacd returns error without message."""
        guacd_client.send_instruction = AsyncMock()

        # Mock the sequence: args instruction, then error instruction without message but with status code
        guacd_client._receive_instruction = AsyncMock(
            side_effect=[
                ["args", "1.0", "width", "height"],  # First response
                [
                    "error",
                    "",
                    "512",
                ],  # Error response without message but with status code 0x0200 (SERVER_ERROR)
            ]
        )

        # The filter will raise GuapyServerError, which will be caught and re-raised as GuacdConnectionError
        with pytest.raises(GuacdConnectionError, match="Unexpected handshake failure"):
            await guacd_client._start_handshake()

        assert guacd_client.state == GuacdClient.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_start_handshake_no_ready_instruction(self, guacd_client):
        """Test _start_handshake when no ready instruction received."""
        guacd_client.send_instruction = AsyncMock()

        # Mock the sequence: args instruction, then empty response
        guacd_client._receive_instruction = AsyncMock(
            side_effect=[
                ["args", "1.0", "width", "height"],  # First response
                [],  # Empty response (no ready)
            ]
        )

        with pytest.raises(
            HandshakeError, match="No 'ready' instruction received from guacd"
        ):
            await guacd_client._start_handshake()

        assert guacd_client.state == GuacdClient.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_start_handshake_wrong_ready_instruction(self, guacd_client):
        """Test _start_handshake when wrong instruction received instead of ready."""
        guacd_client.send_instruction = AsyncMock()

        # Mock the sequence: args instruction, then wrong instruction
        guacd_client._receive_instruction = AsyncMock(
            side_effect=[
                ["args", "1.0", "width", "height"],  # First response
                ["unexpected", "data"],  # Wrong instruction
            ]
        )

        with pytest.raises(
            HandshakeError, match="Expected 'ready' instruction, got: unexpected"
        ):
            await guacd_client._start_handshake()

        assert guacd_client.state == GuacdClient.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_start_handshake_boolean_and_none_parameters(self, guacd_client):
        """Test _start_handshake with boolean and None parameters."""
        guacd_client.send_instruction = AsyncMock()

        # Mock the sequence for successful handshake
        guacd_client._receive_instruction = AsyncMock(
            side_effect=[
                ["args", "1.0", "ignore-cert", "disable-auth", "optional-param"],
                ["ready", "connection_id"],
            ]
        )

        await guacd_client._start_handshake()

        # Verify that send_instruction was called with properly
        # formatted boolean/None values
        calls = guacd_client.send_instruction.call_args_list
        connect_call = None
        for call in calls:
            if call[0][0][0] == "connect":
                connect_call = call[0][0]
                break

        assert connect_call is not None
        # Check that boolean True became "true", False became "false", None became ""
        assert "true" in connect_call  # ignore_cert = True
        assert "false" in connect_call  # disable_auth = False
        assert "" in connect_call  # optional_param = None

    @pytest.mark.asyncio
    async def test_start_message_processing_normal(self, guacd_client):
        """Test start method for normal message processing."""
        mock_reader = AsyncMock()
        guacd_client.reader = mock_reader
        guacd_client.state = GuacdClient.STATE_OPEN

        # Mock reader to return some data then close
        mock_reader.read.side_effect = [
            b"4.sync,9.123456789;",  # Sync instruction
            b"",  # Connection closed
        ]

        guacd_client._process_and_forward_buffer = AsyncMock()

        await guacd_client.start()

        assert guacd_client.state == GuacdClient.STATE_CLOSED
        assert guacd_client._process_and_forward_buffer.called

    @pytest.mark.asyncio
    async def test_start_message_processing_cancelled(self, guacd_client):
        """Test start method when cancelled."""
        mock_reader = AsyncMock()
        guacd_client.reader = mock_reader
        guacd_client.state = GuacdClient.STATE_OPEN

        # Mock reader to raise CancelledError
        mock_reader.read.side_effect = asyncio.CancelledError()

        await guacd_client.start()

        assert guacd_client.state == GuacdClient.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_start_message_processing_exception(self, guacd_client):
        """Test start method with exception."""
        mock_reader = AsyncMock()
        guacd_client.reader = mock_reader
        guacd_client.state = GuacdClient.STATE_OPEN

        # Mock reader to raise an exception
        mock_reader.read.side_effect = Exception("Read error")

        await guacd_client.start()

        assert guacd_client.state == GuacdClient.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_process_and_forward_buffer_sync_handling(
        self, guacd_client, mock_client_connection
    ):
        """Test _process_and_forward_buffer with sync instruction handling."""
        guacd_client._buffer = "4.sync,9.123456789;4.test,4.data;"
        guacd_client.send_instruction = AsyncMock()

        await guacd_client._process_and_forward_buffer()

        # Verify sync reply was sent
        guacd_client.send_instruction.assert_called_with(["sync", "123456789"])

        # Verify messages were sent to WebSocket (properly formatted)
        assert mock_client_connection.send_message.call_count == 2
        # First call should be the formatted sync instruction
        # Second call should be the formatted test instruction

    @pytest.mark.asyncio
    async def test_process_and_forward_buffer_invalid_instruction(
        self, guacd_client, mock_client_connection
    ):
        """Test _process_and_forward_buffer with invalid instruction."""
        guacd_client._buffer = "invalid;4.test,4.data;"

        # Since _find_instruction_end now raises ProtocolParsingError for invalid instructions,
        # this test should expect ProtocolParsingError
        with pytest.raises(ProtocolParsingError):
            await guacd_client._process_and_forward_buffer()

    @pytest.mark.asyncio
    async def test_process_and_forward_buffer_closed_connection(
        self, guacd_client, mock_client_connection
    ):
        """Test _process_and_forward_buffer when WebSocket connection is closed."""
        guacd_client._buffer = "4.test,4.data;"
        mock_client_connection.state = 0  # Closed state

        await guacd_client._process_and_forward_buffer()

        # Should not send message when WebSocket is closed
        mock_client_connection.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_and_forward_buffer_sync_error(
        self, guacd_client, mock_client_connection
    ):
        """Test _process_and_forward_buffer when sync reply fails."""
        guacd_client._buffer = "4.sync,9.123456789;"
        guacd_client.send_instruction = AsyncMock(side_effect=Exception("Send error"))

        # Sync errors should propagate in the current implementation
        with pytest.raises(Exception, match="Send error"):
            await guacd_client._process_and_forward_buffer()

    @pytest.mark.asyncio
    async def test_process_and_forward_buffer_exception(
        self, guacd_client, mock_client_connection
    ):
        """Test _process_and_forward_buffer with exception."""
        guacd_client._buffer = "4.test,4.data;"
        mock_client_connection.send_message.side_effect = Exception("Send error")

        # The new implementation doesn't catch exceptions, so it should propagate
        with pytest.raises(Exception, match="Send error"):
            await guacd_client._process_and_forward_buffer()

    @pytest.mark.asyncio
    async def test_close_with_exception(self, guacd_client):
        """Test close method when writer.close() raises exception."""
        mock_writer = AsyncMock()
        mock_writer.close.side_effect = Exception("Close error")
        mock_writer.wait_closed.side_effect = Exception("Wait closed error")
        guacd_client.writer = mock_writer

        # Should not raise exception
        await guacd_client.close()

        assert guacd_client.state == GuacdClient.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_start_message_loop_exception_handling(self, guacd_client):
        """Test exception handling in the main message loop."""
        # Set up connected state
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        guacd_client.reader = mock_reader
        guacd_client.writer = mock_writer
        guacd_client.state = GuacdClient.STATE_OPEN

        # Mock reader.read to raise an exception (not CancelledError)
        mock_reader.read.side_effect = RuntimeError("Unexpected error")

        # This should catch the exception and log it, not propagate
        await guacd_client.start()

        # Should have tried to read at least once
        mock_reader.read.assert_called()
        # State should be closed after exception
        assert guacd_client.state == GuacdClient.STATE_CLOSED
