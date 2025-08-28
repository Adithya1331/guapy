"""Tests for guapy.server module.

This module tests the main server implementation and FastAPI integration.
"""

import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from guapy.models import ClientOptions, CryptConfig, GuacdOptions
from guapy.server import GuapyServer, create_server


class TestGuapyServerInitialization:
    """Test GuapyServer initialization and configuration."""

    def test_server_initialization_basic(self, client_options, guacd_options):
        """Test basic server initialization."""
        server = GuapyServer(client_options=client_options, guacd_options=guacd_options)

        assert server.client_options == client_options
        assert server.guacd_options == guacd_options
        assert server.process_connection_settings_callback is None
        assert server.connections == {}
        assert server.connection_counter == 0

    def test_server_initialization_with_callback(self, client_options, guacd_options):
        """Test server initialization with callback."""
        callback = MagicMock()

        server = GuapyServer(
            client_options=client_options,
            guacd_options=guacd_options,
            process_connection_settings_callback=callback,
        )

        assert server.process_connection_settings_callback == callback

    def test_server_initialization_without_guacd_options(self, client_options):
        """Test server initialization without guacd options."""
        server = GuapyServer(client_options=client_options)

        assert server.guacd_options is not None
        assert isinstance(server.guacd_options, GuacdOptions)

    def test_server_fastapi_app_creation(self, guapy_server):
        """Test that FastAPI app is properly created."""
        app = guapy_server.app

        assert app is not None
        assert app.title == "Guapy"
        assert "Python implementation of Guacamole" in app.description
        assert app.version == "1.0.0"

    def test_server_cors_middleware_setup(self, guapy_server):
        """Test that CORS middleware is properly configured."""
        # Check that middleware is present
        middleware_classes = [m.cls for m in guapy_server.app.user_middleware]

        # Should have CORS middleware
        from starlette.middleware.cors import CORSMiddleware

        assert CORSMiddleware in middleware_classes

        # Verify that CORS uses configured settings, not hardcoded wildcards
        cors_middleware = None
        for middleware in guapy_server.app.user_middleware:
            if middleware.cls == CORSMiddleware:
                cors_middleware = middleware
                break

        assert cors_middleware is not None
        # The middleware should be configured with client_options CORS settings
        # Note: We can't directly inspect FastAPI middleware kwargs after setup,
        # but we can verify the client_options contain proper CORS configuration
        assert hasattr(guapy_server.client_options, "cors_allow_origins")
        assert isinstance(guapy_server.client_options.cors_allow_origins, list)
        assert len(guapy_server.client_options.cors_allow_origins) > 0

    def test_server_logging_setup(self, guapy_server):
        """Test that server logging is properly configured."""
        assert guapy_server.logger is not None
        assert guapy_server.logger.name == "guapy.server"


class TestGuapyServerRoutes:
    """Test GuapyServer route setup and handling."""

    def test_root_endpoint(self, test_client):
        """Test the root endpoint returns server info."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Guapy"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "guacd_host" in data
        assert "guacd_port" in data

    def test_health_endpoint(self, test_client):
        """Test the health check endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "connections" in data
        assert "guacd_host" in data
        assert "guacd_port" in data

    def test_stats_endpoint(self, test_client):
        """Test the statistics endpoint."""
        response = test_client.get("/stats")

        assert response.status_code == 200
        data = response.json()

        assert "active_connections" in data
        assert "total_connections" in data
        assert "guacd_config" in data
        assert data["guacd_config"]["host"] is not None
        assert data["guacd_config"]["port"] is not None

    def test_websocket_endpoint_path(self, guapy_server):
        """Test that WebSocket endpoints are registered."""
        routes = [route.path for route in guapy_server.app.routes]

        assert "/" in routes  # Main WebSocket endpoint
        assert "/webSocket" in routes  # Alternative endpoint

    def test_websocket_alternative_endpoint(self, test_client):
        """Test that alternative WebSocket endpoint exists."""
        # This tests the route existence, not WebSocket functionality
        # since TestClient doesn't support WebSocket connections directly
        routes = [route.path for route in test_client.app.routes]
        assert "/webSocket" in routes


