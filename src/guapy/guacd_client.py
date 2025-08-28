"""Guacamole protocol handling and guacd client implementation."""

import asyncio
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .client_connection import ClientConnection

from .exceptions import GuacdConnectionError, HandshakeError, ProtocolParsingError
from .filter import ErrorFilter, GuacamoleFilter


class GuacamoleProtocol:
    """Handles Guacamole protocol formatting and parsing with a robust, stateful parser
    that correctly handles all protocol edge cases, including special characters
    and Unicode surrogate pairs.
    """

    @staticmethod
    def format_instruction(parts: list[str]) -> str:
        """Formats instruction parts into the Guacamole protocol string format."""
        formatted_parts = []
        for part in parts:
            part_str = str(part if part is not None else "")
            # The protocol counts Unicode code points, not bytes or UTF-16 characters.
            formatted_parts.append(f"{len(part_str)}.{part_str}")
        return ",".join(formatted_parts) + ";"

    @staticmethod
    def _find_instruction_end(buffer: str) -> int:
        """Finds the end of the first complete Guacamole instruction in the buffer
        by correctly parsing each element's length prefix.

        Returns the index of the terminating semicolon, or -1 if a complete
        instruction is not yet in the buffer.

        Raises ProtocolParsingError on malformed data.
        """
        idx = 0
        while idx < len(buffer):
            # Find the end of the length prefix for the current element
            length_end = buffer.find(".", idx)
            if length_end == -1:
                return -1  # Incomplete: length prefix not fully available

            try:
                # Extract and parse the length of the upcoming element
                length = int(buffer[idx:length_end])
            except ValueError:
                raise ProtocolParsingError(
                    f"Invalid non-numeric length prefix at index {idx}", raw_data=buffer
                )

            # Calculate the full element's end and the terminator's position
            terminator_idx = length_end + 1 + length

            if terminator_idx >= len(buffer):
                return (
                    -1
                )  # Incomplete: element content or terminator not fully available

            terminator = buffer[terminator_idx]

            # If it's a semicolon, we've found the end of the instruction
            if terminator == ";":
                return terminator_idx

            # If it's a comma, this element is valid, so move to the start of the next one
            if terminator == ",":
                idx = terminator_idx + 1
                continue

            # Any other character is a protocol violation
            raise ProtocolParsingError(
                f"Expected ',' or ';' but found '{terminator}' at index {terminator_idx}",
                raw_data=buffer,
            )

        return -1  # No complete instruction found in the buffer

    @staticmethod
    def parse_instruction(instruction: str) -> list[str]:
        """Parses a single, complete, semicolon-terminated Guacamole instruction string.
        This assumes the input string is a valid and complete instruction.
        """
        if not instruction.endswith(";"):
            raise ProtocolParsingError(
                "parse_instruction should only be called on a complete, semicolon-terminated instruction.",
                raw_data=instruction,
            )

        instruction = instruction[:-1]
        if not instruction:  # Handle empty instruction case like "0.;"
            return []

        parts = []
        idx = 0
        while idx < len(instruction):
            length_end = instruction.find(".", idx)
            length = int(instruction[idx:length_end])
            content_start = length_end + 1
            content_end = content_start + length
            parts.append(instruction[content_start:content_end])
            idx = content_end + 1  # Move past the comma to the next element's start

        return parts


