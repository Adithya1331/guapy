"""Pydantic models for configuration and data validation."""

import logging
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from .exceptions import GuapyConfigurationError


class ConnectionType(str, Enum):
    """Supported connection types."""

    RDP = "rdp"
    VNC = "vnc"
    SSH = "ssh"
    TELNET = "telnet"


class ScreenSize(BaseModel):
    """Screen size configuration."""

    width: int = 1024
    height: int = 768
    dpi: int = 96

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class CryptConfig(BaseModel):
    """Encryption configuration."""

    cypher: str = "AES-256-CBC"
    key: str

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class ConnectionSettings(BaseModel):
    """Connection settings for remote desktop protocols (only those sent by guacd)."""

    hostname: Optional[str] = None
    port: Optional[int] = None
    domain: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    dpi: Optional[int] = None
    initial_program: Optional[str] = None
    color_depth: Optional[int] = None
    disable_audio: Optional[bool] = None
    enable_printing: Optional[bool] = None
    printer_name: Optional[str] = None
    enable_drive: Optional[bool] = None
    drive_name: Optional[str] = None
    drive_path: Optional[str] = None
    create_drive_path: Optional[bool] = None
    disable_download: Optional[bool] = None
    disable_upload: Optional[bool] = None
    console: Optional[bool] = None
    console_audio: Optional[bool] = None
    server_layout: Optional[str] = None
    security: Optional[str] = None
    ignore_cert: Optional[bool] = None
    disable_auth: Optional[bool] = None
    remote_app: Optional[str] = None
    remote_app_dir: Optional[str] = None
    remote_app_args: Optional[str] = None
    static_channels: Optional[str] = None
    client_name: Optional[str] = None
    enable_wallpaper: Optional[bool] = None
    enable_theming: Optional[bool] = None
    enable_font_smoothing: Optional[bool] = None
    enable_full_window_drag: Optional[bool] = None
    enable_desktop_composition: Optional[bool] = None
    enable_menu_animations: Optional[bool] = None
    disable_bitmap_caching: Optional[bool] = None
    disable_offscreen_caching: Optional[bool] = None
    disable_glyph_caching: Optional[bool] = None
    preconnection_id: Optional[str] = None
    preconnection_blob: Optional[str] = None
    timezone: Optional[str] = None
    enable_sftp: Optional[bool] = None
    sftp_hostname: Optional[str] = None
    sftp_host_key: Optional[str] = None
    sftp_port: Optional[int] = None
    sftp_username: Optional[str] = None
    sftp_password: Optional[str] = None
    sftp_private_key: Optional[str] = None
    sftp_passphrase: Optional[str] = None
    sftp_directory: Optional[str] = None
    sftp_root_directory: Optional[str] = None
    sftp_server_alive_interval: Optional[int] = None
    sftp_disable_download: Optional[bool] = None
    sftp_disable_upload: Optional[bool] = None
    recording_path: Optional[str] = None
    recording_name: Optional[str] = None
    recording_exclude_output: Optional[bool] = None
    recording_exclude_mouse: Optional[bool] = None
    recording_exclude_touch: Optional[bool] = None
    recording_include_keys: Optional[bool] = None
    create_recording_path: Optional[bool] = None
    resize_method: Optional[str] = None
    enable_audio_input: Optional[bool] = None
    enable_touch: Optional[bool] = None
    read_only: Optional[bool] = None
    gateway_hostname: Optional[str] = None
    gateway_port: Optional[int] = None
    gateway_domain: Optional[str] = None
    gateway_username: Optional[str] = None
    gateway_password: Optional[str] = None
    load_balance_info: Optional[str] = None
    disable_copy: Optional[bool] = None
    disable_paste: Optional[bool] = None
    wol_send_packet: Optional[bool] = None
    wol_mac_addr: Optional[str] = None
    wol_broadcast_addr: Optional[str] = None
    wol_udp_port: Optional[int] = None
    wol_wait_time: Optional[int] = None
    force_lossless: Optional[bool] = None
    normalize_clipboard: Optional[bool] = None

    class Config:
        """Pydantic configuration."""

        extra = "allow"

    def get_setting(self, name: str) -> Any:
        """Get setting value by name."""
        if hasattr(self, name):
            return getattr(self, name)
        return None

    def set_setting(self, name: str, value: Any) -> None:
        """Set setting value by name."""
        setattr(self, name, value)


