import os
from PIL import Image
import numpy as np


def load_image(image_path: str) -> np.ndarray:
    """ Load an image from disk and return it as an array """
    image_path = image_path.strip() # Remove extra whitespace from input path


    if not image_path: # If input empty -> raise an error
        raise ValueError("No image path provided")


    try:
        image = Image.open(image_path) # Open image using pillow

    except FileNotFoundError: # If image find not found -> tries to auto-resolve
        base, ext = os.path.splitext(image_path) # split input into filename and extension format

        if ext == "": # If image format was not given (empty) -> tries for common image format
            for candidate_ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
                test_path = base + candidate_ext # Add common  extension format to filename and check if it exists
                if os.path.exists(test_path):
                    image = Image.open(test_path) # If it exists, then open that file
                    print(f"Auto-resolved input image to: {test_path}")
                    break # Stop searching when found a valid file
            else:
                raise FileNotFoundError(f"Image not found: {image_path}")

        else:
            raise FileNotFoundError(f"Image not found: {image_path}")

    image = image.convert("RGB") # Converts the image to RGB format (removes alpha) -> 3 channel by pixel

    return np.array(image) # returns the array corresponding to the image

def save_image(data: np.ndarray, output_path: str):
    """ Saves an array back into a png image"""
    output_path = output_path.strip() # Remove extra whitespace from output path

    if not output_path: # If no output path given, save the image as output.png to current directory
        output_path = "output.png"
        print(f"Auto-resolved output file to: {output_path}")

    base, ext = os.path.splitext(output_path) # Split path into filename and extension

    if ext.lower() != ".png": # if extension is not in png format, change it to png
        output_path = base + ".png"
        print(f"Auto-resolved output image to: {output_path}")

    image = Image.fromarray(data.astype('uint8')) # Convert array to image, uint8 is for 0-255 RGB values
    image.save(output_path, format="PNG") # Save image to disk in png format