# Guapy

[![PyPI version](https://badge.fury.io/py/guapy.svg)](https://badge.fury.io/py/guapy)
[![Python Support](https://img.shields.io/pypi/pyversions/guapy.svg)](https://pypi.org/project/guapy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Guapy is a modern, async Python implementation of the Apache Guacamole WebSocket proxy server. It enables secure, clientless remote desktop access via web browsers, bridging web clients and remote desktop servers using the Guacamole protocol.

---

## Features

- **Multi-Protocol**: RDP, VNC, SSH, Telnet
- **WebSocket Communication**: Real-time, bidirectional
- **Token-Based Security**: AES-encrypted connection tokens
- **Async & Scalable**: Built with FastAPI and asyncio
- **RESTful API**: Health, stats, and management endpoints
- **Flexible Usage**: Use as a library, standalone server, or integrate with your FastAPI app

---

## Installation

```bash
pip install guapy
```

---

## Usage

### 1. Standalone Server See [`examples/standalone_server.py`](examples/standalone_server.py):

```python
import asyncio
import logging

import uvicorn

from guapy import create_server
from guapy.models import ClientOptions, CryptConfig, GuacdOptions

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to start the Guapy server."""
    client_options = ClientOptions(
        crypt=CryptConfig(
            cypher="AES-256-CBC",
            key="MySuperSecretKeyForParamsToken12",
        ),
        cors_allow_origins=[
            "http://localhost:3000",  # React dev server
        ],
        cors_allow_credentials=True,
        cors_allow_methods=["GET", "POST", "OPTIONS"],
        cors_allow_headers=["Content-Type", "Authorization"],
    )
    guacd_options = GuacdOptions(host="10.21.34.133", port=4822)
    # guacd_options = GuacdOptions(host="127.0.0.1", port=4822)
    server = create_server(client_options, guacd_options)
    logger.info("Starting Guapy server...")
    logger.info("WebSocket endpoint: ws://localhost:8080/")
    logger.info("Health check: http://localhost:8080/health")
    logger.info("Stats: http://localhost:8080/stats")
    logger.info("Press Ctrl+C to stop")
    config = uvicorn.Config(app=server.app, host="0.0.0.0", port=8080)  # noqa: S104
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

```

### 2. CLI Server

Run with flexible config using Typer CLI:

```bash
python -m guapy.cli run --host 0.0.0.0 --port 8080 --guacd-host 127.0.0.1 --guacd-port 4822 --secret-key MySuperSecretKeyForParamsToken12
```

See `python -m guapy.cli --help` for all options.

### 3. Integrate with Your FastAPI App See [`examples/integrated_fastapi_app.py`](examples/integrated_fastapi_app.py):

```python
from fastapi import FastAPI
from guapy import create_server
from guapy.models import ClientOptions, CryptConfig, GuacdOptions

app = FastAPI()

@app.get("/root")
async def root():
    return {"message": "Hello, World!"}

client_options = ClientOptions(
    crypt=CryptConfig(
        cypher="AES-256-CBC",
        key="MySuperSecretKeyForParamsToken12",
    ),
    max_inactivity_time=10000,
)
guacd_options = GuacdOptions(host="127.0.0.1", port=4822)
guapy_server = create_server(client_options, guacd_options)
app.mount("/guapy", guapy_server.app)
```

---

## Configuration

- Use CLI options, environment variables, or a config file (`config.json` or `.env`).
- See `src/guapy/config.py` for details.

---

## API Endpoints

- WebSocket: `ws://localhost:8080/webSocket?token=...`
- REST: `/`, `/health`, `/stats` (or `/guapy/...` if mounted)
- Swagger docs: `/docs` (main app), `/guapy/docs` (mounted Guapy)

---

## Security

- Use strong encryption keys and HTTPS/WSS in production
- Restrict guacd access with firewalls
- Monitor logs for suspicious activity

---

## Development & Examples

- See the `examples/` directory for usage patterns
- Run tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Security audit: `uv run pip-audit`
- Full verification: `uv run python scripts/verify_package.py`

### CI/CD

This project uses GitHub Actions for:
- **Continuous Integration**: Automated testing across Python 3.9-3.13 on Linux, Windows, and macOS
- **Security Scanning**: Dependency vulnerability checks with pip-audit
- **Automated Publishing**: Secure releases to TestPyPI and PyPI using Trusted Publishing
- **Pre-release Support**: Alpha/beta/rc versions automatically go to TestPyPI only

See [PUBLISHING_SETUP.md](PUBLISHING_SETUP.md) for complete setup instructions.

---

## License

MIT. See [LICENSE](LICENSE).

---

## Acknowledgments

- Apache Guacamole project
- FastAPI
- Python asyncio community
