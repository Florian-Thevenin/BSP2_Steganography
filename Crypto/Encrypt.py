from cryptography.fernet import Fernet
import base64


def encrypt_data(data: bytes, key: bytes) -> bytes:
    """ Encrypt binary data using a symmetric key"""
    fernet_key = base64.urlsafe_b64encode(key[:32]) # Takes the 32 bytes key and format it into base64 for fernet
    cipher = Fernet(fernet_key) # Initialized Fernet cypher object
    return cipher.encrypt(data) # Encrypts the input bytes and returns ciphertext


# PLACEHOLDERS ( for future algorithms)
def encrypt_second(data: bytes):
    raise NotImplementedError("Other encryption not implemented yet")


def encrypt_third(data: bytes):
    raise NotImplementedError("Other encryption not implemented yet")