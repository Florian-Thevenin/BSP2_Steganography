# Key Generation from password

#1. Import cryptography library:

#2. Function to generate a random salt

#3. Function to derive a cryptographic key from password + salt
#   - Use PBKDF2HMAC
#   - Set iterations (100,000+)

#4. Return derived key + salt (bytes)

#6. Error handling:
#   - Empty password