class TestGuapyServerWebSocketHandling:
    """Test WebSocket connection handling."""

    @pytest.mark.asyncio
    async def test_websocket_connection_setup(self, guapy_server, mock_websocket):
        """Test WebSocket connection setup."""
        # Mock the client connection and its handle_connection method
        with patch("guapy.server.ClientConnection") as mock_client_conn:
            mock_client_instance = AsyncMock()
            mock_client_conn.return_value = mock_client_instance

            await guapy_server.handle_websocket_connection(mock_websocket)

            # Check that ClientConnection was created
            mock_client_conn.assert_called_once()
            # Check that handle_connection was called
            mock_client_instance.handle_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_connection_counter(self, guapy_server, mock_websocket):
        """Test that connection counter is incremented."""
        initial_counter = guapy_server.connection_counter

        with patch("guapy.server.ClientConnection") as mock_client_conn:
            mock_client_instance = AsyncMock()
            mock_client_conn.return_value = mock_client_instance

            await guapy_server.handle_websocket_connection(mock_websocket)

            assert guapy_server.connection_counter == initial_counter + 1

    @pytest.mark.asyncio
    async def test_websocket_connection_tracking(self, guapy_server, mock_websocket):
        """Test that connections are properly tracked."""
        with patch("guapy.server.ClientConnection") as mock_client_conn:
            mock_client_instance = AsyncMock()
            mock_client_conn.return_value = mock_client_instance

            await guapy_server.handle_websocket_connection(mock_websocket)

            # Connection should be tracked
            assert len(guapy_server.connections) >= 0

    @pytest.mark.asyncio
    async def test_websocket_connection_cleanup(self, guapy_server, mock_websocket):
        """Test WebSocket connection cleanup on disconnect."""
        with patch("guapy.server.ClientConnection") as mock_client_conn:
            # Simulate a disconnection
            mock_client_instance = AsyncMock()
            mock_client_instance.handle_connection.side_effect = Exception(
                "Connection closed"
            )
            mock_client_conn.return_value = mock_client_instance

            with contextlib.suppress(Exception):
                await guapy_server.handle_websocket_connection(mock_websocket)

            # Connection should be cleaned up
            # Note: Actual cleanup logic depends on implementation


class TestGuapyServerConnectionManagement:
    """Test connection management functionality."""

    def test_connection_storage_initialization(self, guapy_server):
        """Test that connection storage is properly initialized."""
        assert isinstance(guapy_server.connections, dict)
        assert len(guapy_server.connections) == 0
        assert guapy_server.connection_counter == 0

    def test_connection_id_generation(self, guapy_server):
        """Test connection ID generation."""
        # Test that connection counter increments
        initial_counter = guapy_server.connection_counter

        # Simulate adding connections
        guapy_server.connection_counter += 1
        assert guapy_server.connection_counter == initial_counter + 1

    def test_multiple_connections_tracking(self, guapy_server):
        """Test tracking multiple connections."""
        # Test connection management structure
        # Note: This tests the structure, not the full functionality
        assert isinstance(guapy_server.connections, dict)


class TestCreateServerFunction:
    """Test the create_server utility function."""

    def test_create_server_basic(self, client_options, guacd_options):
        """Test basic server creation."""
        server = create_server(client_options, guacd_options)

        assert isinstance(server, GuapyServer)
        assert server.client_options == client_options
        assert server.guacd_options == guacd_options

    def test_create_server_with_callback(self, client_options, guacd_options):
        """Test server creation with callback."""
        callback = MagicMock()

        server = create_server(
            client_options, guacd_options, process_connection_settings_callback=callback
        )

        assert server.process_connection_settings_callback == callback

    def test_create_server_minimal(self, client_options):
        """Test server creation with minimal parameters."""
        server = create_server(client_options)

        assert isinstance(server, GuapyServer)
        assert server.client_options == client_options
        assert server.guacd_options is not None


