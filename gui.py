from Steg.Image_Process import load_image, save_image
from Steg.LSB_Encode import embed_lsb
from Steg.LSB_Decode import extract_lsb

from Misc.Utils import (
    text_to_bytes,
    bytes_to_text,
    compress_data,
    decompress_data
)

from Crypto.Key_Generation import derive_key
from Crypto.Encrypt import encrypt_data
from Crypto.Decrypt import decrypt_data


def encode():
    image_path = input("Input image path: ").strip()
    output_path = input("Output image path: ").strip()
    message = input("Message: ")
    password = input("Password: ")

    try:
        image = load_image(image_path)


        data = text_to_bytes(message)
        data = compress_data(data)

        key = derive_key(password)
        encrypted_data = encrypt_data(data, key)

        encoded_image = embed_lsb(image, encrypted_data)

        save_image(encoded_image, output_path)

        print("Encoding complete")

    except Exception as e:
        print(f"Error during encoding: {e}")


def decode():
    image_path = input("Encoded image path: ").strip()
    password = input("Password: ")

    try:
        image = load_image(image_path)

        encrypted_data = extract_lsb(image)

        key = derive_key(password)
        decrypted_data = decrypt_data(encrypted_data, key)

        decompressed_data = decompress_data(decrypted_data)

        message = bytes_to_text(decompressed_data)

        print("\nDecoded Message:")
        print(message)

    except Exception:
        print("Wrong password or corrupted data")


if __name__ == "__main__":
    while True:
        print("\n--- Steganography ---")
        print("1: Encode message into image")
        print("2: Decode message from image")
        print("3: Exit")

        choice = input("> ").strip()

        if choice == "1":
            encode()
        elif choice == "2":
            decode()
        elif choice == "3":
            print("Goodbye, thanks for using my app")
            break
        else:
            print("Invalid choice")

