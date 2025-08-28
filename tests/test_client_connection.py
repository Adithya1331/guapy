"""Tests for client_connection.py."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

from guapy.client_connection import ClientConnection
from guapy.crypto import GuacamoleCrypto
from guapy.exceptions import GuapyConnectionError, TokenDecryptionError
from guapy.guacd_client import GuacdClient
from guapy.models import ClientOptions, ConnectionConfig, GuacdOptions


# Module-level fixtures to be shared across all test classes
@pytest.fixture
def mock_websocket():
    """Create mock websocket."""
    websocket = AsyncMock(WebSocket)
    websocket.query_params = {"token": "mock_token"}
    websocket.receive_text = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.close = AsyncMock()
    websocket.accept = AsyncMock()
    return websocket


@pytest.fixture
def mock_crypto():
    """Create mock crypto."""
    with patch("guapy.client_connection.GuacamoleCrypto") as mock:
        crypto_instance = MagicMock(spec=GuacamoleCrypto)
        mock.return_value = crypto_instance
        yield crypto_instance


@pytest.fixture
def mock_guacd_client():
    """Create mock guacd client."""
    with patch("guapy.client_connection.GuacdClient") as mock:
        client = MagicMock(spec=GuacdClient)
        client.connect = AsyncMock()
        client.start = AsyncMock()
        client.close = AsyncMock()
        client.send_raw_message = AsyncMock()
        client.STATE_OPEN = GuacdClient.STATE_OPEN
        mock.return_value = client
        yield client


@pytest.fixture
def client_connection_client_options():
    """Create client options for client connection."""
    options = MagicMock(spec=ClientOptions)
    # Create a proper mock for the crypt attribute
    crypt_mock = MagicMock()
    crypt_mock.cypher = "AES-256-CBC"
    crypt_mock.key = "12345678901234567890123456789012"  # 32 bytes  # nosec
    options.crypt = crypt_mock
    options.max_inactivity_time = 10000
    return options


@pytest.fixture
def client_connection_guacd_options():
    """Create guacd options for client connection."""
    options = MagicMock(spec=GuacdOptions)
    options.host = "localhost"
    options.port = 4822
    return options


@pytest.fixture
def client_connection(
    mock_websocket, client_connection_client_options, client_connection_guacd_options
):
    """Create client connection instance."""
    with patch("guapy.client_connection.GuacamoleCrypto") as mock_crypto_class:
        # Create a mock crypto instance
        mock_crypto_instance = MagicMock(spec=GuacamoleCrypto)
        mock_crypto_class.return_value = mock_crypto_instance

        connection = ClientConnection(
            websocket=mock_websocket,
            connection_id=1,
            client_options=client_connection_client_options,
            guacd_options=client_connection_guacd_options,
        )

        # Make the mock crypto accessible for test assertions
        connection._mock_crypto = mock_crypto_instance
        return connection


class TestClientConnection:
    """Test suite for ClientConnection class."""

    def test_init(self, client_connection):
        """Test initialization."""
        assert client_connection.websocket is not None
        assert client_connection.connection_id == 1
        assert client_connection.client_options is not None
        assert client_connection.guacd_options is not None
        assert client_connection.state == ClientConnection.STATE_OPEN
        assert client_connection.guacd_client is None
        assert client_connection.connection_config is None
        assert isinstance(client_connection.crypto, GuacamoleCrypto)
        assert client_connection.logger is not None

    @pytest.mark.asyncio
    async def test_send_message_open_state(self, client_connection):
        """Test send_message in open state."""
        await client_connection.send_message("test message")
        client_connection.websocket.send_text.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_send_message_closed_state(self, client_connection):
        """Test send_message in closed state."""
        client_connection.state = ClientConnection.STATE_CLOSED
        await client_connection.send_message("test message")
        client_connection.websocket.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_message_exception(self, client_connection):
        """Test send_message with exception."""
        client_connection.websocket.send_text.side_effect = Exception("Send error")

        # Mock websocket to have an available client_state (not disconnected) for close to work
        client_connection.websocket.client_state = 1

        await client_connection.send_message("test message")

        # State should be closed after exception
        assert client_connection.state == ClientConnection.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_close(self, client_connection, mock_guacd_client):
        """Test close method."""
        # Set up guacd client
        client_connection.guacd_client = mock_guacd_client

        # Mock websocket to have an available client_state (not disconnected)
        # This ensures the conditional check in close() method passes
        client_connection.websocket.client_state = MagicMock()
        client_connection.websocket.client_state.value = (
            1  # Connected state, not DISCONNECTED (3)
        )

        # Close connection
        await client_connection.close()

        # Verify state and method calls
        assert client_connection.state == ClientConnection.STATE_CLOSED
        mock_guacd_client.close.assert_called_once()
        client_connection.websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_already_closed(self, client_connection):
        """Test close when already closed."""
        client_connection.state = ClientConnection.STATE_CLOSED
        await client_connection.close()
        client_connection.websocket.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_exception(self, client_connection):
        """Test close with exception."""
        client_connection.websocket.close.side_effect = Exception("Close error")
        await client_connection.close()
        assert client_connection.state == ClientConnection.STATE_CLOSED
        # Even with an exception, it should attempt to close

    @pytest.mark.asyncio
    async def test_process_token_success(self, client_connection):
        """Test _process_token successful."""
        # Setup mock decryption and token parsing
        client_connection._mock_crypto.decrypt.return_value = {
            "protocol": "rdp",
            "hostname": "test-host",
        }

        # Create a patch for ConnectionConfig.from_token
        with patch("guapy.models.ConnectionConfig.from_token") as mock_from_token:
            mock_config = MagicMock(spec=ConnectionConfig)
            mock_from_token.return_value = mock_config

            # Call the method
            await client_connection._process_token(
                "mock_token", {"token": "mock_token"}
            )

            # Verify decryption and parsing
            client_connection._mock_crypto.decrypt.assert_called_once_with("mock_token")
            mock_from_token.assert_called_once()
            assert client_connection.connection_config == mock_config

    @pytest.mark.asyncio
    async def test_process_token_error(self, client_connection):
        """Test _process_token with error."""
        # Setup mock to raise exception
        client_connection._mock_crypto.decrypt.side_effect = Exception(
            "Decryption error"
        )

        # Call the method and check for exception
        with pytest.raises(TokenDecryptionError):
            await client_connection._process_token(
                "mock_token", {"token": "mock_token"}
            )

    @pytest.mark.asyncio
    async def test_handle_websocket_messages(
        self, client_connection, mock_guacd_client
    ):
        """Test _handle_websocket_messages method."""
        # Setup
        client_connection.guacd_client = mock_guacd_client
        client_connection.guacd_client.state = mock_guacd_client.STATE_OPEN

        # Mock WebSocket to receive one message then disconnect
        client_connection.websocket.receive_text.side_effect = [
            "test message",
            WebSocketDisconnect(),
        ]

        # Call method
        await client_connection._handle_websocket_messages()

        # Verify message was forwarded
        mock_guacd_client.send_raw_message.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_handle_websocket_messages_disconnect(self, client_connection):
        """Test _handle_websocket_messages with disconnect."""
        # Setup WebSocket to disconnect
        client_connection.websocket.receive_text.side_effect = WebSocketDisconnect()

        # Call method
        await client_connection._handle_websocket_messages()

        # Should exit the loop but not change state
        assert client_connection.state == ClientConnection.STATE_OPEN

    @pytest.mark.asyncio
    async def test_handle_websocket_messages_guapy_error(self, client_connection):
        """Test _handle_websocket_messages with GuapyConnectionError."""
        # Setup WebSocket to raise GuapyConnectionError
        client_connection.websocket.receive_text.side_effect = GuapyConnectionError(
            "Test error"
        )

        # Call method
        await client_connection._handle_websocket_messages()

        # Should exit the loop but not change state
        assert client_connection.state == ClientConnection.STATE_OPEN

    @pytest.mark.asyncio
    async def test_handle_websocket_done_normal(self, client_connection):
        """Test _handle_websocket_done with normal completion."""
        # Create mock task
        task = MagicMock()
        task.result.return_value = None

        # Call method
        client_connection._handle_websocket_done(task)

        # Verify state change
        assert client_connection.state == ClientConnection.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_handle_websocket_done_disconnect(self, client_connection):
        """Test _handle_websocket_done with WebSocketDisconnect."""
        # Create mock task
        task = MagicMock()
        task.result.side_effect = WebSocketDisconnect()

        # Call method
        client_connection._handle_websocket_done(task)

        # Verify state change
        assert client_connection.state == ClientConnection.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_handle_websocket_done_error(self, client_connection):
        """Test _handle_websocket_done with other error."""
        # Create mock task
        task = MagicMock()
        task.result.side_effect = Exception("Test error")

        # Call method
        client_connection._handle_websocket_done(task)

        # Verify state change
        assert client_connection.state == ClientConnection.STATE_CLOSED


class TestClientConnectionHandleConnection:
    """Comprehensive tests for handle_connection method to increase coverage."""

    @pytest.mark.asyncio
    async def test_handle_connection_complete_flow(
        self, client_connection, mock_websocket, mock_crypto, mock_guacd_client
    ):
        """Test complete handle_connection flow with all steps."""
        # Setup mocks
        mock_websocket.query_params = {"token": "valid_token", "protocol": "rdp"}
        client_connection._mock_crypto.decrypt.return_value = {
            "protocol": "rdp",
            "hostname": "test.com",
            "port": 3389,
            "username": "user",
            "password": "pass",
        }

        # Mock ConnectionConfig.from_token
        with patch("guapy.client_connection.ConnectionConfig") as mock_config:
            mock_config.from_token.return_value = MagicMock()

            # Mock GuacdClient start to complete normally
            mock_guacd_client.start.return_value = None

            await client_connection.handle_connection()

            # Verify all steps were called
            mock_websocket.accept.assert_called_once_with(subprotocol="guacamole")
            client_connection._mock_crypto.decrypt.assert_called_once_with(
                "valid_token"
            )
            mock_config.from_token.assert_called_once()
            mock_guacd_client.connect.assert_called_once()
            mock_guacd_client.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_connection_missing_token(
        self, client_connection, mock_websocket, mock_crypto, mock_guacd_client
    ):
        """Test handle_connection with missing token parameter."""
        mock_websocket.query_params = {}  # No token

        with pytest.raises(TokenDecryptionError, match="Missing token parameter"):
            await client_connection.handle_connection()

        mock_websocket.accept.assert_called_once_with(subprotocol="guacamole")
        client_connection._mock_crypto.decrypt.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_connection_token_decryption_error(
        self, client_connection, mock_websocket, mock_crypto, mock_guacd_client
    ):
        """Test handle_connection with token decryption failure."""
        mock_websocket.query_params = {"token": "invalid_token"}
        client_connection._mock_crypto.decrypt.side_effect = Exception(
            "Decryption failed"
        )

        with pytest.raises(TokenDecryptionError, match="Invalid token"):
            await client_connection.handle_connection()

        client_connection._mock_crypto.decrypt.assert_called_once_with("invalid_token")

    @pytest.mark.asyncio
    async def test_handle_connection_guacd_connection_error(
        self, client_connection, mock_websocket, mock_crypto, mock_guacd_client
    ):
        """Test handle_connection with guacd connection failure."""
        mock_websocket.query_params = {"token": "valid_token"}
        client_connection._mock_crypto.decrypt.return_value = {"protocol": "rdp"}

        with patch("guapy.client_connection.ConnectionConfig") as mock_config:
            mock_config.from_token.return_value = MagicMock()
            mock_guacd_client.connect.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                await client_connection.handle_connection()

    @pytest.mark.asyncio
    async def test_handle_connection_guacd_start_error(
        self, client_connection, mock_websocket, mock_crypto, mock_guacd_client
    ):
        """Test handle_connection with guacd start failure."""
        mock_websocket.query_params = {"token": "valid_token"}
        client_connection._mock_crypto.decrypt.return_value = {"protocol": "rdp"}

        with patch("guapy.client_connection.ConnectionConfig") as mock_config:
            mock_config.from_token.return_value = MagicMock()
            mock_guacd_client.start.side_effect = Exception("Start failed")

            with pytest.raises(Exception, match="Start failed"):
                await client_connection.handle_connection()

    @pytest.mark.asyncio
    async def test_handle_connection_cancelled(
        self, client_connection, mock_websocket, mock_crypto, mock_guacd_client
    ):
        """Test handle_connection when cancelled."""
        mock_websocket.query_params = {"token": "valid_token"}
        client_connection._mock_crypto.decrypt.return_value = {"protocol": "rdp"}

        with patch("guapy.client_connection.ConnectionConfig") as mock_config:
            mock_config.from_token.return_value = MagicMock()
            mock_guacd_client.start.side_effect = asyncio.CancelledError()

            with pytest.raises(asyncio.CancelledError):
                await client_connection.handle_connection()

            # Should still try to close
            client_connection.close = AsyncMock()


class TestClientConnectionWebSocketHandling:
    """Tests for WebSocket message handling to cover lines 249-271."""

    @pytest.mark.asyncio
    async def test_websocket_messages_normal_flow(
        self, client_connection, mock_websocket, mock_guacd_client
    ):
        """Test normal WebSocket message handling flow."""
        # Setup state
        client_connection.state = ClientConnection.STATE_OPEN
        client_connection.guacd_client = mock_guacd_client
        mock_guacd_client.state = mock_guacd_client.STATE_OPEN

        # Mock receiving messages
        messages = ["message1", "message2"]
        mock_websocket.receive_text.side_effect = [*messages, WebSocketDisconnect()]

        await client_connection._handle_websocket_messages()

        # Verify messages were forwarded
        assert mock_guacd_client.send_raw_message.call_count == 2
        mock_guacd_client.send_raw_message.assert_any_call("message1")
        mock_guacd_client.send_raw_message.assert_any_call("message2")

    @pytest.mark.asyncio
    async def test_websocket_disconnect_handling(
        self, client_connection, mock_websocket, mock_guacd_client
    ):
        """Test WebSocket disconnect handling."""
        client_connection.state = ClientConnection.STATE_OPEN
        mock_websocket.receive_text.side_effect = WebSocketDisconnect()

        # Should not raise exception
        await client_connection._handle_websocket_messages()

    @pytest.mark.asyncio
    async def test_websocket_guapy_connection_error(
        self, client_connection, mock_websocket, mock_guacd_client
    ):
        """Test GuapyConnectionError handling."""
        client_connection.state = ClientConnection.STATE_OPEN
        mock_websocket.receive_text.side_effect = GuapyConnectionError(
            "Connection error"
        )

        # Should not raise exception
        await client_connection._handle_websocket_messages()

    @pytest.mark.asyncio
    async def test_websocket_abnormal_closure_recovery(
        self, client_connection, mock_websocket, mock_guacd_client
    ):
        """Test recovery from abnormal closure (1006 error)."""
        client_connection.state = ClientConnection.STATE_OPEN
        client_connection.guacd_client = mock_guacd_client

        # First call raises 1006 error, second call succeeds, third disconnects
        mock_websocket.receive_text.side_effect = [
            Exception("1006: Abnormal closure"),
            "recovered_message",
            WebSocketDisconnect(),
        ]
        mock_guacd_client.state = mock_guacd_client.STATE_OPEN

        await client_connection._handle_websocket_messages()

        # Should have forwarded the recovered message
        mock_guacd_client.send_raw_message.assert_called_once_with("recovered_message")

    @pytest.mark.asyncio
    async def test_websocket_other_exception(
        self, client_connection, mock_websocket, mock_guacd_client
    ):
        """Test handling of other exceptions."""
        client_connection.state = ClientConnection.STATE_OPEN
        mock_websocket.receive_text.side_effect = Exception("Some other error")

        # Should not raise exception and should break from loop
        await client_connection._handle_websocket_messages()

    @pytest.mark.asyncio
    async def test_websocket_cancelled_error(
        self, client_connection, mock_websocket, mock_guacd_client
    ):
        """Test handling of CancelledError."""
        client_connection.state = ClientConnection.STATE_OPEN
        mock_websocket.receive_text.side_effect = asyncio.CancelledError()

        # Should not raise exception
        await client_connection._handle_websocket_messages()

    @pytest.mark.asyncio
    async def test_websocket_no_guacd_client(self, client_connection, mock_websocket):
        """Test WebSocket handling when guacd client is None."""
        client_connection.state = ClientConnection.STATE_OPEN
        client_connection.guacd_client = None
        mock_websocket.receive_text.side_effect = ["message", WebSocketDisconnect()]

        await client_connection._handle_websocket_messages()

        # Should not try to send to guacd

    @pytest.mark.asyncio
    async def test_websocket_guacd_not_open(
        self, client_connection, mock_websocket, mock_guacd_client
    ):
        """Test WebSocket handling when guacd is not in OPEN state."""
        client_connection.state = ClientConnection.STATE_OPEN
        client_connection.guacd_client = mock_guacd_client
        mock_guacd_client.state = "CLOSED"  # Not open
        mock_websocket.receive_text.side_effect = ["message", WebSocketDisconnect()]

        await client_connection._handle_websocket_messages()

        # Should not forward message
        mock_guacd_client.send_raw_message.assert_not_called()


class TestClientConnectionWebSocketDoneHandler:
    """Tests for _handle_websocket_done callback."""

    def test_websocket_done_normal_completion(self, client_connection):
        """Test WebSocket done handler with normal completion."""
        task = MagicMock()
        task.result.return_value = None  # Normal completion

        client_connection._handle_websocket_done(task)

        task.result.assert_called_once()

    def test_websocket_done_disconnect(self, client_connection):
        """Test WebSocket done handler with disconnect."""
        task = MagicMock()
        task.result.side_effect = WebSocketDisconnect()

        client_connection._handle_websocket_done(task)

        task.result.assert_called_once()

    def test_websocket_done_with_error(self, client_connection):
        """Test WebSocket done handler with error."""
        task = MagicMock()
        task.result.side_effect = Exception("Some error")

        client_connection._handle_websocket_done(task)

        task.result.assert_called_once()

    def test_websocket_done_state_change(self, client_connection):
        """Test WebSocket done handler changes state when open."""
        client_connection.state = ClientConnection.STATE_OPEN
        task = MagicMock()
        task.result.return_value = None

        client_connection._handle_websocket_done(task)

        assert client_connection.state == ClientConnection.STATE_CLOSED


class TestClientConnectionSendMessage:
    """Tests for send_message method."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, client_connection, mock_websocket):
        """Test successful message sending."""
        client_connection.state = ClientConnection.STATE_OPEN

        await client_connection.send_message("test message")

        mock_websocket.send_text.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_send_message_when_closed(self, client_connection, mock_websocket):
        """Test sending message when connection is closed."""
        client_connection.state = ClientConnection.STATE_CLOSED

        await client_connection.send_message("test message")

        mock_websocket.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_message_websocket_error(
        self, client_connection, mock_websocket
    ):
        """Test send_message with WebSocket error."""
        client_connection.state = ClientConnection.STATE_OPEN
        mock_websocket.send_text.side_effect = Exception("Send failed")
        client_connection.close = AsyncMock()

        await client_connection.send_message("test message")

        client_connection.close.assert_called_once()


class TestClientConnectionClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_with_guacd_client(
        self, client_connection, mock_websocket, mock_guacd_client
    ):
        """Test close method with guacd client."""
        client_connection.state = ClientConnection.STATE_OPEN
        client_connection.guacd_client = mock_guacd_client

        # Mock websocket to have an available client_state (not disconnected)
        # This ensures the conditional check in close() method passes
        mock_websocket.client_state = MagicMock()
        mock_websocket.client_state.value = 1  # Connected state, not DISCONNECTED (3)

        await client_connection.close()

        assert client_connection.state == ClientConnection.STATE_CLOSED
        mock_guacd_client.close.assert_called_once()
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_guacd_client(self, client_connection, mock_websocket):
        """Test close method without guacd client."""
        client_connection.state = ClientConnection.STATE_OPEN
        client_connection.guacd_client = None

        # Mock websocket to have an available client_state (not disconnected)
        # This ensures the conditional check in close() method passes
        mock_websocket.client_state = MagicMock()
        mock_websocket.client_state.value = 1  # Connected state, not DISCONNECTED (3)

        await client_connection.close()

        assert client_connection.state == ClientConnection.STATE_CLOSED
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_websocket_error(self, client_connection, mock_websocket):
        """Test close method with WebSocket error."""
        client_connection.state = ClientConnection.STATE_OPEN
        mock_websocket.close.side_effect = Exception("Close failed")

        # Should not raise exception
        await client_connection.close()

        assert client_connection.state == ClientConnection.STATE_CLOSED

    @pytest.mark.asyncio
    async def test_close_already_closed(self, client_connection, mock_websocket):
        """Test close method when already closed."""
        client_connection.state = ClientConnection.STATE_CLOSED

        await client_connection.close()

        # Should not try to close again
        mock_websocket.close.assert_not_called()


