# Main

#1. Import all necessary libraries: tkinter

#2. Initialize the main Tkinter window (title, size)

#3. Create a section for input image selection:
#   - Button to open file explorer
#   - Label to show selected image path

#4. Create a section for plaintext message input:
#   - Entry field for user to enter message

#5. Create a section for password input:
#   - Entry field with password

#6. Create buttons for encoding and decoding operations
#   - Encode button -> triggers message encryption + embedding
#   - Decode button -> triggers extraction + decryption

#7. Link GUI buttons to respective functions in crypto and stego modules
#   - Encode button calls encrypt -> LSB encode -> save
#   - Decode button calls load -> LSB decode -> decrypt

#8. Display output:
#   - For encoding: confirm image saved
#   - For decoding: show recovered plaintext in a messagebox or text field (optional save text in .txt file)

#9. Add error handling:
#   - No image selected

#10. Run Tkinter mainloop