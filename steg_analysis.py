import numpy as np
import matplotlib.pyplot as plt
from Steg.Image_Process import load_image



def histogram_difference(img1, img2):
    """ Compare pixel distributions between two images"""
    # Converts both images from 3D arrays (Height, Width, RGB) into 1D arrays
    a = img1.flatten() # Image A is the original
    b = img2.flatten() # Image B is the suspect Image

    # Split pixel intensity range into 256 bins and counts the number of pixels per intensity value
    hist_a, _ = np.histogram(a, bins=256, range=(0, 256))
    hist_b, _ = np.histogram(b, bins=256, range=(0, 256))

    # Compute absolute difference, and measure how much pixel distribution changed due to embedding
    diff = np.abs(hist_a - hist_b)

    return hist_a, hist_b, diff


def plot_histograms(hist_a, hist_b, diff):
    """ Visualization Module"""
    x = np.arange(256) # Creates array that represent pixel intensity values on x-axis

    plt.figure(figsize=(12, 5)) # Create a graph window of size 12x5 inches


    plt.subplot(1, 2, 1) # Create first subplot

    # Plots original image as blue
    plt.bar(
        x,
        hist_a,
        color="blue",
        alpha=1.0,
        label="Image A (Original)",
        zorder=1
    )

    #Plots suspect image as orange striations (hatch pattern)
    plt.bar(
        x,
        hist_b,
        facecolor="none",
        edgecolor="orange",
        hatch="//",
        linewidth=0.5,
        label="Image B (Suspect)",
        zorder=3
    )

    plt.title("Histogram Comparison")
    plt.xlabel("Pixel intensity (0–255)")
    plt.ylabel("Number of pixels")
    plt.legend()

    # Plot second subplot -> Histogram
    plt.subplot(1, 2, 2)

    # Plot absolute difference histogram
    plt.bar(x, diff, color="black")

    plt.title("Histogram Difference (|A - B|)")
    plt.xlabel("Pixel intensity (0–255)")
    plt.ylabel("Absolute difference in pixel count")

    plt.tight_layout()
    plt.show()



def stego_score(diff):
    """ Returns a numeric value representing "how modified" an image is"""
    total_change = np.sum(diff) # Sums all histogram differences
    normalized = total_change / len(diff) # Normalize score by number of bins (256)

    return normalized



def analyze_two_images(path_original, path_suspect):
    """ Compare original vs Suspect image to check if it was modified"""
    # Load both images into numpy arrays
    img1 = load_image(path_original)
    img2 = load_image(path_suspect)

    hist_a, hist_b, diff = histogram_difference(img1, img2) # Compute differences

    score = stego_score(diff) # Compute score

    # Displays result
    print("\n--- Steganalysis Report ---")
    print(f"Total histogram change score: {score:.2f}")

    # Open a window for visual representation
    plot_histograms(hist_a, hist_b, diff)

    # Simple decision rule (currently not tuned) arbitrary choosen
    if score > 5:
        print("Likely LSB-modified image")
    else:
        print("Likely unmodified image")


# To make the program run when executed directly
if __name__ == "__main__":
    analyze_two_images(
        ".docs/sky.png",
        ".docs/sky_modified.png"
    )