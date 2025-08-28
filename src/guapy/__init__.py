"""Guapy - Python implementation of Guacamole WebSocket proxy server.

Guapy is a lightweight, Python-based implementation of the Apache Guacamole
WebSocket proxy server. It provides secure, clientless remote desktop access
through web browsers by implementing the Guacamole protocol and serving as a
bridge between web clients and remote desktop servers.

Key Features:
    - Multi-Protocol Support: RDP, VNC, SSH, and Telnet protocols
    - WebSocket-Based Communication: Real-time, bidirectional communication
    - Token-Based Security: AES-256-CBC encrypted connection tokens
    - Protocol Compliance: Full Apache Guacamole protocol implementation
    - Scalable Architecture: Asynchronous Python implementation for high concurrency
    - RESTful Management API: Health checks, statistics, and monitoring endpoints

Example:
    Basic server setup:

    >>> from guapy import create_server
    >>> from guapy.models import ClientOptions, GuacdOptions
    >>>
    >>> client_options = ClientOptions()
    >>> guacd_options = GuacdOptions(host="127.0.0.1", port=4822)
    >>> server = create_server(client_options, guacd_options)

For more information, visit: https://github.com/Adithya1331/guapy
"""

# Logging best practices for guapy package
#
# - Each module uses logging.getLogger(__name__) for logging.
# To use logging in your application:
# import logging
# logging.basicConfig(level=logging.INFO,
# format='%(asctime)s %(levelname)s %(name)s %(message)s')
#
# For more advanced configuration, see the Python logging documentation.

# Client connection handling
import logging

from .client_connection import ClientConnection
from .config import ConfigManager, get_config
from .crypto import GuacamoleCrypto
from .exceptions import (
    GuacdConnectionError,
    GuapyAuthenticationError,
    GuapyConfigurationError,
    GuapyConnectionError,
    GuapyCryptoError,
    GuapyError,
    GuapyProtocolError,
    GuapyTimeoutError,
    HandshakeError,
    ProtocolParsingError,
    TokenDecryptionError,
    TokenEncryptionError,
    WebSocketConnectionError,
)
from .guacd_client import GuacamoleProtocol, GuacdClient
from .models import (
    ClientOptions,
    ConnectionConfig,
    GuacdOptions,
    ScreenSize,
    TokenData,
)
from .server import GuapyServer, create_server

# Add a NullHandler to the top-level guapy logger to prevent warnings if the application
# does not configure logging
_logger = logging.getLogger("guapy")
_logger.addHandler(logging.NullHandler())

__version__ = "1.0.0"
__author__ = "Adithya"
__email__ = "adithyakokkirala@gmail.com"

__all__ = [
    "ClientConnection",
    "ClientOptions",
    "ConfigManager",
    "ConnectionConfig",
    "GuacamoleCrypto",
    "GuacamoleProtocol",
    "GuacdClient",
    "GuacdConnectionError",
    "GuacdOptions",
    "GuapyAuthenticationError",
    "GuapyConfigurationError",
    "GuapyConnectionError",
    "GuapyCryptoError",
    "GuapyError",
    "GuapyProtocolError",
    "GuapyServer",
    "GuapyTimeoutError",
    "HandshakeError",
    "ProtocolParsingError",
    "ScreenSize",
    "TokenData",
    "TokenDecryptionError",
    "TokenEncryptionError",
    "WebSocketConnectionError",
    "__author__",
    "__email__",
    "__version__",
    "create_server",
    "get_config",
]
