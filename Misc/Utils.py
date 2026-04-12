import zlib

def text_to_bytes(text: str) -> bytes:
    return text.encode('utf-8')


def bytes_to_text(data: bytes) -> str:
    return data.decode('utf-8')


def compress_data(data: bytes) -> bytes:
    return zlib.compress(data)


def decompress_data(data: bytes) -> bytes:
    return zlib.decompress(data)


def bytes_to_binary(data: bytes) -> str:
    return ''.join(format(byte, '08b') for byte in data)


def binary_to_bytes(binary: str) -> bytes:
    return bytes(int(binary[i:i+8], 2) for i in range(0, len(binary), 8))