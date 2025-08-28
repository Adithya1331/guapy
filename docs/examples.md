# Examples & Tutorials

This section provides practical examples of how to use Guapy in different scenarios.

## 1. Basic Standalone Server

This is the simplest way to get a Guapy server running. It uses the built-in configuration loader, which can be customized via a `config.json` file or environment variables.

A direct way to run the server programmatically:

```python
# examples/standalone_server.py
import uvicorn
from guapy.server import create_server
from guapy.models import ClientOptions, GuacdOptions, CryptConfig

# Basic configuration
SECRET_KEY = "YOUR_SUPER_SECRET_KEY_MUST_BE_32_BYTES"  # Must be 32 bytes for AES-256

# 1. Configure client options, including encryption
client_options = ClientOptions(
    crypt=CryptConfig(
        cypher="AES-256-CBC",
        key=SECRET_KEY,
    )
)

# 2. Configure connection to the guacd daemon
guacd_options = GuacdOptions(host="localhost", port=4822)

# 3. Create the Guapy server instance
server = create_server(client_options, guacd_options)

# 4. Run the server with uvicorn
if __name__ == "__main__":
    uvicorn.run(server.app, host="127.0.0.1", port=8080)
```

## 2. Integrating with an Existing FastAPI Application

You can easily mount the Guapy server as a sub-application within your existing FastAPI project.

```python
# examples/integrated_fastapi_app.py
from fastapi import FastAPI
from guapy.server import create_server
from guapy.models import ClientOptions, GuacdOptions, CryptConfig

# Create your main FastAPI application
app = FastAPI(title="My Application")

@app.get("/api/users")
async def get_users():
    return {"users": []}

# Configure Guapy
SECRET_KEY = "YOUR_SUPER_SECRET_KEY_MUST_BE_32_BYTES"

client_options = ClientOptions(
    crypt=CryptConfig(
        cypher="AES-256-CBC",
        key=SECRET_KEY,
    )
)
guacd_options = GuacdOptions(host="localhost", port=4822)

# Create and mount Guapy server
guapy_server = create_server(client_options, guacd_options)
app.mount("/guapy", guapy_server.app)

# Your application will have:
# - Your API at /api/*
# - Guapy WebSocket at /guapy/webSocket
# - Guapy health check at /guapy/health
```

## 3. CLI Usage

### Basic CLI Commands

```bash
# Start server with defaults
python -m guapy.cli run

# Start with custom configuration
python -m guapy.cli run --host 0.0.0.0 --port 8080 --guacd-host 192.168.1.100

# Show current configuration
python -m guapy.cli show-config
```

### Production Configuration

```bash
# Using environment variables
export GUAPY_SECRET_KEY="MySuperSecretKeyForParamsToken12"
export GUAPY_HOST="0.0.0.0"
export GUAPY_PORT="8080"
python -m guapy.cli run

# Using config file
python -m guapy.cli run --config-file /etc/guapy/production.json
```

## 4. Error Handling

```python
from guapy.exceptions import (
    GuapyError, GuacdConnectionError, TokenDecryptionError,
    GuapyUnauthorizedError, GuapyProtocolError
)
from guapy.server import create_server
from guapy.models import ClientOptions, CryptConfig, GuacdOptions

try:
    client_options = ClientOptions(
        crypt=CryptConfig(
            cypher="AES-256-CBC",
            key="MySuperSecretKeyForParamsToken12",
        )
    )
    guacd_options = GuacdOptions(host="localhost", port=4822)
    server = create_server(client_options, guacd_options)
    
except GuacdConnectionError as e:
    print(f"Failed to connect to guacd: {e}")
    print(f"Error details: {e.details}")
    
except TokenDecryptionError as e:
    print(f"Token decryption failed: {e}")
    
except GuapyError as e:
    print(f"Guapy error [{e.error_code}]: {e.message}")
    if e.details:
        print(f"Additional details: {e.details}")
```

## 5. Custom Filters

```python
from guapy.filter import GuacamoleFilter
from guapy.server import create_server
from guapy.models import ClientOptions, CryptConfig, GuacdOptions
from typing import Optional
import logging

class AuditFilter(GuacamoleFilter):
    """Filter that logs all instructions for auditing."""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
    
    def filter(self, instruction: list[str]) -> Optional[list[str]]:
        # Log all instructions for security auditing
        self.logger.info(f"Instruction: {instruction[0] if instruction else 'empty'}")
        return instruction  # Pass through unchanged

class SecurityFilter(GuacamoleFilter):
    """Filter that blocks potentially dangerous instructions."""
    
    def filter(self, instruction: list[str]) -> Optional[list[str]]:
        if not instruction:
            return instruction
            
        # Block clipboard operations for security
        if instruction[0] == "clipboard":
            return None  # Silently drop
            
        # Block file transfer operations
        if instruction[0] in ["file", "pipe"]:
            return None
            
        return instruction

# To use custom filters, you would need to modify the GuacdClient
# This is an advanced use case - see source code for implementation details
```

## 6. CORS Configuration

### Development CORS (Permissive)
```python
from guapy.models import ClientOptions, CryptConfig

# WARNING: Only for development!
client_options = ClientOptions.create_with_development_cors(
    crypt=CryptConfig(
        cypher="AES-256-CBC",
        key="MySuperSecretKeyForParamsToken12",
    )
)
# This allows all origins - never use in production!
```

### Production CORS (Secure)
```python
from guapy.models import ClientOptions, CryptConfig

# Production-safe CORS configuration
allowed_origins = [
    "https://myapp.com",
    "https://admin.myapp.com"
]

client_options = ClientOptions.create_with_production_cors(
    crypt=CryptConfig(
        cypher="AES-256-CBC",
        key="MySuperSecretKeyForParamsToken12",
    ),
    allowed_origins=allowed_origins
)
```

