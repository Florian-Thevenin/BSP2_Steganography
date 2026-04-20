import hashlib


def derive_key(password: str) -> bytes:
    """ Derives a key from user given password"""
    return hashlib.sha256(password.encode()).digest()
    # Converts password to bytes
    # Apply SHA-256 hashing (deterministic)
    # Digest() returns the raw 32-byte binary hash