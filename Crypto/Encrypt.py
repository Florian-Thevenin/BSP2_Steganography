from cryptography.fernet import Fernet
import base64


def encrypt_data(data: bytes, key: bytes) -> bytes:
    fernet_key = base64.urlsafe_b64encode(key[:32])
    cipher = Fernet(fernet_key)
    return cipher.encrypt(data)


# PLACEHOLDERS ( for future algorithms)
def encrypt_second(data: bytes):
    raise NotImplementedError("Other encryption not implemented yet")


def encrypt_third(data: bytes):
    raise NotImplementedError("Other encryption not implemented yet")