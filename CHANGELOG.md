# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive CI/CD pipeline with GitHub Actions
- Automated testing across Python 3.9-3.13 and multiple OS
- Security vulnerability scanning with pip-audit
- Automated publishing to TestPyPI and PyPI with Trusted Publishing
- Pre-release handling (alpha/beta/rc versions go to TestPyPI only)

### Changed
- Updated starlette dependency to >=0.47.2 for security fix (GHSA-2c2j-9gv5-cj73)
- Enhanced development dependencies with build tools and security audit

### Security
- Fixed starlette vulnerability GHSA-2c2j-9gv5-cj73

## [1.0.0] - 2025-01-28

### Added
- Initial release of Guapy
- Python implementation of Guacamole WebSocket proxy server
- Multi-protocol support: RDP, VNC, SSH, Telnet
- WebSocket-based communication with real-time bidirectional support
- Token-based security with AES-256-CBC encryption
- Async architecture built with FastAPI and asyncio
- RESTful management API with health checks and statistics
- Type hints and py.typed marker for full typing support
- CLI interface with flexible configuration options
- Support for both standalone server and FastAPI integration modes

### Documentation
- Complete API documentation
- Usage examples for different deployment scenarios
- Configuration guide with environment variable support