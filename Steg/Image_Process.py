import os
from PIL import Image
import numpy as np


def load_image(image_path: str) -> np.ndarray:
    image_path = image_path.strip()


    if not image_path:
        raise ValueError("No image path provided")


    try:
        image = Image.open(image_path)

    except FileNotFoundError:
        base, ext = os.path.splitext(image_path)

        if ext == "":
            for candidate_ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
                test_path = base + candidate_ext
                if os.path.exists(test_path):
                    image = Image.open(test_path)
                    print(f"Auto-resolved input image to: {test_path}")
                    break
            else:
                raise FileNotFoundError(f"Image not found: {image_path}")

        else:
            raise FileNotFoundError(f"Image not found: {image_path}")

    image = image.convert("RGB")

    return np.array(image)

def save_image(data: np.ndarray, output_path: str):
    output_path = output_path.strip()

    if not output_path:
        output_path = "output.png"
        print(f"Auto-resolved output file to: {output_path}")

    base, ext = os.path.splitext(output_path)

    if ext.lower() != ".png":
        output_path = base + ".png"
        print(f"Auto-resolved output image to: {output_path}")

    image = Image.fromarray(data.astype('uint8'))
    image.save(output_path, format="PNG")