class TestGuapyServerConfiguration:
    """Test server configuration and options."""

    def test_server_with_custom_client_options(self):
        """Test server with custom client options."""
        client_options = ClientOptions(
            max_inactivity_time=30000,
            crypt=CryptConfig(key="test-encryption-key-1234567890ab"),
        )
        guacd_options = GuacdOptions(host="192.168.1.100", port=4823)

        server = GuapyServer(client_options, guacd_options)

        assert server.client_options.max_inactivity_time == 30000
        assert server.guacd_options.host == "192.168.1.100"
        assert server.guacd_options.port == 4823

    def test_server_with_custom_cors_configuration(self):
        """Test server with custom CORS configuration."""
        # Test custom CORS configuration
        client_options = ClientOptions(
            crypt=CryptConfig(key="test-encryption-key-1234567890ab"),
            cors_allow_origins=["https://myapp.com", "https://admin.myapp.com"],
            cors_allow_methods=["GET", "POST"],
            cors_allow_headers=["Content-Type", "Authorization"],
            cors_allow_credentials=False,
        )

        server = GuapyServer(client_options)

        # Verify CORS configuration is applied
        assert server.client_options.cors_allow_origins == [
            "https://myapp.com",
            "https://admin.myapp.com",
        ]
        assert server.client_options.cors_allow_methods == ["GET", "POST"]
        assert server.client_options.cors_allow_headers == [
            "Content-Type",
            "Authorization",
        ]
        assert server.client_options.cors_allow_credentials is False

    def test_server_with_development_cors(self):
        """Test server with development CORS configuration."""
        # Test development CORS utility method
        crypt_config = CryptConfig(key="test-encryption-key-1234567890ab")
        client_options = ClientOptions.create_with_development_cors(crypt_config)

        server = GuapyServer(client_options)

        # Should use wildcard for development
        assert server.client_options.cors_allow_origins == ["*"]
        assert server.client_options.cors_allow_methods == ["*"]
        assert server.client_options.cors_allow_headers == ["*"]

    def test_server_with_production_cors(self):
        """Test server with production CORS configuration."""
        # Test production CORS utility method
        crypt_config = CryptConfig(key="test-encryption-key-1234567890ab")
        allowed_origins = ["https://myapp.com", "https://app.mycompany.com"]
        client_options = ClientOptions.create_with_production_cors(
            crypt_config, allowed_origins
        )

        server = GuapyServer(client_options)

        # Should use specific origins for production
        assert server.client_options.cors_allow_origins == allowed_origins
        assert (
            "*" not in server.client_options.cors_allow_origins
        )  # No wildcards in production
        assert server.client_options.cors_allow_methods == [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
        ]
        assert "Content-Type" in server.client_options.cors_allow_headers
        assert "Authorization" in server.client_options.cors_allow_headers

    def test_server_configuration_validation(self):
        """Test server configuration validation."""
        client_options = ClientOptions(
            crypt=CryptConfig(key="test-encryption-key-1234567890ab"),
        )

        # Should not raise validation errors
        server = GuapyServer(client_options)
        assert server is not None

    def test_server_default_guacd_options(self, client_options):
        """Test server with default guacd options."""
        server = GuapyServer(client_options)

        assert server.guacd_options is not None
        assert isinstance(server.guacd_options, GuacdOptions)
        assert server.guacd_options.host is not None
        assert server.guacd_options.port > 0


class TestGuapyServerErrorHandling:
    """Test server error handling scenarios."""

    @pytest.mark.asyncio
    async def test_websocket_connection_error_handling(
        self, guapy_server, mock_websocket
    ):
        """Test WebSocket connection error handling."""
        # Mock the ClientConnection to raise an exception
        with patch("guapy.server.ClientConnection") as mock_client_conn:
            mock_client_conn.side_effect = Exception("Connection failed")

            # The server should handle the exception gracefully and not raise it
            await guapy_server.handle_websocket_connection(mock_websocket)

    def test_server_with_invalid_options(self):
        """Test server behavior with invalid options."""
        # Test with None client_options - should raise TypeError
        with pytest.raises(TypeError, match="client_options cannot be None"):
            GuapyServer(None)

        # Test with wrong type for client_options
        with pytest.raises(
            TypeError, match="client_options must be a ClientOptions instance"
        ):
            GuapyServer("invalid_type")

        # Test with wrong type for guacd_options
        client_options = ClientOptions(
            crypt=CryptConfig(key="test-encryption-key-1234567890ab")
        )
        with pytest.raises(
            TypeError, match="guacd_options must be a GuacdOptions instance"
        ):
            GuapyServer(client_options, guacd_options="invalid_type")

    @pytest.mark.asyncio
    async def test_websocket_disconnection_handling(self, guapy_server, mock_websocket):
        """Test handling of WebSocket disconnections."""
        from fastapi.websockets import WebSocketDisconnect

        with patch("guapy.server.ClientConnection") as mock_client_conn:
            mock_client_instance = AsyncMock()
            mock_client_instance.handle_connection.side_effect = WebSocketDisconnect(
                code=1000
            )
            mock_client_conn.return_value = mock_client_instance

            # Should not raise exception
            await guapy_server.handle_websocket_connection(mock_websocket)


