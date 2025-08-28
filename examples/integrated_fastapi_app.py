"""Example: Integrate Guapy as a sub-application in an existing FastAPI app."""

import logging

from fastapi import FastAPI

from guapy import create_server
from guapy.models import ClientOptions, CryptConfig, GuacdOptions

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="FastAPI + Guapy Example")


@app.get("/root")
async def root():
    """Root endpoint."""
    return {"message": "Hello, World!"}


# --- Guapy integration ---
client_options = ClientOptions(
    crypt=CryptConfig(
        cypher="AES-256-CBC",
        key="MySuperSecretKeyForParamsToken12",
    ),
    max_inactivity_time=10000,
    cors_allow_origins=[
        "http://localhost:3000",
    ],
    cors_allow_credentials=True,
    cors_allow_methods=["GET", "POST", "OPTIONS"],
    cors_allow_headers=["Content-Type", "Authorization"],
)
guacd_options = GuacdOptions(host="127.0.0.1", port=4822)
guapy_server = create_server(client_options, guacd_options)

# Mount the Guapy FastAPI app at a sub-path (e.g., /guapy)
app.mount("/guapy", guapy_server.app)

# To run:
# uvicorn integrated_fastapi_app:app --host 0.0.0.0 --port 8005 --reload
