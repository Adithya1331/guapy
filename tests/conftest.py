"""Test configuration and shared fixtures for guapy test suite.

This module provides pytest fixtures and configuration for comprehensive testing
of the guapy library. It includes fixtures for mocking external dependencies,
creating test data, and setting up test environments.
"""

import asyncio
import json
import logging
import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient

from guapy import (
    ClientOptions,
    ConnectionConfig,
    GuacamoleCrypto,
    GuacdClient,
    GuacdOptions,
    GuapyServer,
    ScreenSize,
    TokenData,
)
from guapy.models import ConnectionSettings, ConnectionType, CryptConfig


# Configure logging for tests
@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """Configure logging for test runs."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Suppress verbose logging from dependencies during tests
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


# Temporary directory fixtures
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_config_file(temp_dir: Path) -> Path:
    """Create a temporary config file for testing."""
    config_file = temp_dir / "test_config.json"
    test_config = {
        "server": {
            "host": "localhost",
            "port": 8080,
        },
        "guacd": {
            "host": "127.0.0.1",
            "port": 4822,
        },
        "crypto": {
            "cipher": "AES-256-CBC",
            "key": "0123456789abcdef0123456789abcdef",
        },
    }
    config_file.write_text(json.dumps(test_config, indent=2))
    return config_file


# Cryptographic fixtures
@pytest.fixture
def test_encryption_key() -> str:
    """Provide a test encryption key for AES-256-CBC."""
    return "0123456789abcdef0123456789abcdef"


@pytest.fixture
def test_crypto(test_encryption_key: str) -> GuacamoleCrypto:
    """Create a GuacamoleCrypto instance for testing."""
    return GuacamoleCrypto("AES-256-CBC", test_encryption_key)


@pytest.fixture
def sample_token_data() -> TokenData:
    """Create sample token data for testing."""
    return TokenData(
        connection_id="test-conn-123",
        protocol="rdp",
        hostname="test.example.com",
        port=3389,
        username="testuser",
        password="testpass",
        width=1920,
        height=1080,
        dpi=96,
    )


# Model fixtures
@pytest.fixture
def screen_size() -> ScreenSize:
    """Create a standard screen size for testing."""
    return ScreenSize(width=1920, height=1080, dpi=96)


@pytest.fixture
def client_options() -> ClientOptions:
    """Create standard client options for testing."""
    return ClientOptions(crypt=CryptConfig(key="test-encryption-key-1234567890ab"))


@pytest.fixture
def guacd_options() -> GuacdOptions:
    """Create standard guacd options for testing."""
    return GuacdOptions(
        host="127.0.0.1",
        port=4822,
    )


@pytest.fixture
def connection_config() -> ConnectionConfig:
    """Create a test connection configuration."""
    return ConnectionConfig(
        connection_id="test-conn-123",
        protocol=ConnectionType.RDP,
        hostname="test.example.com",
        port=3389,
        username="testuser",
        password="testpass",
        width=1920,
        height=1080,
        dpi=96,
    )


@pytest.fixture
def connection_settings() -> ConnectionSettings:
    """Create test connection settings."""
    return ConnectionSettings(
        hostname="test.example.com",
        port=3389,
        username="testuser",
        password="testpass",
        domain="TEST",
        security="any",
        ignore_cert=True,
    )


# Server fixtures
@pytest.fixture
def guapy_server(
    client_options: ClientOptions, guacd_options: GuacdOptions
) -> GuapyServer:
    """Create a GuapyServer instance for testing."""
    return GuapyServer(
        client_options=client_options,
        guacd_options=guacd_options,
    )


@pytest.fixture
def test_client(guapy_server: GuapyServer) -> TestClient:
    """Create a FastAPI test client."""
    return TestClient(guapy_server.app)


# Mock fixtures for external dependencies
@pytest.fixture
def mock_websocket() -> MagicMock:
    """Create a mock WebSocket for testing."""
    mock_ws = MagicMock(spec=WebSocket)
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


@pytest.fixture
def mock_guacd_client() -> MagicMock:
    """Create a mock GuacdClient for testing."""
    mock_client = MagicMock(spec=GuacdClient)
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.send_instruction = AsyncMock()
    mock_client.receive_instruction = AsyncMock(return_value="5.ready;")
    mock_client.is_connected = True
    return mock_client


@pytest.fixture
def mock_asyncio_open_connection():
    """Mock asyncio.open_connection for guacd testing."""
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.write = MagicMock()
    mock_writer.drain = AsyncMock()
    mock_writer.close = MagicMock()
    mock_writer.wait_closed = AsyncMock()

    with patch(
        "asyncio.open_connection", return_value=(mock_reader, mock_writer)
    ) as mock_conn:
        yield mock_conn, mock_reader, mock_writer


# Environment variable fixtures
@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """Mock environment variables for testing."""
    env_vars = {
        "GUAPY_HOST": "127.0.0.1",  # Use localhost instead of binding to all interfaces
        "GUAPY_PORT": "8080",
        "GUACD_HOST": "127.0.0.1",
        "GUACD_PORT": "4822",
        "GUAPY_SECRET_KEY": "test-secret-key-123",
        "GUAPY_DEBUG": "true",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield


# Async event loop fixture
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Parameterized test data fixtures
@pytest.fixture(
    params=[
        ConnectionType.RDP,
        ConnectionType.VNC,
        ConnectionType.SSH,
        ConnectionType.TELNET,
    ]
)
def connection_type(request) -> ConnectionType:
    """Parameterized connection types for testing."""
    return request.param


@pytest.fixture(
    params=[
        (1024, 768, 96),
        (1920, 1080, 96),
        (2560, 1440, 144),
        (3840, 2160, 192),
    ]
)
def screen_dimensions(request) -> tuple[int, int, int]:
    """Parameterized screen dimensions for testing."""
    return request.param


@pytest.fixture(
    params=[
        ("", False),  # Empty string
        ("test", False),  # Short string
        ("a" * 31, False),  # 31 bytes
        ("a" * 32, True),  # 32 bytes (valid)
        ("a" * 33, False),  # 33 bytes
    ]
)
def encryption_key_data(request) -> tuple[str, bool]:
    """Parameterized encryption key data (key, is_valid)."""
    return request.param


# Protocol instruction fixtures
@pytest.fixture
def guacamole_instructions() -> dict[str, str]:
    """Sample Guacamole protocol instructions for testing."""
    return {
        "select": "6.select,13.image/jpeg;",
        "ready": "5.ready;",
        "sync": "4.sync,10.1234567890;",
        "mouse": "5.mouse,1.0,1.0,1.1;",
        "key": "3.key,2.65,1.1;",
        "clipboard": "9.clipboard,11.sample text;",
        "size": "4.size,4.1920,4.1080;",
        "args": "4.args,3.rdp;",
        "connect": "7.connect,3.rdp,13.test.example,4.3389,8.testuser,8.testpass;",
        "disconnect": "10.disconnect;",
        "error": "5.error,26.Connection could not be made,5.02000;",
    }


# Error simulation fixtures
@pytest.fixture
def connection_error_scenarios():
    """Different connection error scenarios for testing."""
    return [
        {
            "name": "connection_timeout",
            "exception": asyncio.TimeoutError,
            "message": "Connection timed out",
        },
        {
            "name": "connection_refused",
            "exception": ConnectionRefusedError,
            "message": "Connection refused",
        },
        {
            "name": "network_unreachable",
            "exception": OSError,
            "message": "Network is unreachable",
        },
    ]


# Test data generators
@pytest.fixture
def generate_large_token_data():
    """Generate large token data for stress testing."""

    def _generate(size: int = 1000) -> TokenData:
        return TokenData(
            connection_id=f"large-conn-{'x' * size}",
            protocol="rdp",
            hostname="test.example.com",
            port=3389,
            username="x" * size,
            password="y" * size,
            width=1920,
            height=1080,
            dpi=96,
        )

    return _generate


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_logging():
    """Ensure clean logging state for each test."""
    yield
    # Clear any handlers that might have been added during tests
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)


@pytest.fixture
def isolated_config_manager(temp_dir: Path):
    """Create an isolated ConfigManager for testing."""
    config_file = temp_dir / "isolated_config.json"
    test_config = {
        "server": {"host": "localhost", "port": 8080},
        "guacd": {"host": "127.0.0.1", "port": 4822},
    }
    config_file.write_text(json.dumps(test_config))

    from src.guapy.config import ConfigManager

    return ConfigManager(config_file)


# Performance testing fixtures
@pytest.fixture
def performance_metrics():
    """Track performance metrics during tests."""
    import time

    metrics = {"start_time": time.time(), "operations": []}

    def add_operation(name: str, duration: float):
        metrics["operations"].append({"name": name, "duration": duration})

    metrics["add_operation"] = add_operation
    yield metrics

    # Log performance summary
    total_time = time.time() - metrics["start_time"]
    print(f"\nTest completed in {total_time:.3f}s")
    for op in metrics["operations"]:
        print(f"  {op['name']}: {op['duration']:.3f}s")


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "crypto: mark test as cryptographic test")
    config.addinivalue_line("markers", "network: mark test as network dependent")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location or content."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark slow tests
        if "slow" in item.name or "stress" in item.name:
            item.add_marker(pytest.mark.slow)

        # Mark crypto tests
        if "crypto" in str(item.fspath) or "encrypt" in item.name:
            item.add_marker(pytest.mark.crypto)

        # Mark network tests
        if "network" in item.name or "connection" in item.name:
            item.add_marker(pytest.mark.network)
