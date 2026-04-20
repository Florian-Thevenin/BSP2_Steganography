from cryptography.fernet import Fernet
import base64


def decrypt_data(data: bytes, key: bytes) -> bytes:
    """ Decrypts Fernet-encrypted binary using symmetric key"""
    fernet_key = base64.urlsafe_b64encode(key[:32]) # Takes 32 bytes of key and format it into base64 for fernet
    cipher = Fernet(fernet_key) # Initialize a Fernet cypher object
    return cipher.decrypt(data) # Decrypts the input bytes and returns plaintext


# PLACEHOLDERS ( for future algorithms)
def decrypt_second(data: bytes):
    raise NotImplementedError("Other decryption not implemented yet")


def decrypt_third(data: bytes):
    raise NotImplementedError("Other decryption not implemented yet")
