"""Guacamole protocol handling and guacd client implementation."""

import asyncio
import logging
from typing import Optional

from .exceptions import GuacdConnectionError, HandshakeError


class GuacamoleProtocol:
    """Handles Guacamole protocol formatting and parsing."""

    @staticmethod
    def format_instruction(parts: list[str]) -> str:
        """Format instruction parts into Guacamole protocol format.

        Args:
            parts: List of instruction parts

        Returns:
            Formatted Guacamole protocol instruction
        """
        formatted_parts = []
        for part in parts:
            if part is None:
                part = ""
            part_str = str(part)
            formatted_parts.append(f"{len(part_str)}.{part_str}")
        instruction = ",".join(formatted_parts) + ";"
        logger = logging.getLogger(__name__)
        logger.debug(f"Formatted instruction: {instruction}")
        return instruction

    @staticmethod
    def parse_instruction(instruction: str) -> list[str]:
        """Parse a Guacamole protocol instruction into its parts."""
        logger = logging.getLogger(__name__)
        logger.debug(f"Parsing instruction: {instruction}")
        if not instruction.endswith(";"):
            logger.debug("Invalid instruction - missing semicolon")
            return []
        instruction = instruction[:-1]
        parts = []
        for element in instruction.split(","):
            if "." not in element:
                logger.debug(f"Skipping invalid element: {element}")
                continue
            try:
                length_str, content = element.split(".", 1)
                expected_length = int(length_str)
                if len(content) == expected_length:
                    parts.append(content)
                    logger.debug(f"Parsed element: {content}")
                else:
                    remaining = element[len(length_str) + 1 :]
                    if len(remaining) == expected_length:
                        parts.append(remaining)
                        logger.debug(f"Parsed element with dots: {remaining}")
            except ValueError as e:
                logger.debug(f"Failed to parse element: {element}, error: {e}")
                continue
        logger.debug(f"Parsed parts: {parts}")
        return parts

    @staticmethod
    def parse_attribute(attribute: str) -> str:
        """Parse attribute from Guacamole protocol format.

        Args:
            attribute: Attribute in format "length.value"

        Returns:
            Parsed attribute value
        """
        if "." not in attribute:
            return attribute
        return attribute.split(".", 1)[1]


