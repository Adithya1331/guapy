"""Tests for cli.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from guapy.cli import app, run
from guapy.models import ServerConfig


@pytest.fixture
def cli_runner():
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_server():
    """Create mock server for testing."""
    server = AsyncMock()
    server.start = AsyncMock()
    return server


@pytest.fixture
def mock_create_server():
    """Mock create_server function."""
    with patch("guapy.cli.create_server") as mock:
        mock.return_value = AsyncMock()
        yield mock


@pytest.fixture
def mock_get_config():
    """Mock get_config function."""
    with patch("guapy.cli.get_config") as mock:
        server_config = MagicMock(spec=ServerConfig)
        server_config.host = "127.0.0.1"
        server_config.port = 8080
        server_config.guacd_host = "127.0.0.1"
        server_config.guacd_port = 4822
        server_config.secret_key = "test-key-from-config"
        server_config.max_connections = 100
        mock.return_value = server_config
        yield mock


class TestCLI:
    """Test suite for CLI functionality."""

    def test_app_exists(self):
        """Test that Typer app exists."""
        assert isinstance(app, typer.Typer)

    def test_run_function_exists(self):
        """Test that run function exists."""
        assert callable(run)

    @patch("uvicorn.run")
    @patch("guapy.cli.create_server")
    def test_run_with_defaults(
        self, mock_create_server, mock_uvicorn_run, mock_get_config
    ):
        """Test run command with default options."""
        # Call run function with default values (None for optional params)
        run(
            host=None,
            port=None,
            guacd_host=None,
            guacd_port=None,
            secret_key=None,
            max_connections=None,
            crypt_cypher="AES-256-CBC",
            inactivity_time=10000,
            config_file=None,
            log_level="debug",
        )

        # Check that get_config was called with empty kwargs
        # (all None values filtered out)
        mock_get_config.assert_called_once_with()

        # Check that server was created with ClientOptions and GuacdOptions
        mock_create_server.assert_called_once()

        # Check the arguments to create_server
        args, kwargs = mock_create_server.call_args
        client_options, guacd_options = args

        # Validate ClientOptions
        assert client_options.crypt.cypher == "AES-256-CBC"
        assert client_options.crypt.key == "test-key-from-config"
        assert client_options.max_inactivity_time == 10000

        # Validate GuacdOptions
        assert guacd_options.host == "127.0.0.1"
        assert guacd_options.port == 4822

        # Check that uvicorn.run was called with the server app
        mock_uvicorn_run.assert_called_once()
        uvicorn_kwargs = mock_uvicorn_run.call_args.kwargs
        assert uvicorn_kwargs["host"] == "127.0.0.1"
        assert uvicorn_kwargs["port"] == 8080

    @patch("uvicorn.run")
    @patch("guapy.cli.create_server")
    def test_run_with_custom_options(
        self, mock_create_server, mock_uvicorn_run, mock_get_config
    ):
        """Test run command with custom options."""
        # Define custom options
        custom_options = {
            "host": "127.0.0.1",
            "port": 8000,
            "guacd_host": "custom-guacd",
            "guacd_port": 5000,
            "secret_key": "test-key",
            "max_connections": 50,
            "crypt_cypher": "AES-128-CBC",
        }

        # Call run function with custom options
        run(
            host=custom_options["host"],
            port=custom_options["port"],
            guacd_host=custom_options["guacd_host"],
            guacd_port=custom_options["guacd_port"],
            secret_key=custom_options["secret_key"],
            max_connections=custom_options["max_connections"],
            crypt_cypher=custom_options["crypt_cypher"],
            inactivity_time=10000,
            config_file=None,
            log_level="debug",
        )

        # Check that get_config was called with custom options
        mock_get_config.assert_called_once()
        call_kwargs = mock_get_config.call_args.kwargs
        assert call_kwargs.get("host") == custom_options["host"]
        assert call_kwargs.get("port") == custom_options["port"]
        assert call_kwargs.get("guacd_host") == custom_options["guacd_host"]
        assert call_kwargs.get("guacd_port") == custom_options["guacd_port"]
        assert call_kwargs.get("secret_key") == custom_options["secret_key"]
        assert call_kwargs.get("max_connections") == custom_options["max_connections"]

        # Check that server was created
        mock_create_server.assert_called_once()

        # Check the arguments to create_server
        args, kwargs = mock_create_server.call_args
        client_options, guacd_options = args

        # Validate ClientOptions
        assert client_options.crypt.cypher == "AES-128-CBC"
        assert client_options.crypt.key == "test-key-from-config"
        assert client_options.max_inactivity_time == 10000

        # Validate GuacdOptions
        assert guacd_options.host == "127.0.0.1"
        assert guacd_options.port == 4822

        # Check that uvicorn.run was called
        mock_uvicorn_run.assert_called_once()

    def test_cli_help(self, cli_runner):
        """Test CLI help text."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Guapy:" in result.output

    def test_cli_run_command(self, cli_runner):
        """Test CLI run command."""
        with (
            patch("guapy.cli.get_config") as mock_get_config,
            patch("guapy.cli.create_server") as mock_create_server,
            patch("uvicorn.run") as mock_uvicorn_run,
        ):
            # Setup mocks
            server_config = MagicMock(spec=ServerConfig)
            server_config.host = "127.0.0.1"
            server_config.port = 8080
            server_config.guacd_host = "127.0.0.1"
            server_config.guacd_port = 4822
            server_config.secret_key = "test-key-from-config"
            mock_get_config.return_value = server_config

            # Run command with default options
            result = cli_runner.invoke(app, ["run"])
            assert result.exit_code == 0

            # Verify the calls
            mock_get_config.assert_called_once()
            mock_create_server.assert_called_once()
            mock_uvicorn_run.assert_called_once()

    def test_cli_run_with_options(self, cli_runner):
        """Test CLI run command with options."""
        with (
            patch("guapy.cli.get_config") as mock_get_config,
            patch("guapy.cli.create_server") as mock_create_server,
            patch("uvicorn.run") as mock_uvicorn_run,
        ):
            # Setup mocks
            server_config = MagicMock(spec=ServerConfig)
            server_config.host = "127.0.0.1"
            server_config.port = 8080
            server_config.guacd_host = "127.0.0.1"
            server_config.guacd_port = 4822
            server_config.secret_key = "test-key-from-config"
            mock_get_config.return_value = server_config

            # Run command with options
            result = cli_runner.invoke(
                app,
                [
                    "run",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                    "--guacd-host",
                    "custom-guacd",
                    "--guacd-port",
                    "5000",
                    "--secret-key",
                    "test-key",
                    "--max-connections",
                    "50",
                    "--crypt-cypher",
                    "AES-128-CBC",
                ],
            )
            assert result.exit_code == 0

            # Verify get_config was called with the CLI options
            mock_get_config.assert_called_once()
            call_kwargs = mock_get_config.call_args.kwargs
            assert call_kwargs.get("host") == "127.0.0.1"
            assert call_kwargs.get("port") == 8000
            assert call_kwargs.get("guacd_host") == "custom-guacd"
            assert call_kwargs.get("guacd_port") == 5000
            assert call_kwargs.get("secret_key") == "test-key"
            assert call_kwargs.get("max_connections") == 50

            # Verify the other functions were called
            mock_create_server.assert_called_once()
            mock_uvicorn_run.assert_called_once()
