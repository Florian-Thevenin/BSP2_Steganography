import numpy as np
from Misc.Utils import bytes_to_binary

# We use a 32 bits header size


def embed_lsb(image_data: np.ndarray, payload: bytes) -> np.ndarray:
    """ Embeds a binary payload into an image using LSB"""
    payload_length = len(payload) # Compute payload size

    length_bin = format(payload_length, '032b') # Encode payload length into a 32 bit string header

    payload_bin = bytes_to_binary(payload) # Convert payload bytes into a binary string

    full_payload = length_bin + payload_bin # Concatenate header and payload

    flat_data = image_data.flatten() # Converts a 3D image array (height x width x RGB) into a 1D array

    if len(full_payload) > len(flat_data): # Refuse if the payload is too big
        raise ValueError("Payload too large for image")

    for i in range(len(full_payload)):  # Most Important Part, see below
        # Iterate over each bit of the full payload

        # Step 1: Bitwise AND operation
        # flat_data[i] is a single 8-bit color channel value (0–255)
        # 254 in binary = 11111110
        # AND operation clears the least significant bit (LSB) while keeping all other bits unchanged -> RGB color look the same to human eye
        flat_data[i] = flat_data[i] & 254

        # Step 2: Bitwise OR operation
        # full_payload[i] is a single bit ('0' or '1'), converted to integer (0 or 1)
        # OR operation inserts this bit into the LSB position
        flat_data[i] = flat_data[i] | int(full_payload[i])


    return flat_data.reshape(image_data.shape) # Reshape the 1D array back into the original 3D image array (height, width, RGB)