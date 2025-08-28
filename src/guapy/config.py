"""Configuration management for guapy runnable server.

This module provides helpers for loading
configuration from files, environment variables, and command line arguments.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from .exceptions import GuapyConfigurationError
from .models import ServerConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """Configuration manager for guapy server application."""

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize ConfigManager.

        Args:
            config_file: Path to configuration file, defaults to "config.json"
        """
        self.config_file = config_file or Path("config.json")
        self._file_config: dict[str, Any] = {}
        self._env_config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file and environment."""
        self._load_file_config()
        self._load_env_config()

    def _load_file_config(self) -> None:
        """Load configuration from JSON file."""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    self._file_config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
                self._file_config = {}
        else:
            logger.debug(f"Config file {self.config_file} not found")

    def _load_env_config(self) -> None:
        """Load configuration from environment variables."""
        env_mapping = {
            "HOST": "host",
            "PORT": "port",
            "GUACD_HOST": "guacd_host",
            "GUACD_PORT": "guacd_port",
            "SECRET_KEY": "secret_key",
            "ALLOW_ORIGIN": "allow_origin",
            "MAX_CONNECTIONS": "max_connections",
            "CONNECTION_TIMEOUT": "connection_timeout",
        }

        for env_var, config_key in env_mapping.items():
            value: Optional[str] = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                processed_value: Any = value
                if config_key in [
                    "port",
                    "guacd_port",
                    "max_connections",
                    "connection_timeout",
                ]:
                    try:
                        processed_value = int(value)
                    except ValueError:
                        logger.warning(f"Invalid integer value for {env_var}: {value}")
                        continue

                self._env_config[config_key] = processed_value

    def get_config(self, **cli_args: Any) -> ServerConfig:
        """Get final configuration with priority.

        CLI args > env vars > config file > defaults.

        Args:
            **cli_args: Command line arguments to override other sources

        Returns:
            ServerConfig instance with resolved configuration
        """
        # Start with defaults
        config_dict: dict[str, Any] = {
            "host": "127.0.0.1",
            "port": 8080,
            "guacd_host": "localhost",
            "guacd_port": 4822,
            "allow_origin": "*",
            "max_connections": 100,
            "connection_timeout": 300,
        }

        # Apply file config
        config_dict.update(self._file_config)

        # Apply environment config
        config_dict.update(self._env_config)

        # Apply CLI arguments (remove None values)
        cli_config = {k: v for k, v in cli_args.items() if v is not None}
        config_dict.update(cli_config)

        # Validate required fields
        if not config_dict.get("secret_key"):
            raise GuapyConfigurationError("SECRET_KEY is required but not provided")

        # Only pass fields that are actually in ServerConfig
        from .models import ServerConfig

        allowed_fields = set(ServerConfig.model_fields.keys())
        filtered_config = {k: v for k, v in config_dict.items() if k in allowed_fields}
        return ServerConfig(**filtered_config)


# Default configuration manager instance
_default_manager = None


def get_config_manager(config_file: Optional[Path] = None) -> ConfigManager:
    """Get the default configuration manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ConfigManager(config_file)
    return _default_manager


def get_config(**cli_args: Any) -> ServerConfig:
    """Convenience function to get configuration using the default manager.

    Args:
        **cli_args: Command line arguments to override other sources

    Returns:
        ServerConfig instance
    """
    manager = get_config_manager()
    return manager.get_config(**cli_args)
