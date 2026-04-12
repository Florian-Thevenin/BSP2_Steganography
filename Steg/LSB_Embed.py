import numpy as np

HEADER_SIZE = 32  # bits


def embed_lsb(image_data: np.ndarray, payload: bytes) -> np.ndarray:
    payload_length = len(payload)

    # Convert length to 32-bit binary
    length_bin = format(payload_length, '032b')

    # Convert payload to binary
    payload_bin = ''.join(format(byte, '08b') for byte in payload)

    full_payload = length_bin + payload_bin

    flat_data = image_data.flatten()

    if len(full_payload) > len(flat_data):
        raise ValueError("Payload too large for image")

    for i in range(len(full_payload)):
        flat_data[i] = (flat_data[i] & 254) | int(full_payload[i])

    return flat_data.reshape(image_data.shape)