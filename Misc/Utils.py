import zlib # Lossless Compression & Decompression Algorithm


def text_to_bytes(text: str) -> bytes:
    """ Convert a string into bytes using utf-8 encoding"""
    return text.encode('utf-8')


def bytes_to_text(data: bytes) -> str:
    """ Convert bytes sequences back to characters"""
    return data.decode('utf-8')


def compress_data(data: bytes) -> bytes:
    """ Compress binary data using zlib"""
    return zlib.compress(data)


def decompress_data(data: bytes) -> bytes:
    """ Decompress binary data using zlib"""
    return zlib.decompress(data)


def bytes_to_binary(data: bytes) -> str:
    """ Converts each byte into an 8-bit string and concatenate all"""
    return ''.join(format(byte, '08b') for byte in data)


def binary_to_bytes(binary: str) -> bytes:
    """ Reconstructs bytes from a binary string"""
    return bytes(int(binary[i:i+8], 2) for i in range(0, len(binary), 8))