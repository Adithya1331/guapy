"""Main server implementation for guapy."""

import logging
from typing import Any, Callable, Optional, Union

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .client_connection import ClientConnection
from .exceptions import WebSocketConnectionError
from .models import ClientOptions, GuacdOptions


class GuapyServer:
    """Main WebSocket server for handling Guacamole connections."""

    def __init__(
        self,
        client_options: ClientOptions,
        guacd_options: Optional[GuacdOptions] = None,
        process_connection_settings_callback: Optional[Callable] = None,
    ):
        """Initialize the Guapy server.

        Args:
            client_options: Client configuration options
            guacd_options: guacd connection options
            process_connection_settings_callback: Optional callback for processing
            connection settings

        Raises:
            TypeError: If client_options is None or not a ClientOptions instance
            TypeError: If guacd_options is not None and not a GuacdOptions instance
        """
        # Validate client_options
        if client_options is None:
            raise TypeError("client_options cannot be None")

        if not isinstance(client_options, ClientOptions):
            raise TypeError(
                "client_options must be a ClientOptions instance, got"
                + f"{type(client_options)}"
            )

        # Validate guacd_options if provided
        if guacd_options is not None and not isinstance(guacd_options, GuacdOptions):
            raise TypeError(
                "guacd_options must be a GuacdOptions instance or None, got"
                + f"{type(guacd_options)}"
            )

        self.client_options = client_options
        self.guacd_options = guacd_options or GuacdOptions()
        self.process_connection_settings_callback = process_connection_settings_callback

        self.app = FastAPI(
            title="Guapy",
            description="Python implementation of Guacamole WebSocket server",
            version="1.0.0",
        )

        self.connections: dict[int, ClientConnection] = {}
        self.connection_counter = 0

        # Setup centralized logging
        self.logger = logging.getLogger(__name__)

        self._setup_routes()
        self._setup_middleware()

        # Log startup message
        self.logger.info("Starting Guapy server")

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/")
        async def root() -> dict[str, Union[str, int]]:
            """Root endpoint - returns server info."""
            return {
                "name": "Guapy",
                "version": "1.0.0",
                "status": "running",
                "guacd_host": self.guacd_options.host,
                "guacd_port": self.guacd_options.port,
            }

        @self.app.websocket("/")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            await self.handle_websocket_connection(websocket)

        @self.app.websocket("/webSocket")
        async def websocket_alt_endpoint(websocket: WebSocket) -> None:
            """Alternative WebSocket endpoint for compatibility existing clients."""
            await self.handle_websocket_connection(websocket)

        @self.app.get("/health")
        async def health_check() -> dict[str, Union[str, int]]:
            """Health check endpoint."""
            return {
                "status": "healthy",
                "connections": len(self.connections),
                "guacd_host": self.guacd_options.host,
                "guacd_port": self.guacd_options.port,
            }

        @self.app.get("/stats")
        async def get_stats() -> dict[str, Union[int, dict[str, Union[str, int]]]]:
            """Statistics endpoint."""
            return {
                "active_connections": len(self.connections),
                "total_connections": self.connection_counter,
                "guacd_config": {
                    "host": self.guacd_options.host,
                    "port": self.guacd_options.port,
                },
            }

    def _setup_middleware(self) -> None:
        """Setup CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.client_options.cors_allow_origins,
            allow_credentials=self.client_options.cors_allow_credentials,
            allow_methods=self.client_options.cors_allow_methods,
            allow_headers=self.client_options.cors_allow_headers,
        )

    async def handle_websocket_connection(self, websocket: WebSocket) -> None:
        """Handle individual WebSocket connections."""
        self.logger.debug("New WebSocket connection request received")
        self.connection_counter += 1
        connection_id = self.connection_counter
        client_connection = None  # Initialize to track if connection was created

        try:
            self.logger.debug(f"Creating client connection {connection_id}")
            client_connection = ClientConnection(
                websocket,
                connection_id,
                self.client_options,
                self.guacd_options,
            )
            self.connections[connection_id] = client_connection
            self.logger.info(
                f"New connection established: {connection_id}",
                extra={"connection_id": connection_id},
            )
            self.logger.debug(
                f"Starting client connection handler for {connection_id}",
                extra={"connection_id": connection_id},
            )
            await client_connection.handle_connection()

        except WebSocketConnectionError as e:
            self.logger.error(
                f"WebSocket connection failed: {e}",
                extra={"connection_id": connection_id},
            )
            try:
                await websocket.close()
            except Exception as close_error:
                self.logger.error(
                    f"Failed to close websocket: {close_error}",
                    extra={"connection_id": connection_id},
                )
        except Exception as e:
            self.logger.error(
                f"Unexpected error in WebSocket connection: {e}",
                extra={"connection_id": connection_id},
            )
            try:
                await websocket.close()
            except Exception as close_error:
                self.logger.error(
                    f"Failed to close websocket: {close_error}",
                    extra={"connection_id": connection_id},
                )

        finally:
            # Always remove connection from tracking dict if it was added
            if connection_id in self.connections:
                self.logger.debug(
                    f"Cleaning up connection {connection_id}",
                    extra={"connection_id": connection_id},
                )
                del self.connections[connection_id]
                self.logger.info(
                    f"Connection cleaned up: {connection_id}",
                    extra={"connection_id": connection_id},
                )
            # Ensure client connection is properly closed
            if client_connection is not None:
                try:
                    await client_connection.close()
                    self.logger.debug(
                        f"Client connection closed for {connection_id}",
                        extra={"connection_id": connection_id},
                    )
                except Exception as close_error:
                    self.logger.error(
                        f"Error closing client connection: {close_error}",
                        extra={"connection_id": connection_id},
                    )


def create_server(
    client_options: ClientOptions,
    guacd_options: Optional[GuacdOptions] = None,
    **kwargs: Any,
) -> GuapyServer:
    """Factory function to create a GuapyServer instance.

    Args:
        client_options: Client configuration options
        guacd_options: Optional guacd connection options
        **kwargs: Additional arguments passed to server constructor

    Returns:
        Configured GuapyServer instance
    """
    return GuapyServer(client_options, guacd_options, **kwargs)
