"""Tests for config.py module."""

import json
import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from guapy.config import ConfigManager, get_config
from guapy.exceptions import GuapyConfigurationError
from guapy.models import ServerConfig


class TestConfigManager:
    """Test suite for ConfigManager class."""

    @pytest.fixture
    def sample_config_json(self):
        """Sample configuration JSON."""
        return {
            "host": "127.0.0.1",
            "port": 8080,
            "guacd_host": "localhost",
            "guacd_port": 4822,
            "secret_key": "test-key-12345678901234567890123456789012",  # nosec
            "max_connections": 100,
        }

    @pytest.fixture
    def mock_config_file(self, sample_config_json):
        """Create a mock config file."""
        with (
            patch("builtins.open", mock_open(read_data=json.dumps(sample_config_json))),
            patch("pathlib.Path.exists", return_value=True),
        ):
            yield Path("config.json")

    @pytest.fixture
    def config_manager(self, mock_config_file):
        """Create ConfigManager instance."""
        return ConfigManager(mock_config_file)

    def test_init_with_existing_file(self, mock_config_file, sample_config_json):
        """Test initialization with existing config file."""
        manager = ConfigManager(mock_config_file)
        assert manager.config_file == mock_config_file
        assert manager._file_config == sample_config_json

    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent file."""
        with patch("pathlib.Path.exists", return_value=False):
            manager = ConfigManager(Path("nonexistent.json"))
            assert manager.config_file == Path("nonexistent.json")
            assert manager._file_config == {}

    def test_init_with_invalid_json(self):
        """Test initialization with invalid JSON."""
        with (
            patch("builtins.open", mock_open(read_data="invalid json")),
            patch("pathlib.Path.exists", return_value=True),
        ):
            manager = ConfigManager(Path("invalid.json"))
            assert manager._file_config == {}

    def test_load_env_config(self):
        """Test loading config from environment variables."""
        # Setup environment variables using the correct format
        env_vars = {
            "HOST": "0.0.0.0",  # noqa: S104
            "PORT": "8000",
            "GUACD_HOST": "guacd",
            "GUACD_PORT": "4822",
            "SECRET_KEY": "env-key-12345678901234567890123456789012",  # nosec
            "MAX_CONNECTIONS": "50",
        }

        with (
            patch.dict(os.environ, env_vars),
            patch("pathlib.Path.exists", return_value=False),
        ):
            manager = ConfigManager(Path("config.json"))
            # Environment variables should be loaded
            env_config = manager._env_config
            # Check the loaded values
            assert env_config.get("host") == "0.0.0.0"  # noqa: S104
            assert env_config.get("port") == 8000
            assert env_config.get("guacd_host") == "guacd"
            assert env_config.get("guacd_port") == 4822
            assert (
                env_config.get("secret_key")
                == "env-key-12345678901234567890123456789012"
            )
            assert env_config.get("max_connections") == 50

    def test_get_config_with_defaults(self):
        """Test get_config with defaults when no config file exists."""
        with patch("pathlib.Path.exists", return_value=False):
            manager = ConfigManager(Path("config.json"))

            # Should raise error for missing secret_key
            with pytest.raises(GuapyConfigurationError, match="SECRET_KEY is required"):
                manager.get_config()

    def test_get_config_with_file_config(self, config_manager):
        """Test get_config with file configuration."""
        server_config = config_manager.get_config()
        assert isinstance(server_config, ServerConfig)
        assert server_config.host == "127.0.0.1"
        assert server_config.port == 8080
        assert server_config.guacd_host == "localhost"
        assert server_config.guacd_port == 4822
        assert server_config.secret_key == "test-key-12345678901234567890123456789012"
        assert server_config.max_connections == 100

    def test_get_config_with_cli_args(self, config_manager):
        """Test get_config with CLI arguments override."""
        server_config = config_manager.get_config(
            host="0.0.0.0",  # noqa: S104
            port=9000,
            secret_key="cli-key-12345678901234567890123456789012",  # nosec
        )

        assert isinstance(server_config, ServerConfig)
        # CLI args should override file config
        assert server_config.host == "0.0.0.0"  # noqa: S104
        assert server_config.port == 9000
        assert server_config.secret_key == "cli-key-12345678901234567890123456789012"
        # Other values should come from file config
        assert server_config.guacd_host == "localhost"
        assert server_config.guacd_port == 4822

    def test_get_config_with_env_vars(self):
        """Test get_config with environment variables."""
        # Setup environment variables to override some settings
        env_vars = {
            "HOST": "0.0.0.0",  # noqa: S104
            "SECRET_KEY": "env-key-12345678901234567890123456789012",  # nosec
        }

        with (
            patch.dict(os.environ, env_vars),
            patch("pathlib.Path.exists", return_value=False),
        ):
            manager = ConfigManager(Path("config.json"))
            server_config = manager.get_config()

            # Environment variable should override defaults
            assert server_config.host == "0.0.0.0"  # noqa: S104
            assert (
                server_config.secret_key == "env-key-12345678901234567890123456789012"
            )
            # Other values should be defaults
            assert server_config.port == 8080
            assert server_config.guacd_host == "localhost"

    def test_get_config_priority_order(self):
        """Test configuration priority: CLI > env > file > defaults."""
        file_config = {
            "host": "file-host",
            "port": 8081,
            "secret_key": "file-key-12345678901234567890123456789012",  # nosec
        }

        env_vars = {
            "HOST": "env-host",
            "SECRET_KEY": "env-key-12345678901234567890123456789012",  # nosec
        }

        with (
            patch("builtins.open", mock_open(read_data=json.dumps(file_config))),
            patch("pathlib.Path.exists", return_value=True),
            patch.dict(os.environ, env_vars),
        ):
            manager = ConfigManager(Path("config.json"))
            server_config = manager.get_config(
                host="cli-host",
                # No CLI secret_key, should use env
            )

            # CLI should win
            assert server_config.host == "cli-host"
            # Env should override file
            assert (
                server_config.secret_key == "env-key-12345678901234567890123456789012"
            )
            # File should override default
            assert server_config.port == 8081

    def test_invalid_env_var_types(self):
        """Test handling of invalid environment variable types."""
        env_vars = {
            "PORT": "not-a-number",
            "MAX_CONNECTIONS": "also-not-a-number",
        }

        with (
            patch.dict(os.environ, env_vars),
            patch("pathlib.Path.exists", return_value=False),
        ):
            manager = ConfigManager(Path("config.json"))
            # Should ignore invalid values and use defaults
            assert "port" not in manager._env_config
            assert "max_connections" not in manager._env_config


class TestGetConfig:
    """Test suite for get_config function."""

    def test_get_config_function(self):
        """Test get_config convenience function."""
        with patch("guapy.config.get_config_manager") as mock_get_manager:
            mock_manager = mock_get_manager.return_value
            mock_config = ServerConfig(
                host="127.0.0.1",
                port=8080,
                guacd_host="localhost",
                guacd_port=4822,
                secret_key="test-key-12345678901234567890123456789012",
            )
            mock_manager.get_config.return_value = mock_config

            # Call get_config with some args
            result = get_config(host="0.0.0.0", port=9000)  # noqa: S104

            # Should call manager.get_config with the args
            mock_manager.get_config.assert_called_once_with(host="0.0.0.0", port=9000)  # noqa: S104
            assert result == mock_config

    def test_get_config_no_args(self):
        """Test get_config with no arguments."""
        with patch("guapy.config.get_config_manager") as mock_get_manager:
            mock_manager = mock_get_manager.return_value
            mock_config = ServerConfig(
                host="127.0.0.1",
                port=8080,
                guacd_host="localhost",
                guacd_port=4822,
                secret_key="test-key-12345678901234567890123456789012",
            )
            mock_manager.get_config.return_value = mock_config

            # Call get_config with no args
            result = get_config()

            # Should call manager.get_config with no args
            mock_manager.get_config.assert_called_once_with()
            assert result == mock_config
