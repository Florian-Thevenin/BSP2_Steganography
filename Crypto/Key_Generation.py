import hashlib


def derive_key(password: str) -> bytes:
    return hashlib.sha256(password.encode()).digest()