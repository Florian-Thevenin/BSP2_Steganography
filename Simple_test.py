import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image
import numpy as np


# Convert message → binary

def text_to_binary(message):
    return ''.join(format(ord(c), '08b') for c in message)


# Convert binary → Message

def binary_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(c, 2)) for c in chars)


# Encode message into image

def encode_image(image_path, message, output_path):
    image = Image.open(image_path).convert("RGB")
    data = np.array(image)

    binary_message = text_to_binary(message) + '1111111111111110'  # end marker

    flat_data = data.flatten()
    if len(binary_message) > len(flat_data):
        raise ValueError("Message too large for this image")

    # LSB embedding
    for i in range(len(binary_message)):
        flat_data[i] = (flat_data[i] & 254) | int(binary_message[i])

    new_data = flat_data.reshape(data.shape)
    Image.fromarray(new_data.astype('uint8')).save(output_path)
    messagebox.showinfo("Success", f"Image saved as:\n{output_path}")


#  Decode message from image

def decode_image(image_path):
    image = Image.open(image_path).convert("RGB")
    data = np.array(image)

    flat_data = data.flatten()
    binary_data = ''.join(str(value & 1) for value in flat_data)

    end_marker = '1111111111111110'
    message_bits = binary_data.split(end_marker)[0]

    return binary_to_text(message_bits)


# GUI

def encode_gui():
    # Open file explorer to choose image
    input_path = filedialog.askopenfilename(title="Select image to encode", filetypes=[("PNG files","*.png")])
    if not input_path:
        return

    # Ask user for plaintext
    message = simpledialog.askstring("Input", "Enter message to hide:")
    if not message:
        return

    # Choose where to save
    output_path = filedialog.asksaveasfilename(title="Save encoded image as", defaultextension=".png", filetypes=[("PNG files","*.png")])
    if not output_path:
        return

    try:
        encode_image(input_path, message, output_path)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def decode_gui():
    # Open file explorer to choose encoded image
    input_path = filedialog.askopenfilename(title="Select encoded image", filetypes=[("PNG files","*.png")])
    if not input_path:
        return

    try:
        message = decode_image(input_path)
        messagebox.showinfo("Decoded Message", message)
    except Exception as e:
        messagebox.showerror("Error", str(e))


# Main Window

root = tk.Tk()
root.title("LSB Steganography Demo")

# Buttons
tk.Button(root, text="Encode Message into Image", command=encode_gui, width=30, height=2).pack(pady=10)
tk.Button(root, text="Decode Message from Image", command=decode_gui, width=30, height=2).pack(pady=10)
tk.Button(root, text="Exit", command=root.quit, width=30, height=2).pack(pady=10)

root.mainloop()