"""Client connection handling for WebSocket connections."""

import asyncio
import contextlib
import logging
from typing import Optional

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

from .crypto import GuacamoleCrypto
from .exceptions import (
    GuapyConnectionError,
    TokenDecryptionError,
)
from .guacd_client import GuacdClient
from .models import ClientOptions, ConnectionConfig, GuacdOptions


class ClientConnection:
    """Handles individual WebSocket client connections with proper state management."""

    STATE_OPEN = 1
    STATE_CLOSED = 2

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
        self.websocket = websocket
        self.connection_id = connection_id
        self.client_options = client_options
        self.guacd_options = guacd_options
        self.logger = logging.getLogger(__name__)

        self.state = self.STATE_OPEN  # Start in open state
        self.last_activity = asyncio.get_event_loop().time()
        self.guacd_client: Optional[GuacdClient] = None
        self.connection_config: Optional[ConnectionConfig] = None

        self.crypto = GuacamoleCrypto(
            client_options.crypt.cypher, client_options.crypt.key
        )

    async def handle_connection(self) -> None:
        """Main connection handler with proper state management."""
        try:
            self.logger.debug(
                "Starting WebSocket connection acceptance",
                extra={"connection_id": self.connection_id},
            )
            await self.websocket.accept(subprotocol="guacamole")
            self.logger.debug(
                "WebSocket connection accepted",
                extra={"connection_id": self.connection_id},
            )

            # Process connection token
            query_params = dict(self.websocket.query_params)
            self.logger.debug(
                f"Received query params: {query_params}",
                extra={"connection_id": self.connection_id},
            )

            if not query_params.get("token"):
                self.logger.error(
                    "Missing token parameter",
                    extra={"connection_id": self.connection_id},
                )
                raise TokenDecryptionError("Missing token parameter")

            self.logger.debug(
                "Processing token...", extra={"connection_id": self.connection_id}
            )
            await self._process_token(query_params["token"], query_params)

            self.logger.debug(
                f"Creating GuacdClient for connection {self.connection_id}",
                extra={"connection_id": self.connection_id},
            )
            self.guacd_client = GuacdClient(
                self,
            )
            self.logger.debug(
                f"Connecting to guacd at "
                f"{self.guacd_options.host}:{self.guacd_options.port}",
                extra={"connection_id": self.connection_id},
            )
            await self.guacd_client.connect(
                self.guacd_options.host, self.guacd_options.port
            )  # Start guacd message processing
            self.logger.debug(
                "Starting guacd message processing",
                extra={"connection_id": self.connection_id},
            )
            # Create tasks but don't await them yet - let guacd drive lifecycle
            guacd_task = asyncio.create_task(self.guacd_client.start())
            websocket_task = asyncio.create_task(self._handle_websocket_messages())
            self.logger.debug(
                "Connection ready - waiting for messages",
                extra={"connection_id": self.connection_id},
            )
            try:
                # Use a done callback to handle WebSocket closure gracefully
                websocket_task.add_done_callback(
                    lambda t: self._handle_websocket_done(t)
                )

                # Only wait for guacd task
                # where guacd connection drives the lifecycle
                await guacd_task

            except Exception as e:
                self.logger.error(
                    f"GuacdClient error: {e}",
                    extra={"connection_id": self.connection_id},
                )
                # Only if guacd fails, we need to close everything
                raise
            finally:
                if not websocket_task.done():
                    # Gracefully cancel WebSocket if still running
                    websocket_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await websocket_task

            # Clean up
            self.logger.debug(
                "Starting cleanup", extra={"connection_id": self.connection_id}
            )
            await self.close()
            self.logger.debug(
                "Cleanup completed", extra={"connection_id": self.connection_id}
            )

        except asyncio.CancelledError:
            self.logger.info(
                "Connection handler cancelled",
                extra={"connection_id": self.connection_id},
            )
            await self.close()
            raise
        except Exception as e:
            self.logger.error(
                f"ERROR in handle_connection: {e!s}",
                extra={"connection_id": self.connection_id},
            )
            raise
        finally:
            self.logger.debug(
                "Connection handler ended", extra={"connection_id": self.connection_id}
            )

    async def _process_token(self, token: str, query_params: dict[str, str]) -> None:
        """Process and validate connection token."""
        try:
            token_data = self.crypto.decrypt(token)
            self.connection_config = ConnectionConfig.from_token(
                token_data, query_params
            )
            self.logger.info(
                "Token processed successfully",
                extra={"connection_id": self.connection_id},
            )

        except Exception as e:
            raise TokenDecryptionError(f"Invalid token: {e}") from e

    async def send_message(self, message: str) -> None:
        """Send message to WebSocket client."""
        if self.state == self.STATE_OPEN:
            try:
                await self.websocket.send_text(message)
                self.last_activity = asyncio.get_event_loop().time()
            except Exception as e:
                self.logger.error(
                    f"Failed to send message: {e}",
                    extra={"connection_id": self.connection_id},
                )
                await self.close()

    async def close(self) -> None:
        """Close connection and cleanup."""
        if self.state != self.STATE_CLOSED:
            self.logger.debug(
                f"Closing connection {self.connection_id}",
                extra={"connection_id": self.connection_id},
            )
            self.state = self.STATE_CLOSED

            if self.guacd_client:
                await self.guacd_client.close()

            try:
                # Check if websocket is still available before closing
                if (
                    hasattr(self.websocket, "client_state")
                    and self.websocket.client_state.value != 3
                ):  # 3 = DISCONNECTED
                    await self.websocket.close()
            except Exception as e:
                self.logger.debug(
                    f"WebSocket close error (likely already closed): {e}",
                    extra={"connection_id": self.connection_id},
                )
        else:
            self.logger.debug(
                f"Connection {self.connection_id} already closed",
                extra={"connection_id": self.connection_id},
            )

    async def _handle_websocket_messages(self) -> None:
        """Handle WebSocket messages in event-driven manner."""
        try:
            while self.state == self.STATE_OPEN:
                try:
                    # Non-blocking receive with timeout to allow for cleanup
                    message = await asyncio.wait_for(
                        self.websocket.receive_text(), timeout=None
                    )
                    self.logger.debug(
                        f"Received WebSocket message: {message}",
                        extra={"connection_id": self.connection_id},
                    )
                    self.last_activity = asyncio.get_event_loop().time()

                    if (
                        self.guacd_client
                        and self.guacd_client.state == self.guacd_client.STATE_OPEN
                    ):
                        self.logger.debug(
                            "Forwarding raw message to guacd",
                            extra={"connection_id": self.connection_id},
                        )
                        # Forward raw message directly to guacd
                        await self.guacd_client.send_raw_message(message)

                except WebSocketDisconnect as e:
                    self.logger.debug(
                        f"WebSocket disconnected: {e}",
                        extra={"connection_id": self.connection_id},
                    )
                    # Do NOT set self.state = STATE_CLOSED here!
                    break
                except GuapyConnectionError as e:
                    self.logger.debug(
                        f"Guapy connection error: {e}",
                        extra={"connection_id": self.connection_id},
                    )
                    # Do NOT set self.state = STATE_CLOSED here!
                    break
                except Exception as e:
                    self.logger.debug(
                        f"WebSocket error: {e}",
                        extra={"connection_id": self.connection_id},
                    )
                    if str(e).startswith("1006"):  # Abnormal closure
                        self.logger.debug(
                            "Attempting to recover from abnormal closure",
                            extra={"connection_id": self.connection_id},
                        )
                        # Don't break - try to keep connection alive
                        await asyncio.sleep(0.1)  # Small delay before retry
                        continue
                    # Do NOT set self.state = STATE_CLOSED here!
                    break

        except asyncio.CancelledError:
            self.logger.info(
                "WebSocket message handler cancelled (outer)",
                extra={"connection_id": self.connection_id},
            )
        except Exception as e:
            self.logger.debug(
                f"WebSocket message handler error: {e}",
                extra={"connection_id": self.connection_id},
            )
        finally:
            self.logger.debug(
                "WebSocket message handler ended",
                extra={"connection_id": self.connection_id},
            )

    def _handle_websocket_done(self, task: asyncio.Task[None]) -> None:
        """Handle WebSocket task completion.

        This is called when the WebSocket task is done, either due to normal completion
        or an error.

        Args:
            task: The completed WebSocket task
        """
        try:
            # Try to get the result to check if there was an error
            task.result()
            self.logger.debug(
                "WebSocket closed normally", extra={"connection_id": self.connection_id}
            )
        except WebSocketDisconnect:
            self.logger.debug(
                "WebSocket closed by client",
                extra={"connection_id": self.connection_id},
            )
        except Exception as e:
            self.logger.debug(
                f"WebSocket closed with error: {e}",
                extra={"connection_id": self.connection_id},
            )

        # Set connection state to closed when WebSocket is done
        if self.state == self.STATE_OPEN:
            self.logger.debug(
                f"WebSocket done, marking connection {self.connection_id} as closed",
                extra={"connection_id": self.connection_id},
            )
            self.state = self.STATE_CLOSED
