import itertools
import string
import time

from Steg.LSB_Extract import extract_lsb
from Steg.Image_Process import load_image
from Crypto.Key_Generation import derive_key
from Crypto.Decrypt import decrypt_data
from Misc.Utils import decompress_data, bytes_to_text




MAX_BRUTEFORCE_LENGTH = 6 # Maximum password length to try in bruteforce mode

# All characters available on a standard AZERTY/QWERTY keyboard including accented latin characters
CHARSET = (
    string.ascii_lowercase +        # a-z
    string.ascii_uppercase +        # A-Z
    string.digits +                 # 0-9
    string.punctuation +            # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
    " " +                           # Whitespace
    "àâäéèêëîïôöùûüç" # Accented latin characters
)




def try_password(extracted_data: bytes, password: str) -> str | None:
    """ Try a single password against the extracted payload, returns decrypted message or None """
    try:
        key = derive_key(password) # Derive key from candidate password
        decrypted = decrypt_data(extracted_data, key) # Try to decrypt with that key
        decompressed = decompress_data(decrypted) # Try to decompress decrypted data
        message = bytes_to_text(decompressed) # Try to decode to text
        return message # All steps passed, password is correct

    except Exception:
        return None # Any failure means wrong password




def wordlist_attack(extracted_data: bytes, wordlist_path: str) -> tuple | None:
    """ Try every password in a wordlist file, returns (password, message) if found """

    if not wordlist_path: # If no wordlist path given, skip
        return None

    try:
        with open(wordlist_path, "r", encoding="latin-1", errors="ignore") as f:
            words = f.read().splitlines() # Read all lines, one password per line
    except FileNotFoundError:
        print(f"Wordlist not found: {wordlist_path}") # Warn user if file missing
        return None

    print(f"\nStarting wordlist attack with {len(words)} passwords...")

    start = time.perf_counter() # Start timer
    guesses = 0 # Count total attempts

    for word in words: # Iterate over each password candidate
        guesses += 1
        result = try_password(extracted_data, word) # Try this password

        if result is not None: # Password worked
            elapsed = time.perf_counter() - start
            print(f"Password found: {word}") # Display found password
            print(f"Guesses: {guesses}") # Display number of attempts
            print(f"Time: {elapsed:.2f}s") # Display time taken
            print(f"Speed: {guesses / elapsed:.0f} guesses/sec") # Display speed
            return word, result # Return found password and decrypted message

        if guesses % 10_000 == 0: # Every 10000 guesses, print progress
            elapsed = time.perf_counter() - start
            print(f"Tried {guesses} passwords... ({guesses / elapsed:.0f}/sec)")

    print(f"Wordlist exhausted after {guesses} attempts, password not found") # Wordlist failed
    return None




def bruteforce_attack(extracted_data: bytes) -> tuple | None:
    """ Try every possible combination up to MAX_BRUTEFORCE_LENGTH, returns (password, message) if found """

    print(f"\nStarting bruteforce attack up to length {MAX_BRUTEFORCE_LENGTH}...")
    print(f"Charset size: {len(CHARSET)} characters")
    print("Warning: this may take a very long time")

    start = time.perf_counter() # Start timer
    guesses = 0 # Count total attempts

    for length in range(1, MAX_BRUTEFORCE_LENGTH + 1): # Try lengths 1 to MAX_BRUTEFORCE_LENGTH
        print(f"\nTrying length {length}...")

        for combo in itertools.product(CHARSET, repeat=length): # Generate every combination of that length
            password = "".join(combo) # Join characters into a string
            guesses += 1

            result = try_password(extracted_data, password) # Try this password

            if result is not None: # Password worked
                elapsed = time.perf_counter() - start
                print(f"Password found: {password}") # Display found password
                print(f"Guesses: {guesses}") # Display number of attempts
                print(f"Time: {elapsed:.2f}s") # Display time taken
                print(f"Speed: {guesses / elapsed:.0f} guesses/sec") # Display speed
                return password, result # Return found password and decrypted message

            if guesses % 100_000 == 0: # Every 100000 guesses, print progress
                elapsed = time.perf_counter() - start
                print(f"Tried {guesses} passwords... ({guesses / elapsed:.0f}/sec)")

    print(f"Bruteforce exhausted after {guesses} attempts, password not found") # Bruteforce failed
    return None




def run_attack(image_path: str, wordlist_path: str = None):
    """ Full attack pipeline, wordlist first then bruteforce """

    image = load_image(image_path) # Load image into numpy array
    extracted_data = extract_lsb(image) # Extract hidden payload from image

    print("\n--- Password Attack ---")

    # Phase 1 - Wordlist
    result = wordlist_attack(extracted_data, wordlist_path) # Try wordlist first

    if result is None and wordlist_path: # Wordlist was provided but failed
        print("\nWordlist failed, switching to bruteforce...")

    # Phase 2 - Bruteforce if wordlist failed or was not provided
    if result is None:
        result = bruteforce_attack(extracted_data) # Fall back to bruteforce

    # Final result
    if result is not None:
        password, message = result
        print("\n--- Attack Successful ---")
        print(f"Password : {password}")
        print(f"Message  : {message}")
    else:
        print("\nAttack failed, password could not be found") # Both methods failed


if __name__ == "__main__":
    image_path = input("Encoded image path: ").strip() # Get image path from user

    print("\nDo you have a wordlist ?") # Ask user if they have a wordlist
    print("1: Yes")
    print("2: No")

    choice = input("> ").strip().lower()

    if choice in ["1", "yes", "y"]:
        wordlist_path = input("Wordlist path: ").strip() # Get wordlist path from user
    else:
        wordlist_path = None # No wordlist, go straight to bruteforce

    run_attack(image_path, wordlist_path)