"""Tests for guapy.__init__ module.

This module tests the package initialization, version information,
and import functionality.
"""

import sys
from unittest import mock

import guapy as guapy


class TestPackageInitialization:
    """Test package initialization and metadata."""

    def test_package_version(self):
        """Test that package version is properly defined."""
        assert hasattr(guapy, "__version__")
        assert isinstance(guapy.__version__, str)
        assert guapy.__version__ == "1.0.0"

    def test_package_author(self):
        """Test that package author is properly defined."""
        assert hasattr(guapy, "__author__")
        assert isinstance(guapy.__author__, str)
        assert guapy.__author__ == "Adithya"

    def test_package_email(self):
        """Test that package email is properly defined."""
        assert hasattr(guapy, "__email__")
        assert isinstance(guapy.__email__, str)
        assert guapy.__email__ == "adithyakokkirala@gmail.com"

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        expected_exports = {
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
        }

        assert hasattr(guapy, "__all__")
        assert isinstance(guapy.__all__, list)
        assert set(guapy.__all__) == expected_exports

    def test_imports_available(self):
        """Test that all exports are actually importable."""
        for item in guapy.__all__:
            assert hasattr(guapy, item), f"Export '{item}' not available in module"

    def test_null_handler_configured(self):
        """Test that NullHandler is properly configured to prevent warnings."""
        import logging
        import sys
        from importlib import reload

        import guapy  # Import guapy to trigger the logging setup  # noqa: F401

        # Force reload to ensure handler is added
        if "guapy" in sys.modules:
            reload(sys.modules["guapy"])

        logger = logging.getLogger("guapy")

        # Check that at least one handler is a NullHandler
        null_handlers = [
            h for h in logger.handlers if isinstance(h, logging.NullHandler)
        ]
        assert len(null_handlers) >= 1, "NullHandler not configured"


class TestImportStructure:
    """Test the import structure and dependencies."""

    def test_core_classes_importable(self):
        """Test that core classes can be imported successfully."""
        from guapy import (
            ClientConnection,
            ClientOptions,
            GuacamoleCrypto,
            GuacdClient,
            GuapyServer,
        )

        # Verify classes are actual classes
        assert isinstance(ClientConnection, type)
        assert isinstance(ClientOptions, type)
        assert isinstance(GuacamoleCrypto, type)
        assert isinstance(GuacdClient, type)
        assert isinstance(GuapyServer, type)

    def test_model_classes_importable(self):
        """Test that model classes can be imported successfully."""
        from guapy import (
            ConnectionConfig,
            GuacdOptions,
            ScreenSize,
            TokenData,
        )

        # Verify classes are actual classes
        assert isinstance(ConnectionConfig, type)
        assert isinstance(GuacdOptions, type)
        assert isinstance(ScreenSize, type)
        assert isinstance(TokenData, type)

    def test_exception_classes_importable(self):
        """Test that exception classes can be imported successfully."""
        from guapy import (
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

        # Verify they are exception classes
        exceptions = [
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
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, Exception)

    def test_utility_functions_importable(self):
        """Test that utility functions can be imported successfully."""
        from guapy import create_server, get_config

        # Verify they are callable
        assert callable(create_server)
        assert callable(get_config)

    def test_config_manager_importable(self):
        """Test that ConfigManager can be imported successfully."""
        from guapy import ConfigManager

        assert isinstance(ConfigManager, type)

    def test_protocol_classes_importable(self):
        """Test that protocol classes can be imported successfully."""
        from guapy import GuacamoleProtocol

        assert isinstance(GuacamoleProtocol, type)


class TestCompatibility:
    """Test Python version compatibility and requirements."""

    def test_python_version_compatibility(self):
        """Test that package runs on supported Python versions."""
        version_info = sys.version_info
        # Package requires Python 3.9+
        assert version_info >= (3, 9), f"Python {version_info} not supported"

    def test_required_dependencies_available(self):
        """Test that required dependencies are available."""
        import importlib.util

        required_deps = [
            "fastapi",
            "uvicorn",
            "websockets",
            "cryptography",
            "pydantic",
            "typer",
        ]

        for dep in required_deps:
            spec = importlib.util.find_spec(dep)
            assert spec is not None, f"Required dependency '{dep}' not available"

    def test_optional_dependencies_graceful_handling(self):
        """Test that optional dependencies are handled gracefully."""
        # Test with mock missing dependency
        with mock.patch.dict(sys.modules, {"missing_optional": None}):
            # Should not raise import error
            import guapy

            assert guapy is not None


class TestModuleDocstring:
    """Test module documentation."""

    def test_module_has_docstring(self):
        """Test that module has proper docstring."""
        assert guapy.__doc__ is not None
        assert len(guapy.__doc__.strip()) > 0

    def test_docstring_contains_key_information(self):
        """Test that docstring contains essential information."""
        docstring = guapy.__doc__

        # Check for key elements
        assert "Guapy" in docstring
        assert "Python implementation" in docstring
        assert "Guacamole" in docstring
        assert "WebSocket proxy server" in docstring

    def test_docstring_contains_examples(self):
        """Test that docstring contains usage examples."""
        docstring = guapy.__doc__

        # Check for example section
        assert "Example:" in docstring
        assert "create_server" in docstring

    def test_docstring_contains_features(self):
        """Test that docstring lists key features."""
        docstring = guapy.__doc__

        expected_features = [
            "Multi-Protocol Support",
            "WebSocket-Based Communication",
            "Token-Based Security",
            "Protocol Compliance",
            "Scalable Architecture",
            "RESTful Management API",
        ]

        for feature in expected_features:
            assert feature in docstring


class TestLazyImports:
    """Test lazy import behavior and circular import prevention."""

    def test_no_circular_imports(self):
        """Test that importing guapy doesn't create circular imports."""
        # This test passes if the import succeeds without hanging
        import guapy

        assert guapy is not None

    def test_submodule_imports_isolated(self):
        """Test that submodule imports don't interfere with each other."""
        # Import modules in different orders to check for dependencies
        from guapy import crypto, exceptions, models

        assert crypto is not None
        assert models is not None
        assert exceptions is not None

        # Import in reverse order
        from guapy import crypto as cry2
        from guapy import exceptions as exc2
        from guapy import models as mod2

        assert cry2 is not None
        assert mod2 is not None
        assert exc2 is not None


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_logging_configuration_correct(self):
        """Test that logging is configured correctly for the package."""
        import logging
        import sys
        from importlib import reload

        # Import guapy to ensure logging setup is triggered
        import guapy  # noqa: F401

        # Force reload to ensure handler is added
        if "guapy" in sys.modules:
            reload(sys.modules["guapy"])

        # Get the main package logger
        logger = logging.getLogger("guapy")

        # Should have at least a NullHandler
        handlers = [h for h in logger.handlers if isinstance(h, logging.NullHandler)]
        assert len(handlers) >= 1

        # Check for NullHandler
        has_null_handler = any(
            isinstance(handler, logging.NullHandler) for handler in logger.handlers
        )
        assert has_null_handler

    def test_no_unwanted_log_output(self):
        """Test that importing guapy doesn't produce unwanted log output."""
        import logging
        from io import StringIO

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.WARNING)

        # Add handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        old_level = root_logger.level
        root_logger.setLevel(logging.WARNING)

        try:
            # Re-import to trigger any logging
            import importlib

            import guapy

            importlib.reload(guapy)

            # Check that no warnings were logged
            log_output = log_capture.getvalue()
            assert log_output == "", f"Unexpected log output: {log_output}"
        finally:
            # Clean up
            root_logger.removeHandler(handler)
            root_logger.setLevel(old_level)