class TokenData(BaseModel):
    """Data structure for encrypted connection tokens."""

    connection: dict[str, Any]

    @classmethod
    def from_token(cls, token_data: Any) -> "TokenData":
        """Create from decrypted token data."""
        logger = logging.getLogger(__name__)
        logger.debug(f"Raw token data: {token_data}", extra={"token_data": token_data})
        try:
            if not isinstance(token_data, dict):
                logger.error(
                    f"Token data is not a dictionary: {type(token_data)}",
                    extra={"token_data": token_data},
                )
                raise GuapyConfigurationError(
                    "Token data must be a dictionary",
                    config_section="token",
                    config_key="data",
                    expected_type="dict",
                    actual_value=type(token_data).__name__,
                )

            if "connection" not in token_data:
                logger.error(
                    f"Missing 'connection' key in token data: {token_data.keys()}",
                    extra={"token_data": token_data},
                )
                raise GuapyConfigurationError(
                    "Token data missing 'connection' field",
                    config_section="token",
                    config_key="connection",
                    expected_type="dict",
                    actual_value=None,
                )

            return cls(connection=token_data["connection"])
        except GuapyConfigurationError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to parse token data: {e}", extra={"token_data": token_data}
            )
            raise GuapyConfigurationError(
                f"Invalid token format: {e}",
                config_section="token",
                config_key="format",
            ) from e

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class ConnectionConfig(BaseModel):
    """Configuration for a guacd connection."""

    protocol: ConnectionType
    settings: ConnectionSettings
    query_parameters: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_token(
        cls, token_data: dict[str, Any], query_params: dict[str, str]
    ) -> "ConnectionConfig":
        """Create from token data and query parameters."""
        logger = logging.getLogger(__name__)
        logger.debug(
            f"Creating ConnectionConfig from token data: {token_data}",
            extra={"token_data": token_data},
        )
        try:
            data = TokenData.from_token(token_data)
            if "type" not in data.connection:
                logger.error(
                    f"Missing 'type' in connection data: {data.connection.keys()}",
                    extra={"token_data": token_data},
                )
                raise GuapyConfigurationError(
                    "Connection type not specified in token",
                    config_section="connection",
                    config_key="type",
                    expected_type="string",
                    actual_value=None,
                )

            if "settings" not in data.connection:
                logger.error(
                    f"Missing 'settings' in conn data: {data.connection.keys()}",
                    extra={"token_data": token_data},
                )
                raise GuapyConfigurationError(
                    "Connection settings not specified in token",
                    config_section="connection",
                    config_key="settings",
                    expected_type="dict",
                    actual_value=None,
                )

            return cls(
                protocol=data.connection["type"],
                settings=ConnectionSettings(**data.connection["settings"]),
                query_parameters=query_params,
            )
        except GuapyConfigurationError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to create ConnectionConfig: {e}",
                extra={"token_data": token_data},
            )
            raise GuapyConfigurationError(
                f"from_token: {e}", config_section="connection", config_key="format"
            ) from e

    @property
    def parameters(self) -> dict[str, Any]:
        """Get connection parameters for guacd handshake."""
        # Start with core parameters that are always needed
        params = {
            "hostname": self.settings.hostname,
            "port": self.settings.port,
            "username": self.settings.username,
            "password": self.settings.password,
        }

        if self.protocol == ConnectionType.SSH:
            # SSH specific parameters
            params.update(
                {
                    "hostname": self.settings.hostname,
                    "port": self.settings.port or 22,
                    "username": self.settings.username,
                    "password": self.settings.password,
                    "font-name": "monospace",
                    "font-size": "12",
                    "color-scheme": "gray-black",
                    "enable-sftp": "true",
                }
            )
        elif self.protocol == ConnectionType.RDP:
            # RDP specific parameters
            params.update(
                {
                    "hostname": self.settings.hostname,
                    "port": self.settings.port or 3389,
                    "username": self.settings.username,
                    "password": self.settings.password,
                    "domain": self.settings.domain,
                    "security": self.settings.security,
                    "enable-drive": str(self.settings.enable_drive).lower()
                    if self.settings.enable_drive is not None
                    else None,
                    "drive-path": self.settings.drive_path,
                }
            )

        # Remove None values
        return {k: v for k, v in params.items() if v is not None}


