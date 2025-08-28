# guapy.config

## ConfigManager
Configuration manager for guapy server application.

**Constructor:**
```python
def __init__(self, config_file: Optional[Path] = None):
    """Initialize ConfigManager.
    Args:
        config_file: Path to configuration file, defaults to "config.json"
    """
```

**Description:**
Loads configuration from file, environment variables, and command line arguments. Provides unified access to server configuration.

---

See [../api.md](../api.md) for module index.
