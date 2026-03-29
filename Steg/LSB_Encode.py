# LSB Encoding/Embedding

#1. Import Libraries : Pillow , numpy,

#2. Create a function to convert the plaintext (or encrypted message) into a binary string
#   - Use UTF-8 (maybe add UTF-16 or other for compatibility with more characters) for encoding, then convert to bits

#3. Create a function to encode the length of the message into the first pixels (so extraction knows message size)

#4. Create the main LSB embedding function:
#   - Load image and convert to NumPy array
#   - Flatten pixel array for  iteration
#   - For each bit of the message:
#       - Replace the least significant bit (LSB) of each color channel

#5. Ensure that only as many pixels as needed are modified

#6. Reshape modified array back to image dimensions

#7. Return the modified Image object

#8. Add error handling:
#   - Message too long for the selected image

#9. Optionally: add a parameter to choose LSB depth (1 bit, 2 bits, etc.) for payload vs image reliability tradeoff