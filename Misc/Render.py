from PIL import Image, ImageDraw, ImageFont  # For Images & GIF
import numpy as np  # For arrays
import os
import re  # Used for regex text splitting

from Steg.Image_Process import load_image
from Misc.Utils import resource_path

FONT_PATH = resource_path(os.path.join(".docs", "Satoshi-Medium.otf"))  # Font Used
MAX_SINGLE_RENDER_CHARS = 250  # Message under 250 char get render as image, longer ones becomes GIF


def to_numpy_image(img):
    """ Normalizer, makes the render module more flexible:
        A numpy array -> returns it as-is
        A string file path -> loads it via load_image utility
        Anything else -> raises a clear error
    """
    if isinstance(img, np.ndarray):
        return img
    if isinstance(img, str):
        return load_image(img)
    raise TypeError(f"Unsupported image type: {type(img)}")


def wrap_text_centered(draw, text, font, max_width):
    """ Manually wraps text word by word depending on width and not char count"""
    words = text.split()
    lines = []
    current = ""

    for w in words:
        test = current + (" " if current else "") + w
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            lines.append(current)
            current = w

    if current:
        lines.append(current)

    return lines


def apply_gradient(img):
    """ Applies a dark gradient shadow to the bottom of an image so white text stays readable """
    w, h = img.size
    grad_h = int(h * 0.35)
    gradient = Image.new("L", (1, grad_h))
    for i in range(grad_h):
        gradient.putpixel((0, i), int(220 * (i / grad_h)))
    gradient = gradient.resize((w, grad_h))
    overlay = Image.new("RGB", (w, grad_h), (0, 0, 0))
    img.paste(overlay, (0, h - grad_h), gradient)


def draw_text_lines(draw, lines, font, w, y, line_height):
    """ Draws each wrapped line of text centred horizontally onto the image """
    y_offset = y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (w - bbox[2]) // 2
        draw.text((x, y_offset), line, fill=(255, 255, 255), font=font)
        y_offset += line_height


def render_single(image, text, font_size_override=None):
    """ Renders text onto a static image """
    image = to_numpy_image(image)
    img = Image.fromarray(image.astype("uint8"))
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # Determine starting font size
    font_size = font_size_override if font_size_override else 125

    # Always run the fit-check loop to ensure text actually fits,
    # even when a manual size is provided.
    while font_size > 10:
        font = ImageFont.truetype(FONT_PATH, font_size)
        lines = wrap_text_centered(draw, text, font, int(w * 0.9))
        line_height = font.getbbox("Ay")[3]
        total_height = line_height * len(lines)
        max_line_width = max(draw.textbbox((0, 0), l, font=font)[2] for l in lines)

        if max_line_width <= w and total_height <= h * 0.4:
            break  # Fits

        if font_size_override:
            # User set a size that's too big — shrink until it fits
            font_size -= 2
        else:
            font_size -= 2

    font = ImageFont.truetype(FONT_PATH, font_size)
    lines = wrap_text_centered(draw, text, font, int(w * 0.9))
    line_height = font.getbbox("Ay")[3]
    total_height = line_height * len(lines)
    y = h - total_height - 20

    apply_gradient(img)
    draw_text_lines(draw, lines, font, w, y, line_height)

    return np.array(img)


def smart_chunk_text(text, max_words=8):
    """ Splits long text into smaller chunks for GIF frames, break at punctuation"""
    parts = re.split(r'(?<=[.,])\s+', text)
    chunks, buf = [], []

    for p in parts:
        buf_words = buf + p.split()
        if len(buf_words) <= max_words:
            buf = buf_words
        else:
            for word in p.split():
                if len(buf) >= max_words:
                    chunks.append(' '.join(buf))
                    buf = []
                buf.append(word)

    if buf:
        chunks.append(' '.join(buf))

    return chunks


def render_gif(image, text, font_size_override=None):
    """ Render a multi frame GIF, one frame per text chunk"""
    image = to_numpy_image(image)
    base = Image.fromarray(image.astype("uint8"))
    chunks = smart_chunk_text(text)
    frames = []

    for chunk in chunks:
        frame = base.copy()
        draw = ImageDraw.Draw(frame)
        w, h = frame.size

        font_size = font_size_override if font_size_override else 70

        while font_size > 10:
            font = ImageFont.truetype(FONT_PATH, font_size)
            lines = wrap_text_centered(draw, chunk, font, int(w * 0.9))
            line_height = font.getbbox("Ay")[3]
            total_height = line_height * len(lines)
            max_line_width = max(draw.textbbox((0, 0), l, font=font)[2] for l in lines)

            if max_line_width <= w and total_height <= h * 0.4:
                break

            font_size -= 2

        font = ImageFont.truetype(FONT_PATH, font_size)
        lines = wrap_text_centered(draw, chunk, font, int(w * 0.9))
        line_height = font.getbbox("Ay")[3]
        total_height = line_height * len(lines)
        y = h - total_height - 20

        apply_gradient(frame)
        draw_text_lines(draw, lines, font, w, y, line_height)
        frames.append(frame)

    return frames


def render_text_on_image(image, text, font_size_override=None):
    """ Function that chooses to render onto static image or GIF depending on message length"""
    if len(text) < MAX_SINGLE_RENDER_CHARS:
        return render_single(image, text, font_size_override=font_size_override)
    print("Text too long → switching to GIF mode")
    return render_gif(image, text, font_size_override=font_size_override)