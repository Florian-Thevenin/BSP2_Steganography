import numpy as np
from Misc.Utils import binary_to_bytes

HEADER_SIZE = 32  # Number of bits used to store payload length


def extract_lsb(image_data: np.ndarray) -> bytes:
    """ Extracts hidden binary payload from an image array using LSB"""
    flat_data = image_data.flatten() # Converts 3D image array (height x width x RGB channels) into a 1D array

    binary_data = ''.join(str(value & 1) for value in flat_data) # Extract the LSB from each 8-bits color value and concatenate them into a string

    length_bin = binary_data[:HEADER_SIZE] # Reads the first 32 bits that encode the payload length
    payload_length = int(length_bin, 2) # Convert that length into an integer

    payload_bits = binary_data[HEADER_SIZE:HEADER_SIZE + payload_length * 8] # Skip header and extracts only payload


    payload = binary_to_bytes(payload_bits) # Converts binary string into bytes object

    return payload