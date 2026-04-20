import time
import os

from Steg.Image_Process import load_image
from Steg.LSB_Embed import embed_lsb
from Steg.LSB_Extract import extract_lsb

from Misc.Utils import text_to_bytes, compress_data, decompress_data

from Crypto.Key_Generation import derive_key
from Crypto.Encrypt import encrypt_data
from Crypto.Decrypt import decrypt_data


def now():
    """ Timer used to measure execution time of differents operations"""
    return time.perf_counter()


def test_capacity(image_path: str):
    """ Loads image and computes theoretical LSB embedding capacity"""
    image = load_image(image_path) # Loads Image as a 3D numpy array

    total_values = image.size # Total number of color channel values (R, G, B for each pixel)
    usable_bytes = (total_values // 8) - 4 # Number of LSB Slots Available (1 per 8-bit color value) -4 for header

    if usable_bytes < 0:
        usable_bytes = 0

    print("\n--- Capacity Analysis ---")
    print(f"Image shape        : {image.shape}") # (Height, Width, number of color value)
    print(f"Max payload        : {usable_bytes} bytes") # Max number of bytes (Before Compression)
    print(f"Max ASCII chars    : {usable_bytes} chars") # MAX ASCII Characters (8 bits for one char)
    print(f"Safe UTF-8 chars   : ~{usable_bytes // 2} chars") # Average Max UTF-8 (ASCII takes 8 bits, but accented letters e.g. (é, ï) takes 2

    return usable_bytes # Return Max payload


def test_compression(message: str, max_capacity: int):
    """ Measures compression efficiency and execution time"""
    raw = text_to_bytes(message) # Convert text to a sequences of bytes

    # Measures compression execution time
    start = now()
    compressed = compress_data(raw)
    t = now() - start

    ratio = len(compressed) / len(raw) # Compression efficiency ratio
    usage = (len(compressed) / max_capacity) * 100 # Percentage of image capacity used by compressed data

    print("\n--- Compression Test ---")
    print(f"Original size   : {len(raw)} bytes")
    print(f"Compressed size : {len(compressed)} bytes")
    print(f"Compression time: {t:.6f}s")
    print(f"Compression ratio: {ratio:.4f}")
    print(f"Compressed usage : {usage:.2f}% of image capacity")

    if len(compressed) <= max_capacity:
        print("Compressed payload fits inside image")
    else:
        print("Compressed payload exceeds image capacity")

    return compressed


def check_password_strength(password: str):
    """ Simple Password scoring """
    print("\n--- Password Analysis ---")

    score = 0

    if len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1

    if any(c.isdigit() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c in "!@#$%^&*" for c in password):
        score += 2

    if score >= 5:
        print("Strong password")
    elif score >= 3:
        print("Medium strength password")
    else:
        print("Weak password")

    return score


def load_txt(path: str) -> str:
    """ Loads text file used for mock payloads"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_mock_payload(choice, max_capacity):
    # Generates mock payloads of different sizes to test capacity
    small_base = load_txt(".docs/small.txt")
    medium_base = load_txt(".docs/medium.txt")
    large_base = load_txt(".docs/large.txt")

    if choice == "1":
        # no repetition
        return small_base.strip()

    elif choice == "2":
        # expand until 40% capacity
        target = int(max_capacity * 0.4)
        result = ""

        while len(result.encode("utf-8")) < target:
            result += medium_base + "\n"

        return result.strip()

    elif choice == "3":
        # expand until 80% capacity
        target = int(max_capacity * 0.8)
        result = ""

        while len(result.encode("utf-8")) < target:
            result += large_base + "\n"

        return result.strip()

    return None


def run_pipeline():
    """ Execute steganography pipeline and measure performance"""
    total_exec_time = 0.0
    # Accumulates total execution time of all operations

    image_path = input("\nEnter PNG image path: ").strip() # Gets image path from user and removes whitespaces

    if not os.path.exists(image_path):
        print("File not found")
        return

    # Measures Loading time and add to total
    start = now()
    max_capacity = test_capacity(image_path)
    total_exec_time += now() - start


    print("\nChoose payload:") # Ask User for payload
    print("1: Small mock")
    print("2: Medium mock")
    print("3: Large (80% capacity)")
    print("4: Custom text")

    choice = input("> ").strip() # Prompt User

    if choice in ["1", "2", "3"]:
        message = get_mock_payload(choice, max_capacity)
    else:
        message = input("\nEnter plaintext message: ")

    raw = text_to_bytes(message) # Convert plaintext message to bytes sequences

    print("\n--- Payload Info ---")
    print(f"Plaintext bytes : {len(raw)}") # Displays raw byte size of message
    print(f"Plaintext chars : {len(message)}") # Displays number of characters in original message
    print(f"Capacity usage  : {(len(raw)/max_capacity)*100:.2f}%") # Shows how much of image embedding capacity is used

    # Measures Compression time and add to total
    start = now()
    compressed = test_compression(message, max_capacity)
    total_exec_time += now() - start


    password = input("\nEnter password: ") # Gets encryption password from user

    check_password_strength(password) # Evaluates password strength

    key = derive_key(password) # Derives 256 bits key from password


    print("\n--- Encryption ---")
    #Measures Encryption execution time
    start = now()
    encrypted = encrypt_data(compressed, key)
    enc_time = now() - start
    total_exec_time += enc_time
    print(f"Encryption time: {enc_time:.6f}s")


    print("\n--- Embedding ---")
    # Measures embedding execution time
    image = load_image(image_path)

    start = now()
    stego_array = embed_lsb(image.copy(), encrypted)
    embed_time = now() - start
    total_exec_time += embed_time

    print(f"Embedding time: {embed_time:.6f}s")


    print("\n--- Extraction ---")
    # Measures extracting execution time
    start = now()
    extracted = extract_lsb(stego_array)
    extract_time = now() - start
    total_exec_time += extract_time

    print(f"Extraction time : {extract_time:.6f}s")

    print("\n--- Decryption ---")
    # Measures Decryption execution time
    start = now()
    decrypted = decrypt_data(extracted, key)
    decrypt_time = now() - start
    total_exec_time += decrypt_time

    print(f"Decryption time : {decrypt_time:.6f}s")

    print("\n--- Decompression ---")
    # Measures decompression execution time
    start = now()
    decompressed = decompress_data(decrypted)
    decompress_time = now() - start

    total_exec_time += decompress_time

    print(f"Decompression time : {decompress_time:.6f}s")


    print("\n--- FINAL RESULT ---")
    print("Stego completed successfully")

    print(f"\nTOTAL EXECUTION TIME: {total_exec_time:.6f}s")


if __name__ == "__main__":
    run_pipeline()