# guapy.cli

Command-line interface for running and configuring Guapy server.

## Commands

### run

Start the Guapy server with configurable options.

**Usage:**
```bash
python -m guapy.cli run [OPTIONS]
```

**Options:**
- `--host TEXT`: Host to bind the server (overrides config)
- `--port INTEGER`: Port to bind the server (overrides config)
- `--guacd-host TEXT`: guacd host (overrides config)
- `--guacd-port INTEGER`: guacd port (overrides config)
- `--secret-key TEXT`: Secret key for authentication (overrides config)
- `--max-connections INTEGER`: Maximum concurrent connections (overrides config)
- `--crypt-cypher TEXT`: Encryption cypher for tokens (default: AES-256-CBC)
- `--inactivity-time INTEGER`: Max inactivity time in ms (default: 10000)
- `--config-file TEXT`: Path to config file (default: config.json)
- `--log-level TEXT`: Log level (debug, info, warning, error, critical)

**Examples:**
```bash
# Start with default configuration
python -m guapy.cli run

# Start with custom host and port
python -m guapy.cli run --host 0.0.0.0 --port 8080

# Start with custom guacd connection
python -m guapy.cli run --guacd-host 192.168.1.100 --guacd-port 4822

# Start with custom secret key
python -m guapy.cli run --secret-key "MySecretKey32BytesLongForAES256"

# Start with debug logging
python -m guapy.cli run --log-level debug

# Start with custom config file
python -m guapy.cli run --config-file /path/to/my-config.json
```

### show-config

Display the current server configuration.

**Usage:**
```bash
python -m guapy.cli show-config [OPTIONS]
```

**Options:**
- `--config-file TEXT`: Path to config file (default: config.json)

**Examples:**
```bash
# Show current configuration
python -m guapy.cli show-config

# Show configuration from specific file
python -m guapy.cli show-config --config-file /path/to/config.json
```

## Configuration Priority

The CLI follows this configuration priority (highest to lowest):

1. **Command-line arguments**: Direct CLI options override everything
2. **Environment variables**: Standard environment variable names
3. **Configuration file**: JSON or .env file (default: config.json)
4. **Default values**: Built-in defaults

## Configuration File Format

### JSON Format (config.json)
```json
{
  "host": "127.0.0.1",
  "port": 8080,
  "guacd_host": "127.0.0.1",
  "guacd_port": 4822,
  "secret_key": "MySuperSecretKeyForParamsToken12",
  "max_connections": 100,
  "crypt_cypher": "AES-256-CBC",
  "inactivity_time": 10000,
  "log_level": "info"
}
```

### Environment Variables
```bash
export GUAPY_HOST="0.0.0.0"
export GUAPY_PORT="8080"
export GUAPY_GUACD_HOST="127.0.0.1"
export GUAPY_GUACD_PORT="4822"
export GUAPY_SECRET_KEY="MySuperSecretKeyForParamsToken12"
export GUAPY_MAX_CONNECTIONS="100"
export GUAPY_CRYPT_CYPHER="AES-256-CBC"
export GUAPY_INACTIVITY_TIME="10000"
export GUAPY_LOG_LEVEL="info"
```

## Security Considerations

### Secret Key Requirements
- Must be exactly 32 bytes for AES-256-CBC encryption
- Use a cryptographically secure random key
- Never commit secret keys to version control
- Use environment variables or secure config files in production

### Network Security
- Bind to `127.0.0.1` for local-only access
- Use `0.0.0.0` only when external access is required
- Always use HTTPS/WSS in production environments
- Restrict guacd access with firewalls

## Integration Examples

### Systemd Service
```ini
[Unit]
Description=Guapy WebSocket Proxy Server
After=network.target

[Service]
Type=simple
User=guapy
WorkingDirectory=/opt/guapy
ExecStart=/opt/guapy/venv/bin/python -m guapy.cli run --config-file /etc/guapy/config.json
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Docker Container
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["python", "-m", "guapy.cli", "run", "--host", "0.0.0.0", "--port", "8080"]
```

### Process Manager (PM2)
```json
{
  "apps": [{
    "name": "guapy",
    "script": "python",
    "args": ["-m", "guapy.cli", "run"],
    "cwd": "/opt/guapy",
    "env": {
      "GUAPY_HOST": "127.0.0.1",
      "GUAPY_PORT": "8080",
      "GUAPY_SECRET_KEY": "MySuperSecretKeyForParamsToken12"
    },
    "instances": 1,
    "autorestart": true
  }]
}
```

**Description:**
The CLI provides a convenient way to run and configure Guapy servers with flexible configuration options. It supports multiple configuration sources and follows standard CLI conventions for ease of use in various deployment scenarios.

---

See [../api.md](../api.md) for module index.