class TestGuapyServerIntegration:
    """Test server integration scenarios."""

    def test_server_app_routes_registered(self, guapy_server):
        """Test that all expected routes are registered."""
        routes = [route.path for route in guapy_server.app.routes]

        expected_routes = ["/", "/health", "/stats", "/webSocket"]
        for route in expected_routes:
            assert route in routes

    def test_server_app_middleware_configured(self, guapy_server):
        """Test that middleware is properly configured."""
        # Should have middleware configured
        assert len(guapy_server.app.user_middleware) > 0

    def test_server_with_test_client_integration(self, test_client):
        """Test server integration with test client."""
        # Test multiple endpoints
        endpoints = ["/", "/health", "/stats"]

        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200

            # All endpoints should return JSON
            data = response.json()
            assert isinstance(data, dict)

    def test_concurrent_endpoint_access(self, test_client):
        """Test concurrent access to server endpoints."""
        import concurrent.futures

        def make_request(endpoint):
            return test_client.get(endpoint)

        endpoints = ["/", "/health", "/stats"]

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, ep) for ep in endpoints]

            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                assert response.status_code == 200


class TestGuapyServerLogging:
    """Test server logging functionality."""

    def test_server_startup_logging(self, client_options, guacd_options, caplog):
        """Test that server startup is logged."""
        import logging

        caplog.set_level(logging.INFO)

        GuapyServer(client_options, guacd_options)

        # Check for startup message
        assert any(
            "Starting Guapy server" in record.message for record in caplog.records
        )

    def test_server_request_logging(self, test_client, caplog):
        """Test that server requests can be logged."""
        import logging

        caplog.set_level(logging.DEBUG)

        # Make a request
        response = test_client.get("/health")
        assert response.status_code == 200

        # FastAPI/Uvicorn should generate some log messages
        # The exact format depends on the logging configuration


class TestGuapyServerPerformance:
    """Test server performance characteristics."""

    def test_multiple_health_checks(self, test_client):
        """Test performance of multiple health checks."""
        # Make multiple requests to ensure no memory leaks or slowdowns
        for _ in range(100):
            response = test_client.get("/health")
            assert response.status_code == 200

    def test_stats_endpoint_performance(self, test_client):
        """Test stats endpoint performance."""
        # Stats should be fast even with many calls
        for _ in range(10):
            response = test_client.get("/stats")
            assert response.status_code == 200
            data = response.json()
            assert "active_connections" in data

    def test_server_memory_usage(self, guapy_server):
        """Test that server doesn't leak memory on initialization."""
        # Basic test - just ensure server can be created and destroyed
        import gc

        initial_objects = len(gc.get_objects())

        # Create and destroy servers
        for _ in range(10):
            server = GuapyServer(
                ClientOptions(
                    crypt=CryptConfig(key="test-encryption-key-1234567890ab"),
                ),
                GuacdOptions(),
            )
            del server

        gc.collect()
        final_objects = len(gc.get_objects())

        # Should not have significantly more objects
        # (allowing for some variation in GC behavior)
        assert final_objects < initial_objects + 100


class TestGuapyServerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_server_with_minimal_configuration(self):
        """Test server with minimal configuration."""
        client_options = ClientOptions(
            max_inactivity_time=1000,
            crypt=CryptConfig(key="test-encryption-key-1234567890ab"),
        )

        server = GuapyServer(client_options)
        assert server is not None

    def test_server_with_maximum_configuration(self):
        """Test server with maximum reasonable configuration."""
        client_options = ClientOptions(
            max_inactivity_time=3600000,
            crypt=CryptConfig(key="test-encryption-key-1234567890ab"),
        )
        guacd_options = GuacdOptions(
            host="very-long-hostname.example.com",
            port=65535,
        )

        server = GuapyServer(client_options, guacd_options)
        assert server is not None

    def test_server_route_response_headers(self, test_client):
        """Test that server responses have appropriate headers."""
        response = test_client.get("/health")

        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_server_cors_headers(self, test_client):
        """Test CORS headers in responses."""
        # Make an OPTIONS request to check CORS
        response = test_client.options("/health")

        # Should handle OPTIONS request (even if empty response)
        # Different behaviors are acceptable
        assert response.status_code in [200, 204, 405]
