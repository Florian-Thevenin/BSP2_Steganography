from cryptography.fernet import Fernet
import base64


def decrypt_data(data: bytes, key: bytes) -> bytes:
    fernet_key = base64.urlsafe_b64encode(key[:32])
    cipher = Fernet(fernet_key)
    return cipher.decrypt(data)


# PLACEHOLDERS ( for future algorithms)
def decrypt_second(data: bytes):
    raise NotImplementedError("Other decryption not implemented yet")


def decrypt_third(data: bytes):
    raise NotImplementedError("Other decryption not implemented yet")
