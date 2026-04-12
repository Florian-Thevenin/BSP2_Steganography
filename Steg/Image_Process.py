from PIL import Image
import numpy as np


def load_image(image_path: str) -> np.ndarray:
    image = Image.open(image_path).convert("RGB")
    return np.array(image)


def save_image(data: np.ndarray, output_path: str):
    image = Image.fromarray(data.astype('uint8'))
    image.save(output_path)