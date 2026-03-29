# LSB Decoding/Extraction

#1. Import required modules: Pillow, numpy,

#2. Create function to read message length from the first pixels

#3. Flatten the image pixel array

#4. Extract the LSBs corresponding to message bits

#5. Reconstruct the binary string into bytes

#6. Convert bytes to string using UTF-8

#7. Return the extracted encrypted message

#8. Error handling:
#   - If the message length is invalid
#   - If extraction fails due to corrupted image or other things