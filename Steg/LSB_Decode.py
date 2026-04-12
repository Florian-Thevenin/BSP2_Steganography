import numpy as np

HEADER_SIZE = 32  # bits


def extract_lsb(image_data: np.ndarray) -> bytes:
    flat_data = image_data.flatten()

    binary_data = ''.join(str(value & 1) for value in flat_data)

    # Read first 32 bits = payload length
    length_bin = binary_data[:HEADER_SIZE]
    payload_length = int(length_bin, 2)

    # Extract payload bits
    payload_bits = binary_data[HEADER_SIZE:HEADER_SIZE + payload_length * 8]

    # Convert to bytes
    payload = bytes(
        int(payload_bits[i:i+8], 2)
        for i in range(0, len(payload_bits), 8)
    )

    return payload