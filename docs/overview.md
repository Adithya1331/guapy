# Overview

Guapy is a Python implementation of the Guacamole WebSocket proxy server. It enables browser-based remote desktop access using RDP, VNC, and SSH protocols.

- **Project Purpose:** Provide a modern, async Python alternative to Apache Guacamole's guacd.
- **Key Features:**
  - FastAPI-based async server
  - WebSocket proxy for RDP, VNC, SSH
  - Secure connection handling with configurable CORS
  - Production-ready security defaults
  - Extensible and type-annotated codebase

## Security Features

- **Configurable CORS**: Secure by default with localhost origins, easily configurable for production
- **Token-based authentication**: Encrypted connection tokens using AES-256-CBC
- **Environment-aware configuration**: Separate development and production security settings

See [API Reference](api.md) for details.
