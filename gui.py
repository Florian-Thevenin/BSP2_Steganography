from Steg.Image_Process import load_image, save_image
from Steg.LSB_Embed import embed_lsb
from Steg.LSB_Extract import extract_lsb

from Misc.Utils import (
    text_to_bytes,
    bytes_to_text,
    compress_data,
    decompress_data
)

from Crypto.Key_Generation import derive_key
from Crypto.Encrypt import encrypt_data, encrypt_second, encrypt_third
from Crypto.Decrypt import decrypt_data, decrypt_second, decrypt_third



def encode():
    image_path = input("Input image path: ").strip()
    output_path = input("Output image path: ").strip()
    message = input("Message: ")

    print("\nDo you want to set a password?")
    print("1: Yes")
    print("2: No")

    use_password = input("> ").strip().lower()

    try:
        image = load_image(image_path)

        data = text_to_bytes(message)
        data = compress_data(data)

        encrypted_data = data  # default fallback

        if use_password in ["2", "no", "n"]:
            print("No encryption applied")

        elif use_password in ["1", "yes", "y"]:
            password = input("Password: ")

            print("\nChoose encryption algorithm:")
            print("1: Fernet")
            print("2: Second")
            print("3: Third")

            algo = input("> ").strip().lower()

            key = derive_key(password)

            if algo in ["1", "fernet"]:
                encrypted_data = encrypt_data(data, key)
                print("Using Fernet encryption")

            elif algo in ["2", "second"]:
                encrypted_data = encrypt_second(data)
                print("Using Other encryption (not implemented)")

            elif algo in ["3", "third"]:
                encrypted_data = encrypt_third(data)
                print("Using Other encryption (not implemented)")

            else:
                print("Invalid choice, defaulting to Fernet")
                encrypted_data = encrypt_data(data, key)

        else:
            print("Invalid value, defaulting to no encryption")

        encoded_image = embed_lsb(image, encrypted_data)


        save_image(encoded_image, output_path)

        print("Encoding complete")

    except Exception as e:
        print(f"Error during encoding: {e}")



def decode():
    image_path = input("Encoded image path: ").strip()

    print("\nDo you have a password?")
    print("1: Yes")
    print("2: No")

    use_password = input("> ").strip().lower()

    try:
        image = load_image(image_path)

        extracted_data = extract_lsb(image)

        data = extracted_data #default fallback

        if use_password in ["2", "no", "n"]:
            print("No decryption applied")

        elif use_password in ["1", "yes", "y"]:
            password = input("Password: ")

            print("\nChoose encryption algorithm:")
            print("1: Fernet")
            print("2: Second")
            print("3: Third")

            algo = input("> ").strip().lower()

            key = derive_key(password)

            if algo in ["1", "fernet"]:
                data = decrypt_data(extracted_data, key)
                print("Fernet decryption successful")

            elif algo in ["2", "second"]:
                data = decrypt_second(extracted_data)
                print("Other decryption (not implemented)")

            elif algo in ["3", "third"]:
                data = decrypt_third(extracted_data)
                print("Other decryption (not implemented)")

            else:
                print("Invalid choice, defaulting to Fernet")
                data = decrypt_data(extracted_data, key)

        else:
            print("Invalid value, defaulting to no decryption")


        decompressed_data = decompress_data(data)
        message = bytes_to_text(decompressed_data)

        print("\nDecoded Message:")
        print(message)

    except Exception as e:
        print("Error during decoding:", e)


if __name__ == "__main__":
    while True:
        print("\n--- Steganography ---")
        print("1: Embed message into image")
        print("2: Extract message from image")
        print("3: Exit")

        choice = input("> ").strip().lower()

        if choice in ["1", "encode", "e"]:
            encode()
        elif choice in ["2", "decode", "d"]:
            decode()
        elif choice in ["3", "exit", "ex"]:
            print("Goodbye, thanks for using my app")
            break
        else:
            print("Invalid choice")