class GuacdClient:
    """Manages TCP connection to guacd daemon with proper protocol handling."""

    STATE_OPENING = 0
    STATE_OPEN = 1
    STATE_CLOSED = 2

    def __init__(self, client_connection: "ClientConnection") -> None:
        """Initialize guacd client."""
        self.client_connection = client_connection
        self.logger = logging.getLogger(__name__)
        self.filters: list[GuacamoleFilter] = [ErrorFilter()]
        self.state = self.STATE_OPENING
        self.writer: Optional[asyncio.StreamWriter] = None
        self.reader: Optional[asyncio.StreamReader] = None
        self._buffer = ""
        self.last_activity = asyncio.get_event_loop().time()
        self.logger.debug("GuacdClient initialized")

    async def connect(self, host: str, port: int) -> None:
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

    async def _start_handshake(self) -> None:
        """Initiate handshake with guacd, raising specific exceptions on failure."""
        try:
            if self.client_connection.connection_config is None:
                raise GuacdConnectionError("Connection config is not set")

            protocol = self.client_connection.connection_config.protocol.value
            await self.send_instruction(["select", protocol])

            instruction = await self._receive_instruction()
            if not instruction or instruction[0] != "args":
                raise HandshakeError(
                    "Expected 'args' instruction from guacd",
                    handshake_phase="args",
                    received_instruction=instruction[0] if instruction else "None",
                )

            settings = self.client_connection.connection_config.settings
            await self.send_instruction(
                ["size", str(settings.width), str(settings.height), str(settings.dpi)]
            )
            await self.send_instruction(["audio", "audio/L16"])
            await self.send_instruction(["video"])
            await self.send_instruction(["image", "image/png", "image/jpeg"])

            version = instruction[1]
            param_names = instruction[2:]
            params = ["connect", version]
            for name in param_names:
                attr = name.replace("-", "_")
                value = getattr(settings, attr, "")
                if isinstance(value, bool):
                    value = "true" if value else "false"
                if value is None:
                    value = ""
                params.append(str(value))

            await self.send_instruction(params)

            ready_instruction = await self._receive_instruction()
            if not ready_instruction:
                raise HandshakeError(
                    "No 'ready' instruction received from guacd",
                    handshake_phase="ready",
                )

            self.filters[0].filter(ready_instruction)

            if ready_instruction[0] != "ready":
                raise HandshakeError(
                    f"Expected 'ready' instruction, got: {ready_instruction[0]}",
                    handshake_phase="ready",
                    received_instruction=ready_instruction[0],
                )

            self.state = self.STATE_OPEN
            self.logger.info("Guacd handshake completed successfully.")
        except (ProtocolParsingError, HandshakeError) as e:
            self.state = self.STATE_CLOSED
            self.logger.error(f"Handshake failed due to protocol error: {e}")
            raise
        except Exception as e:
            self.state = self.STATE_CLOSED
            self.logger.error(f"An unexpected error occurred during handshake: {e}")
            raise GuacdConnectionError("Unexpected handshake failure") from e

    async def send_instruction(self, instruction_parts: list[str]) -> None:
        """Sends the instructions to format and then to guacd using send_raw_message"""
        instruction = GuacamoleProtocol.format_instruction(instruction_parts)
        await self.send_raw_message(instruction)

    async def send_raw_message(self, message: str) -> None:
        if not self.writer:
            raise ConnectionError("Not connected to guacd")
        self.writer.write(message.encode())
        await self.writer.drain()
        self.last_activity = asyncio.get_event_loop().time()

    async def _receive_instruction(self) -> Optional[list[str]]:
        """Read from the socket until a complete instruction is buffered, then parse it."""
        while True:
            try:
                instruction_end = GuacamoleProtocol._find_instruction_end(self._buffer)
                if instruction_end != -1:
                    instruction_str = self._buffer[: instruction_end + 1]
                    self._buffer = self._buffer[instruction_end + 1 :]
                    return GuacamoleProtocol.parse_instruction(instruction_str)
            except ProtocolParsingError:
                self.logger.error("Protocol parsing error, closing connection.")
                await self.close()
                raise

            if not self.reader:
                return None
            chunk = await self.reader.read(4096)
            if not chunk:
                self.logger.info(
                    "Guacd connection closed while waiting for instruction."
                )
                return None
            self._buffer += chunk.decode(errors="replace")

    def _apply_filters(self, instruction: list[str]) -> Optional[list[str]]:
        current_instruction: Optional[list[str]] = instruction
        for f in self.filters:
            if current_instruction is None:
                return None
            current_instruction = f.filter(current_instruction)
        return current_instruction

    async def start(self) -> None:
        """Start processing guacd messages in an event-driven loop."""
        self.logger.debug("Starting guacd message processing (event-driven)")
        try:
            while self.state == self.STATE_OPEN:
                try:
                    # Add null check for reader
                    if not self.reader:
                        self.logger.debug(
                            "No reader available, ending message processing"
                        )
                        break

                    # Check if client connection is still open
                    if (
                        self.client_connection.state
                        == self.client_connection.STATE_CLOSED
                    ):
                        self.logger.debug(
                            "Client connection closed, ending guacd message processing"
                        )
                        break

                    data = await self.reader.read(4096)
                    if not data:
                        self.logger.debug("guacd connection closed by remote host")
                        break
                    self._buffer += data.decode(errors="replace")
                    self.logger.debug(
                        f"Received guacd data({len(data)} chars):{self._buffer[:120]}"
                    )
                    await self._process_and_forward_buffer()
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

    async def _process_and_forward_buffer(self) -> None:
        """Parse all complete instructions from buffer, filter them, and forward."""
        while True:
            try:
                instruction_end = GuacamoleProtocol._find_instruction_end(self._buffer)
                if instruction_end == -1:
                    break  # No more complete instructions in buffer
            except ProtocolParsingError:
                self.logger.error(
                    "Protocol parsing error in buffer, closing connection."
                )
                await self.close()
                raise

            instruction_str = self._buffer[: instruction_end + 1]
            self._buffer = self._buffer[instruction_end + 1 :]

            parsed = GuacamoleProtocol.parse_instruction(instruction_str)
            filtered: Optional[list[str]] = self._apply_filters(parsed)

            if filtered:
                final_instruction_str = GuacamoleProtocol.format_instruction(filtered)
                if self.client_connection.state == self.client_connection.STATE_OPEN:
                    await self.client_connection.send_message(final_instruction_str)
                else:
                    break

                if filtered[0] == "sync":
                    await self.send_instruction(["sync", filtered[1]])

    async def close(self) -> None:
        if self.state != self.STATE_CLOSED:
            self.state = self.STATE_CLOSED
            if self.writer:
                try:
                    self.writer.close()
                    await self.writer.wait_closed()
                except Exception as e:
                    self.logger.debug(f"Error closing guacd writer: {e}")
        self.writer = None
        self.reader = None