class GuacdClient:
    """Manages TCP connection to guacd daemon with proper protocol handling."""

    STATE_OPENING = 0
    STATE_OPEN = 1
    STATE_CLOSED = 2

    def __init__(
        self,
        client_connection,
    ):
        """Initialize guacd client.

        Args:
            client_connection: Associated client connection
        """
        self.client_connection = client_connection
        self.logger = logging.getLogger(__name__)

        self.state = self.STATE_OPENING
        self.writer = None
        self.reader = None
        self._buffer = ""
        self._activity_check_task = None
        self.last_activity = asyncio.get_event_loop().time()
        self.logger.debug("GuacdClient initialized")

    async def connect(self, host: str, port: int):
        """Establish TCP connection to guacd."""
        try:
            self.logger.debug(f"Connecting to guacd at {host}:{port}")
            self.reader, self.writer = await asyncio.open_connection(host, port)
            self.logger.debug("TCP connection established")
            self.state = self.STATE_OPENING
            await self._start_handshake()
        except Exception as e:
            self.logger.error(f"Failed to connect to guacd: {e}")
            raise GuacdConnectionError(
                f"Failed to connect to guacd: {e}",
                guacd_host=host,
                guacd_port=port,
            ) from e

    async def _start_handshake(self):
        """Initiate handshake with guacd."""
        try:
            protocol = self.client_connection.connection_config.protocol.value
            self.logger.debug("Starting handshake - Step 1")
            self.logger.debug(f"Selecting protocol: {protocol}")
            await self.send_instruction(["select", protocol])
            self.logger.debug("Starting handshake - Step 2")
            self.logger.debug("Waiting for args instruction...")
            instruction = await self._receive_instruction()
            self.logger.debug(f"Received instruction: {instruction}")
            if not instruction:
                self.logger.error("No instruction received")
                raise HandshakeError(
                    "No instruction received during handshake",
                    handshake_phase="select",
                )
            if instruction[0] != "args":
                self.logger.error(f"Expected 'args' instruction, got: {instruction[0]}")
                raise HandshakeError(
                    f"Expected 'args' instruction, got: {instruction[0]}",
                    handshake_phase="args",
                    expected_instruction="args",
                    received_instruction=instruction[0],
                )
            self.logger.debug("Starting handshake - Step 3")
            settings = self.client_connection.connection_config.settings
            width = settings.width
            height = settings.height
            dpi = settings.dpi
            self.logger.debug(f"Sending screen size: {width}x{height}x{dpi}")
            await self.send_instruction(["size", width, height, dpi])
            self.logger.debug("Sending audio support")
            await self.send_instruction(["audio", "audio/L16"])
            self.logger.debug("Sending video support")
            await self.send_instruction(["video"])
            self.logger.debug("Sending image support")
            await self.send_instruction(["image", "image/png", "image/jpeg"])
            self.logger.debug("Starting handshake - Step 4")
            version = instruction[1]
            param_names = instruction[2:]
            params = ["connect", version]
            settings = self.client_connection.connection_config.settings
            for name in param_names:
                attr = name.replace("-", "_")
                value = getattr(settings, attr, "")
                if isinstance(value, bool):
                    value = "true" if value else "false"
                if value is None:
                    value = ""
                params.append(str(value))
            self.logger.debug("Sending connection parameters (dynamic mapping)")
            self.logger.debug(f"Full params list: {params}")
            await self.send_instruction(params)
            self.logger.debug("Starting handshake - Step 5")
            self.logger.debug("Waiting for ready instruction...")
            ready_instruction = await self._receive_instruction()
            self.logger.debug(f"Received instruction: {ready_instruction}")
            if not ready_instruction:
                self.logger.error("No ready instruction received")
                raise HandshakeError(
                    "No ready instruction received during handshake",
                    handshake_phase="ready",
                    expected_instruction="ready",
                )
            if ready_instruction[0] != "ready":
                if ready_instruction[0] == "error":
                    error_msg = (
                        ready_instruction[1]
                        if len(ready_instruction) > 1
                        else "Unknown error"
                    )
                    self.logger.error(f"guacd returned error: {error_msg}")
                    raise HandshakeError(
                        f"guacd error: {error_msg}",
                        handshake_phase="ready",
                        expected_instruction="ready",
                        received_instruction="error",
                    )
                else:
                    self.logger.error(
                        f"Expected 'ready' instruction, got: {ready_instruction[0]}"
                    )
                    raise HandshakeError(
                        f"Expected 'ready' instruction, got: {ready_instruction[0]}",
                        handshake_phase="ready",
                        expected_instruction="ready",
                        received_instruction=ready_instruction[0],
                    )
            connection_id = (
                ready_instruction[1] if len(ready_instruction) > 1 else "unknown"
            )
            self.logger.debug(f"Connection established with ID: {connection_id}")
            self.state = self.STATE_OPEN
            self.logger.debug(
                "Handshake completed successfully - ready for interactive phase"
            )
            self.logger.debug("GuacdClient is now in OPEN state")
        except Exception as e:
            self.logger.error(f"Handshake failed: {e}")
            self.state = self.STATE_CLOSED
            raise ConnectionError(f"Handshake failed: {e}") from e

    async def send_instruction(self, instruction_parts: list[str]):
        """Send a formatted instruction to guacd."""
        if not self.writer:
            self.logger.error("Not connected to guacd")
            raise ConnectionError("Not connected to guacd")
        instruction = GuacamoleProtocol.format_instruction(instruction_parts)
        self.logger.debug(f"Sending raw instruction: {instruction}")
        self.writer.write(instruction.encode())
        await self.writer.drain()
        self.last_activity = asyncio.get_event_loop().time()

    async def send_raw_message(self, message: str):
        """Send a raw message directly to guacd."""
        if not self.writer:
            self.logger.error("Not connected to guacd")
            raise ConnectionError("Not connected to guacd")
        self.logger.debug(f"Sending raw message to guacd: {message}")
        self.writer.write(message.encode())
        await self.writer.drain()
        self.last_activity = asyncio.get_event_loop().time()

    async def _receive_instruction(self) -> Optional[list[str]]:
        self.logger.debug("Waiting for instruction...")
        while ";" not in self._buffer:
            if not self.reader:
                self.logger.error("No reader available")
                return None
            chunk = await self.reader.read(4096)
            if not chunk:
                self.logger.error("Connection closed by server")
                return None
            decoded = chunk.decode()
            self.logger.debug(f"Received raw chunk: {decoded}")
            self._buffer += decoded
            self.last_activity = asyncio.get_event_loop().time()
        instruction_end = self._buffer.index(";")
        instruction = self._buffer[: instruction_end + 1]
        self._buffer = self._buffer[instruction_end + 1 :]
        self.logger.debug(f"Processing instruction: {instruction}")
        parsed = GuacamoleProtocol.parse_instruction(instruction)
        self.logger.debug(f"Parsed instruction parts: {parsed}")
        return parsed

    async def start(self):
        """Start processing guacd messages in an event-driven loop."""
        self.logger.debug("Starting guacd message processing (event-driven)")
        try:
            while self.state == self.STATE_OPEN:
                try:
                    # Add null check for reader
                    if not self.reader:
                        self.logger.debug("No reader available, ending message processing")
                        break
                    
                    # Check if client connection is still open
                    if self.client_connection.state == self.client_connection.STATE_CLOSED:
                        self.logger.debug("Client connection closed, ending guacd message processing")
                        break
                        
                    data = await self.reader.read(4096)
                    if not data:
                        self.logger.debug("guacd connection closed by remote host")
                        break
                    self._buffer += data.decode(errors="replace")
                    self.logger.debug(
                        f"Received guacd data({len(data)} chars):{self._buffer[:120]}"
                    )
                    await self._send_buffer_to_websocket()
                except asyncio.CancelledError:
                    self.logger.info("guacd message loop cancelled")
                    break
        except asyncio.CancelledError:
            self.logger.info("guacd message loop cancelled (outer)")
        except Exception as e:
            self.logger.debug(f"Error in guacd message loop: {e}")
        finally:
            self.logger.debug("guacd message loop ended")
            self.state = self.STATE_CLOSED

    async def _send_buffer_to_websocket(self):
        try:
            while ";" in self._buffer:
                delimiter_pos = self._buffer.index(";")
                instruction = self._buffer[: delimiter_pos + 1]
                self._buffer = self._buffer[delimiter_pos + 1 :]
                parsed = GuacamoleProtocol.parse_instruction(instruction)
                if not parsed:
                    self.logger.debug(
                        f"Skipping invalid instr for WebSocket: {instruction}"
                    )
                    continue
                if self.client_connection.state == self.client_connection.STATE_OPEN:
                    await self.client_connection.send_message(instruction)
                else:
                    self.logger.debug("WebSocket closed, not sending instruction.")
                    break
                try:
                    if (
                        parsed
                        and parsed[0] == "sync"
                        and len(parsed) > 1
                        and self.client_connection.state
                        == self.client_connection.STATE_OPEN
                    ):
                        timestamp = parsed[1]
                        await self.send_instruction(["sync", timestamp])
                        self.logger.debug(f"Sent sync reply with timestamp {timestamp}")
                except Exception as e:
                    self.logger.debug(f"Failed to parse/send sync reply: {e}")
        except Exception as e:
            self.logger.debug(f"Error sending buffer to WebSocket: {e}")

    async def close(self):
        """Close the guacd connection."""
        if self.state != self.STATE_CLOSED:  # Only close if not already closed
            self.logger.debug("Closing guacd connection")
            self.state = self.STATE_CLOSED
            
            if self.writer:
                try:
                    self.writer.close()
                    await self.writer.wait_closed()
                    self.writer = None  # Clear reference after closing
                except Exception as e:
                    self.logger.debug(f"Error closing guacd connection: {e}")  # Changed from error to debug
        else:
            self.logger.debug("GuacdClient already closed")