### Custom CORS Configuration
```python
from guapy.models import ClientOptions, CryptConfig

client_options = ClientOptions(
    crypt=CryptConfig(
        cypher="AES-256-CBC",
        key="MySuperSecretKeyForParamsToken12",
    ),
    cors_allow_origins=["https://myapp.com"],
    cors_allow_credentials=True,
    cors_allow_methods=["GET", "POST", "OPTIONS"],
    cors_allow_headers=["Content-Type", "Authorization"],
)

# Your existing FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "This is my main application."}

# --- Guapy Integration ---

# 1. Configure Guapy
SECRET_KEY = "YOUR_SUPER_SECRET_KEY_MUST_BE_32_BYTES"
client_options = ClientOptions(
    crypt=CryptConfig(cypher="AES-256-CBC", key=SECRET_KEY)
)
guacd_options = GuacdOptions(host="localhost", port=4822)

# 2. Create the Guapy server
guapy_server = create_server(client_options, guacd_options)

# 3. Mount the Guapy WebSocket endpoint
# This makes Guapy available at /guacamole/
app.mount("/guacamole", guapy_server.app)

# To run this integrated app:
# uvicorn integrated_fastapi_app:app --reload
```

## 3. Generating a Connection Token

To connect, a client needs a secure token. Here’s how you can generate one.

```python
import json
from guapy.crypto import GuacamoleCrypto

SECRET_KEY = "YOUR_SUPER_SECRET_KEY_MUST_BE_32_BYTES"

# 1. Define the connection parameters
connection_params = {
    "connection": {
        "type": "rdp",
        "settings": {
            "hostname": "192.168.1.100",
            "port": "3389",
            "username": "myuser",
            "password": "mypassword",
            "ignore-cert": "true",
        }
    }
}

# 2. Initialize the crypto handler with your secret key
crypto = GuacamoleCrypto(cipher_name="AES-256-CBC", key=SECRET_KEY)

# 3. Encrypt the data to create the token
token = crypto.encrypt(connection_params)

print(f"Generated Token: {token}")

# The client would then connect to:
# ws://localhost:8080/?token=GENERATED_TOKEN_HERE
```

## 4. CORS Configuration Examples

### Production Configuration
For production environments, use specific allowed origins:

```python
from guapy.models import ClientOptions, CryptConfig

# Secure production CORS configuration
crypt_config = CryptConfig(
    cypher="AES-256-CBC",
    key="YOUR_32_BYTE_SECRET_KEY_HERE_123456"
)

# Option 1: Using the utility method (recommended)
client_options = ClientOptions.create_with_production_cors(
    crypt=crypt_config,
    allowed_origins=[
        "https://myapp.com",
        "https://admin.myapp.com",
        "https://api.mycompany.com"
    ]
)

# Option 2: Manual configuration for fine control
client_options = ClientOptions(
    crypt=crypt_config,
    cors_allow_origins=["https://myapp.com", "https://admin.myapp.com"],
    cors_allow_credentials=True,
    cors_allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    cors_allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)
```

### Development Configuration
For development environments only (WARNING: Security risk in production):

```python
# Development-only CORS configuration
client_options = ClientOptions.create_with_development_cors(
    crypt=crypt_config,
    max_inactivity_time=30000  # Other options can be passed too
)

# This is equivalent to:
client_options = ClientOptions(
    crypt=crypt_config,
    cors_allow_origins=["*"],  # WARNING: Allows ALL origins!
    cors_allow_credentials=True,
    cors_allow_methods=["*"],
    cors_allow_headers=["*"],
)
```

### Environment-Specific Configuration
```python
import os
from guapy.models import ClientOptions, CryptConfig

crypt_config = CryptConfig(
    cypher="AES-256-CBC",
    key=os.getenv("GUAPY_SECRET_KEY")
)

if os.getenv("ENVIRONMENT") == "development":
    # Development: Allow all origins (use with caution)
    client_options = ClientOptions.create_with_development_cors(crypt_config)
else:
    # Production: Restrict to specific domains
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "https://myapp.com").split(",")
    client_options = ClientOptions.create_with_production_cors(
        crypt_config, 
        allowed_origins
    )
```

## 5. Security Best Practices

### CORS Security
1. **Never use wildcard origins (`*`) in production**
2. **Use specific domains**: List only the domains that need access
3. **Environment-specific configuration**: Use restrictive settings in production
4. **Regular audits**: Review and update allowed origins regularly

### Example Security Checklist
```python
# ✅ Good: Specific origins
cors_allow_origins=["https://myapp.com", "https://admin.myapp.com"]

# ❌ Bad: Wildcard in production
cors_allow_origins=["*"]  # Only for development!

# ✅ Good: Specific methods
cors_allow_methods=["GET", "POST", "OPTIONS"]

# ❌ Bad: All methods
cors_allow_methods=["*"]  # Unnecessary in most cases
```

### Updating Existing Code
If you're upgrading from an older version of Guapy, your existing code will continue to work with secure defaults:

```python
# Old code (still works, but now secure by default)
client_options = ClientOptions(
    crypt=CryptConfig(cypher="AES-256-CBC", key=SECRET_KEY)
)
# Now uses secure localhost origins instead of wildcard

# Recommended: Explicitly configure for your environment
client_options = ClientOptions(
    crypt=CryptConfig(cypher="AES-256-CBC", key=SECRET_KEY),
    cors_allow_origins=["https://yourapp.com"]  # Your specific domain
)
```

