# guapy.crypto

## GuacamoleCrypto
Handles encryption and decryption of connection tokens.

**Constructor:**
```python
def __init__(self, cipher_name: str, key: str):
    """Initialize crypto handler.
    Args:
        cipher_name: Name of the cipher (e.g., 'AES-256-CBC')
        key: Encryption key
    """
```

**Description:**
Supports AES-256-CBC encryption. Used for secure token handling in Guapy connections.

---

See [../api.md](../api.md) for module index.
