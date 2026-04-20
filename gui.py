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
    """ Full Pipeline to hide a plaintext message inside an image"""
    image_path = input("Input image path: ").strip() # Collect image path
    output_path = input("Output image path: ").strip()  # Get Modified image saving path
    message = input("Message: ") # Gets the plaintext message to hide

    print("\nDo you want to set a password?") # Ask User whether Encryption should be applied
    print("1: Yes")
    print("2: No")

    use_password = input("> ").strip().lower() # Prompt User

    try:
        image = load_image(image_path) # Loads the image into a numpy array

        data = text_to_bytes(message) # Converts plaintext to bytes sequences
        data = compress_data(data) # Compress message to save space

        encrypted_data = data  # default fallback if user choose no encryption

        if use_password in ["2", "no", "n"]: # If user selects no encryption, default fallback is used
            print("No encryption applied")

        elif use_password in ["1", "yes", "y"]: # If user selects yes
            password = input("Password: ") # Ask for password

            print("\nChoose encryption algorithm:") # Ask User for Encryption Algorithm
            print("1: Fernet")
            print("2: Second")
            print("3: Third")

            algo = input("> ").strip().lower() # Prompt User

            key = derive_key(password) # Derive 256 bit key from user password

            if algo in ["1", "fernet"]: # Selects Fernet encryption algorithm
                encrypted_data = encrypt_data(data, key) # Encrypts compressed data using Fernet symmetric encryption
                print("Using Fernet encryption")

            elif algo in ["2", "second"]:
                encrypted_data = encrypt_second(data)
                print("Using Other encryption (not implemented)")

            elif algo in ["3", "third"]:
                encrypted_data = encrypt_third(data)
                print("Using Other encryption (not implemented)")

            else:
                print("Invalid choice, defaulting to Fernet") # If user typed an invalid algorithm, default to fernet
                encrypted_data = encrypt_data(data, key)

        else:
            print("Invalid value, defaulting to no encryption") # If user type invalid input, default to no encryption

        encoded_image = embed_lsb(image, encrypted_data) # # Embeds encrypted binary data into image using LSB steganography


        save_image(encoded_image, output_path) # Saves modified image containing hidden encrypted message

        print("Encoding complete")

    except Exception as e:
        print(f"Error during encoding: {e}")



def decode():
    """ Full Pipeline to recover a hidden message from an image"""
    image_path = input("Encoded image path: ").strip() # Collect Modified Image from user that hides a message

    print("\nDo you have a password?") # Ask User if he has a password
    print("1: Yes")
    print("2: No")

    use_password = input("> ").strip().lower() # Prompt User

    try:
        image = load_image(image_path) # Loads the image into a numpy array

        extracted_data = extract_lsb(image) # Extracts hidden payload

        data = extracted_data #default fallback, user assumes extracted data is already plaintext

        if use_password in ["2", "no", "n"]:
            print("No decryption applied")

        elif use_password in ["1", "yes", "y"]:
            password = input("Password: ")

            print("\nChoose encryption algorithm:") # Ask user for decryption algorithm
            print("1: Fernet")
            print("2: Second")
            print("3: Third")

            algo = input("> ").strip().lower() # Prompt User

            key = derive_key(password) # Derive 256 bits key from user given password

            if algo in ["1", "fernet"]: # Selects Fernet encryption algorithm
                data = decrypt_data(extracted_data, key) # Decrypt extracted payload using Fernet symmetric encryption
                print("Fernet decryption successful")

            elif algo in ["2", "second"]:
                data = decrypt_second(extracted_data)
                print("Other decryption (not implemented)")

            elif algo in ["3", "third"]:
                data = decrypt_third(extracted_data)
                print("Other decryption (not implemented)")

            else:
                print("Invalid choice, defaulting to Fernet") # User typed invalid choice, default to fernet
                data = decrypt_data(extracted_data, key)

        else:
            print("Invalid value, defaulting to no decryption") # User typed invalid choice, default to no decryption


        decompressed_data = decompress_data(data) # Decompress payload using zlib
        message = bytes_to_text(decompressed_data) # Convert payload to readable text

        print("\nDecoded Message:") # Print the plaintext into terminal
        print(message)

    except Exception as e:
        print("Error during decoding:", e)


if __name__ == "__main__": # Used when program is executed directly
    while True: # # Infinite loop providing user interface menu until exit is selected
        print("\n--- Steganography ---")
        print("1: Embed message into image")
        print("2: Extract message from image")
        print("3: Exit")

        choice = input("> ").strip().lower() # Reads user choice

        if choice in ["1", "encode", "e"]:
            encode()
        elif choice in ["2", "decode", "d"]:
            decode()
        elif choice in ["3", "exit", "ex"]:
            print("Goodbye, thanks for using my app")
            break
        else:
            print("Invalid choice")