class GuacdOptions(BaseModel):
    """Configuration for guacd daemon connection."""

    host: str = "127.0.0.1"
    port: int = 4822

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class ClientOptions(BaseModel):
    """Client configuration options."""

    max_inactivity_time: int = 10000  # milliseconds
    crypt: CryptConfig

    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"],
        description="List of allowed origins for CORS. Use ['*'] only for development.",
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Whether to allow credentials in CORS requests"
    )
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="List of allowed HTTP methods for CORS",
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["*"], description="List of allowed headers for CORS"
    )

    @classmethod
    def create_with_development_cors(
        cls, crypt: CryptConfig, **kwargs: Any
    ) -> "ClientOptions":
        """Create ClientOptions with development-friendly CORS settings.

        WARNING: Only use in development environments!
        """
        return cls(
            crypt=crypt,
            cors_allow_origins=["*"],  # Allow all origins for development
            cors_allow_credentials=True,
            cors_allow_methods=["*"],
            cors_allow_headers=["*"],
            **kwargs,
        )

    @classmethod
    def create_with_production_cors(
        cls, crypt: CryptConfig, allowed_origins: list[str], **kwargs: Any
    ) -> "ClientOptions":
        """Create ClientOptions with production-safe CORS settings."""
        return cls(
            crypt=crypt,
            cors_allow_origins=allowed_origins,
            cors_allow_credentials=True,
            cors_allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            cors_allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
            **kwargs,
        )

    # Default connection settings for each protocol type
    connection_default_settings: dict[ConnectionType, dict[str, object]] = Field(
        default_factory=lambda: {
            ConnectionType.RDP: {
                "args": "connect",
                "port": "3389",
                "width": 1024,
                "height": 768,
                "dpi": 96,
            },
            ConnectionType.VNC: {
                "args": "connect",
                "port": "5900",
                "width": 1024,
                "height": 768,
                "dpi": 96,
            },
            ConnectionType.SSH: {
                "args": "connect",
                "port": 22,
                "width": 1024,
                "height": 768,
                "dpi": 96,
            },
            ConnectionType.TELNET: {
                "args": "connect",
                "port": 23,
                "width": 1024,
                "height": 768,
                "dpi": 96,
            },
        }
    )

    # Settings that can be passed unencrypted in query parameters
    allowed_unencrypted_connection_settings: dict[ConnectionType, list[str]] = Field(
        default_factory=lambda: {
            ConnectionType.RDP: ["width", "height", "dpi"],
            ConnectionType.VNC: ["width", "height", "dpi"],
            ConnectionType.SSH: [
                "color-scheme",
                "font-name",
                "font-size",
                "width",
                "height",
                "dpi",
            ],
            ConnectionType.TELNET: [
                "color-scheme",
                "font-name",
                "font-size",
                "width",
                "height",
                "dpi",
            ],
        }
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        arbitrary_types_allowed = True


class ServerConfig(BaseModel):
    """Server configuration for guapy."""

    host: str = "127.0.0.1"
    port: int = 8080
    guacd_host: str = "127.0.0.1"
    guacd_port: int = 4822
    secret_key: str
    max_connections: int = 100
    allow_origin: str = "*"
    connection_timeout: int = 300

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
