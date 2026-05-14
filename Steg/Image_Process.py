import os
from PIL import Image
import numpy as np


def load_image(image_path: str) -> np.ndarray:
    """ Load an image from disk and return it as an array """
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
    """ Saves an array back into a png image"""
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


def save_gif(frames: list, output_path: str, duration: int = 3500):
    """ Saves a list of PIL Images as an animated GIF without cross-frame zoom/palette artifacts."""
    output_path = output_path.strip()

    if not output_path:
        output_path = "output.gif"
        print(f"Auto-resolved output file to: {output_path}")

    base, ext = os.path.splitext(output_path)

    if ext.lower() != ".gif":
        output_path = base + ".gif"
        print(f"Auto-resolved output gif to: {output_path}")

    if not frames:
        raise ValueError("No frames to save")

    # ── Normalise all frames to the same size and palette ────────────────────
    # Without this, PIL quantises each frame independently, which causes
    # different palette entries per frame. When a GIF player renders frame N
    # using frame N-1's canvas dimensions it can appear zoomed or shifted.
    #
    # Fix: convert every frame to RGBA first (so transparency is available),
    # then let PIL quantise from a single combined palette derived from
    # the first frame. We also set disposal=2 (restore to background) so
    # each frame is drawn on a clean slate, eliminating any bleed-through
    # from the previous frame.

    # Ensure all frames are the same size (use frame 0 as reference)
    w, h = frames[0].size
    normalised = []
    for f in frames:
        if f.size != (w, h):
            f = f.resize((w, h), Image.LANCZOS)
        # Keep as RGB — GIF palette quantisation handles the conversion
        normalised.append(f.convert("RGB"))

    # Build a global palette from the first frame and apply it to all frames
    # using Quantize so every frame shares the same 256-colour palette.
    palette_source = normalised[0].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    quantised = [palette_source]
    for f in normalised[1:]:
        quantised.append(f.quantize(palette=palette_source, dither=0))

    quantised[0].save(
        output_path,
        save_all=True,
        append_images=quantised[1:],
        duration=duration,
        loop=0,
        disposal=2   # restore to background colour between frames — prevents bleed-through
    )