from PIL import Image, ImageDraw, ImageFont # For Images & GIF
import numpy as np # For arrays
import os
import re # Used for regex text splitting

from Steg.Image_Process import load_image


FONT_PATH = os.path.join(".docs", "Satoshi-Medium.otf") # Font Used
MAX_SINGLE_RENDER_CHARS = 250 # Message under 250 char get render as image, longer ones becomes GIF


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

    # Build a candidate line by appending next word, avoids adding a leading space when current is blank
    # Then Measures pixel dimensions of the candidate line and return a tuple (left, top, right, bottom)
    for w in words:
        test = current + (" " if current else "") + w
        bbox = draw.textbbox((0, 0), test, font=font)

        if bbox[2] <= max_width: # Checks if the right edge of the candidate line still fits inside the max-width of image
            current = test # If fits, accept the word and update current line
        else: # Candidate line was too wide
            lines.append(current) # Save the current line as a completed line
            current = w # Start a new beginning with word that didn't fit

    if current: # If there's a line that never got flushed
        lines.append(current) # Flush it

    return lines # Return list of wrapped lines

def apply_gradient(img):
    """ Applies a dark gradient shadow to the bottom of an image so white text stays readable """
    w, h = img.size # Unpack image dimensions
    grad_h = int(h * 0.35) # Gradient covers the bottom 35% of the image

    gradient = Image.new("L", (1, grad_h)) # Create a 1px wide greyscale image, "L" is for greyscale

    for i in range(grad_h): # Loop through every row of that 1px wide image
        gradient.putpixel((0, i), int(220 * (i / grad_h))) # Set pixel value from 0 (top, invisible) to 220 (bottom, mostly opaque)

    gradient = gradient.resize((w, grad_h)) # Stretch the 1px wide gradient to full image width
    overlay = Image.new("RGB", (w, grad_h), (0, 0, 0)) # Create a solid black rectangle same size as gradient
    img.paste(overlay, (0, h - grad_h), gradient) # Paste black rectangle onto image bottom, using gradient as transparency mask

def draw_text_lines(draw, lines, font, w, y, line_height):
    """ Draws each wrapped line of text centred horizontally onto the image """
    y_offset = y # Start at the given Y position

    for line in lines: # Iterate over each wrapped line
        bbox = draw.textbbox((0, 0), line, font=font) # Measure this line's pixel width
        x = (w - bbox[2]) // 2 # Calculate X position to centre the line horizontally

        draw.text((x, y_offset), line, fill=(255, 255, 255), font=font) # Draw line in white at calculated position
        y_offset += line_height # Move Y tracker down by one line height

def render_single(image, text):
    """ Renders text onto a static image"""
    image = to_numpy_image(image) # Normalize image to numpy array using custom function above

    img = Image.fromarray(image.astype("uint8")) # Convert numpy array to image
    draw = ImageDraw.Draw(img) # Create a drawing context attached to image, any "draw" call will directly paint onto that image

    w, h = img.size # Unbox image dimensions
    font_size = 200 # Starting font size

    while font_size > 10: # Keeps trying smaller font sizes until the text fits.
        font = ImageFont.truetype(FONT_PATH, font_size) # Loads Custom font
        lines = wrap_text_centered(draw, text, font, int(w * 0.9)) # Wrap text using 90% of image width as a limit

        line_height = font.getbbox("Ay")[3] # Measures the pixel height of a line using "Ay"
        # A has a tall ascender, y has a descender, so together they represent the full height range of the font.
        # [3] is the bottom of the bounding box, which equals the line height.
        total_height = line_height * len(lines) # Compute total pixel height all lines will occupy when stacked together

        max_line_width = max(draw.textbbox((0, 0), l, font=font)[2] for l in lines) # Finds the widest line among all

        if max_line_width <= w and total_height <= h * 0.4: # If text doesn't overflow, and takes no more than 40% of image height
            break # Conditions met, exit loop

        font_size -= 2 # Didn't fit, so we shrink font by 2

    font = ImageFont.truetype(FONT_PATH, font_size) # After end of loop, reloads the font with the right size
    lines = wrap_text_centered(draw, text, font, int(w * 0.9)) # Re wraps the text at the final font

    line_height = font.getbbox("Ay")[3] # Recalculate line height
    total_height = line_height * len(lines) # Recalculates total text block height

    y = h - total_height - 20 # Calculates the Y coordinate where the first line of text should start
                              # Positions the text block 20 pixels above the bottom of the image

    # Apply a gradient shadow so white text is lisible
    apply_gradient(img)

    # Draw each line of text centred onto the image
    draw_text_lines(draw, lines, font, w, y, line_height)

    return np.array(img) # Converts finished image back to numpy array


def smart_chunk_text(text, max_words=20):
    """ Splits long text into smaller chunks for GIF frames, break at punctuation"""
    parts = re.split(r'(?<=[.,])\s+', text) # Splits the text at any whitespace that follows a comma or full stop.
    chunks, buf = [], "" # chunks if final list of frame texts, buf for buffer is current chunk being accumulated.

    for p in parts: # Iterates over each punctuation part
        cand = (buf + " " + p).strip() if buf else p # Builds a candidate chunk. If buf is not empty, appends new part with a space

        if len(cand.split()) <= max_words: # checks if candidate chunk is within word limit
            buf = cand # if within limit, accept it and keep accumulating
        else: # if exceed word limit
            if buf: # makes sure buffer is not empty
                chunks.append(buf) # Saves current chunk as a completed frame
            buf = p # Start a new chunk with the part that didn't fit

    if buf: # End of loop flush
        chunks.append(buf) # Save final chunk

    return chunks # Return list of text chunks


def render_gif(image, text):
    """ Render a multi frame GIF, one frame per text chunk"""
    image = to_numpy_image(image) # Normalize to numpy array

    base = Image.fromarray(image.astype("uint8")) # Base -> every frame is the same
    chunks = smart_chunk_text(text) # split text into framed sized chunks

    frames = [] # Will hold finished image for each frame

    for chunk in chunks: # Iterate over each text chunk to produce one frame
        frame = base.copy() # Create fresh copy of base image
        draw = ImageDraw.Draw(frame) # Create a drawing context for this frame

        w, h = frame.size # Gets frame dimensions
        font = ImageFont.truetype(FONT_PATH, 40) # Loads the font at a fixed size 40 -> Stay Consistent

        lines = wrap_text_centered(draw, chunk, font, int(w * 0.9)) # Wraps this chunks text to fit 90% of frame width

        line_height = font.getbbox("Ay")[3] # Gets line height the same way as in render_single
        total_height = line_height * len(lines) # Total pixel height of the text block for this frame.

        y = h - total_height - 20 # Starting Y for the text block, 20px above the bottom.

        # Apply gradient shadow to frame
        apply_gradient(frame)

        # Draw each line of this chunk centred onto the frame
        draw_text_lines(draw, lines, font, w, y, line_height)

        frames.append(frame) # Adds the completed frame to the list.

    # Return frames ONLY (main handles saving)
    return frames


def render_text_on_image(image, text):
    """ Function that choose to render onto static image or GIF depending on message length"""
    if len(text) < MAX_SINGLE_RENDER_CHARS:
        return render_single(image, text)

    print("Text too long → switching to GIF mode")
    return render_gif(image, text)