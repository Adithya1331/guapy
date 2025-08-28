"""Example: Run Guapy as a standalone WebSocket server."""

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
            "http://localhost:3000",
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