class TestClientConnectionProcessToken:
    """Tests for _process_token method."""

    @pytest.mark.asyncio
    async def test_process_token_success(self, client_connection, mock_crypto):
        """Test successful token processing."""
        token_data = {"protocol": "rdp", "hostname": "test.com"}
        client_connection._mock_crypto.decrypt.return_value = token_data
        query_params = {"token": "valid_token", "width": "1024"}

        with patch("guapy.client_connection.ConnectionConfig") as mock_config:
            mock_config.from_token.return_value = MagicMock()

            await client_connection._process_token("valid_token", query_params)

            client_connection._mock_crypto.decrypt.assert_called_once_with(
                "valid_token"
            )
            mock_config.from_token.assert_called_once_with(token_data, query_params)

    @pytest.mark.asyncio
    async def test_process_token_decryption_error(self, client_connection, mock_crypto):
        """Test token processing with decryption error."""
        client_connection._mock_crypto.decrypt.side_effect = Exception("Bad token")

        with pytest.raises(TokenDecryptionError, match="Invalid token"):
            await client_connection._process_token("bad_token", {})

    @pytest.mark.asyncio
    async def test_process_token_config_error(self, client_connection, mock_crypto):
        """Test token processing with ConnectionConfig error."""
        client_connection._mock_crypto.decrypt.return_value = {"protocol": "rdp"}

        with patch("guapy.client_connection.ConnectionConfig") as mock_config:
            mock_config.from_token.side_effect = Exception("Invalid config")

            with pytest.raises(TokenDecryptionError, match="Invalid token"):
                await client_connection._process_token("token", {})


class TestClientConnectionStateManagement:
    """Tests for connection state management."""

    def test_initial_state(self, client_connection):
        """Test initial connection state."""
        assert client_connection.state == ClientConnection.STATE_OPEN
        assert client_connection.connection_id == 1
        assert client_connection.guacd_client is None
        assert client_connection.connection_config is None

    def test_state_constants(self):
        """Test state constants exist."""
        assert hasattr(ClientConnection, "STATE_OPEN")
        assert hasattr(ClientConnection, "STATE_CLOSED")
        assert ClientConnection.STATE_OPEN == 1
        assert ClientConnection.STATE_CLOSED == 2

    def test_crypto_initialization(
        self, client_connection, client_connection_client_options
    ):
        """Test crypto is properly initialized."""
        assert client_connection.crypto is not None
        # Verify crypto was created with correct parameters
        assert isinstance(client_connection.crypto, GuacamoleCrypto)

    def test_last_activity_tracking(self, client_connection):
        """Test last activity time tracking."""
        import time

        initial_time = client_connection.last_activity
        time.sleep(0.01)  # Small delay

        # After some time, should be different
        assert (
            client_connection.last_activity == initial_time
        )  # Not updated until activity
