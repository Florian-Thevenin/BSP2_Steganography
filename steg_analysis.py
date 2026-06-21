import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from Steg.Image_Process import load_image



# Config Values

STEGO_THRESHOLD = 5          # Sensitivity threshold for two-image histogram comparison, higher = less sensitive
CHI_SQUARE_THRESHOLD = 0.05  # P-value threshold for chi-square test, below this = likely stego
RS_THRESHOLD = 0.02          # RS analysis threshold, difference between R and S groups above this = likely stego
SPA_THRESHOLD = 0.05         # Sample pair analysis threshold, embedding rate above this = likely stego
SNV_THRESHOLD = 0.95         # SNV linearity threshold, R² above this = likely stego (too linear)
EVEN_ODD_THRESHOLD = 0.01    # Even-odd ratio deviation threshold, below this = likely stego



def histogram_difference(img1, img2):
    """ Compare pixel distributions between two images """
    a = img1.flatten() # Image A is the original
    b = img2.flatten() # Image B is the suspect image

    hist_a, _ = np.histogram(a, bins=256, range=(0, 256)) # Count pixels per intensity value for image A
    hist_b, _ = np.histogram(b, bins=256, range=(0, 256)) # Count pixels per intensity value for image B

    diff = np.abs(hist_a - hist_b) # Compute absolute difference between both histograms

    return hist_a, hist_b, diff


def stego_score(diff):
    """ Returns a numeric value representing how modified an image is """
    total_change = np.sum(diff) # Sum all histogram differences
    normalized = total_change / len(diff) # Normalize score by number of bins

    return normalized



def lsb_plane_analysis(img):
    """ Extracts LSB plane and measures its uniformity
        Natural images have random noisy LSBs
        Stego images have more uniform or structured LSBs due to embedding
    """
    flat = img.flatten().astype(np.int32) # Flatten image to 1D array

    lsb_plane = flat & 1 # Extract least significant bit of every pixel value

    lsb_mean = np.mean(lsb_plane) # Mean of LSB plane, should be close to 0.5 for both natural and stego
    lsb_var = np.var(lsb_plane) # Variance of LSB plane

    # In natural images LSB variance is slightly below 0.25
    # Embedding pushes it closer to exactly 0.25 (perfectly random)
    deviation = abs(lsb_var - 0.25) # Deviation from perfect randomness

    # Compute local variance across 8x8 blocks to detect spatial patterns
    h, w = img.shape[:2]
    block_vars = [] # Will hold variance of each block

    for i in range(0, h - 8, 8): # Iterate over rows in steps of 8
        for j in range(0, w - 8, 8): # Iterate over columns in steps of 8
            block = img[i:i+8, j:j+8, :].flatten() & 1 # Extract LSB plane of this block
            block_vars.append(np.var(block)) # Compute variance of this block

    block_var_std = np.std(block_vars) # Standard deviation of block variances
    # Natural images have high std (uneven LSB distribution across blocks)
    # Stego images have low std (LSBs are uniformly distributed across blocks due to embedding)

    likely_stego = deviation < 0.01 and block_var_std < 0.05 # Both conditions suggest embedding

    return {
        "lsb_mean": lsb_mean,
        "lsb_variance": lsb_var,
        "deviation_from_random": deviation,
        "block_variance_std": block_var_std,
        "likely_stego": likely_stego
    }


def chi_square_attack(img):
    """ Chi-square test on pixel value pairs
        LSB embedding makes adjacent value pairs (0,1), (2,3), (4,5)... appear with equal frequency
        Chi-square measures how far actual distribution is from that perfectly paired expectation
    """
    flat = img.flatten().astype(np.int32) # Flatten image to 1D array

    hist, _ = np.histogram(flat, bins=256, range=(0, 256)) # Count frequency of each pixel value

    # Group pixel values into pairs (0,1), (2,3), (4,5)...
    observed = [] # Actual counts
    expected = [] # Expected counts if embedding occurred

    for i in range(0, 256, 2): # Step through pairs
        n1 = hist[i]     # Count of even value
        n2 = hist[i + 1] # Count of odd value
        mean = (n1 + n2) / 2 # Expected count if perfectly paired

        if mean > 0: # Avoid division by zero
            observed.append(n1)
            observed.append(n2)
            expected.append(mean)
            expected.append(mean)

    observed = np.array(observed)
    expected = np.array(expected)

    # Compute chi-square statistic manually
    chi2 = np.sum((observed - expected) ** 2 / expected) # Chi-square formula
    dof = len(observed) - 1 # Degrees of freedom

    p_value = 1 - stats.chi2.cdf(chi2, dof) # P-value from chi-square distribution
    # Low p-value means distribution is suspiciously close to perfectly paired = likely stego

    likely_stego = p_value < CHI_SQUARE_THRESHOLD

    return {
        "chi2_statistic": chi2,
        "p_value": p_value,
        "likely_stego": likely_stego
    }


#TOO SLOW -> to be improved
def rs_analysis(img):
    """ Regular-Singular analysis
        Divides image into pixel groups and classifies each as Regular, Singular or Unusable
        LSB embedding disturbs the natural R > S balance in a mathematically predictable way
        Can estimate embedding rate from how much R and S diverge
    """
    flat = img.flatten().astype(np.int32) # Flatten to 1D array
    n = len(flat)
    group_size = 4 # Number of pixels per group

    # Discrimination function — measures smoothness of a pixel group
    # Higher value = less smooth = more natural
    def discrimination(group):
        return np.sum(np.abs(np.diff(group))) # Sum of absolute differences between adjacent pixels

    # Flipping function F1 — flips LSB of pixel (0↔1, 2↔3, 4↔5...)
    def flip(group):
        return np.where(group % 2 == 0, group + 1, group - 1)

    # Inverse flipping function F-1 — shifts values (-1↔0, 1↔2, 3↔4...)
    def flip_inv(group):
        return np.where(group % 2 == 1, group - 1, group + 1)

    r, s, r_inv, s_inv = 0, 0, 0, 0 # Counters for each group type

    for i in range(0, n - group_size, group_size): # Iterate over groups
        group = flat[i:i + group_size].copy() # Extract this group

        f_orig = discrimination(group) # Smoothness of original group

        flipped = flip(group) # Apply F1 flipping
        f_flip = discrimination(flipped) # Smoothness after flipping

        flipped_inv = flip_inv(group) # Apply F-1 flipping
        f_flip_inv = discrimination(flipped_inv) # Smoothness after inverse flipping

        # Classify group under F1
        if f_flip > f_orig:   # Flipping made it less smooth = Regular
            r += 1
        elif f_flip < f_orig: # Flipping made it more smooth = Singular
            s += 1

        # Classify group under F-1
        if f_flip_inv > f_orig:
            r_inv += 1
        elif f_flip_inv < f_orig:
            s_inv += 1

    total_groups = (n // group_size) # Total number of groups

    # Normalize counts
    r_norm = r / total_groups
    s_norm = s / total_groups
    r_inv_norm = r_inv / total_groups
    s_inv_norm = s_inv / total_groups

    rs_difference = abs(r_norm - s_norm) # In natural images R >> S, embedding closes this gap

    # Estimate embedding rate using RS formula
    # Derived from the mathematical relationship between R, S, R-1, S-1 and embedding rate p
    a = 2 * (r_inv_norm - r_norm)
    b = r_norm - r_inv_norm + s_norm - s_inv_norm
    c = s_inv_norm - s_norm

    discriminant = b ** 2 - 4 * a * c # Quadratic discriminant

    if discriminant >= 0 and a != 0: # Solve quadratic equation for embedding rate
        p1 = (-b + np.sqrt(discriminant)) / (2 * a)
        p2 = (-b - np.sqrt(discriminant)) / (2 * a)
        embedding_rate = min(p1, p2) if min(p1, p2) > 0 else max(p1, p2) # Take positive root
        embedding_rate = max(0.0, min(1.0, embedding_rate)) # Clamp to 0-1 range
    else:
        embedding_rate = 0.0 # Could not estimate

    likely_stego = rs_difference < RS_THRESHOLD or embedding_rate > SPA_THRESHOLD

    return {
        "r": r_norm,
        "s": s_norm,
        "r_inv": r_inv_norm,
        "s_inv": s_inv_norm,
        "rs_difference": rs_difference,
        "estimated_embedding_rate": embedding_rate,
        "likely_stego": likely_stego
    }



def sample_pair_analysis(img):
    """ Sample Pair Analysis
        Counts adjacent pixel pairs that fall into specific categories
        Solves a quadratic equation to estimate embedding rate
        More accurate than RS on small payloads
    """
    flat = img.flatten().astype(np.int32) # Flatten to 1D array

    # Count pairs of adjacent pixels
    u = flat[:-1] # All pixels except last
    v = flat[1:]  # All pixels except first

    # Count pairs where values differ only in LSB (within same even/odd pair)
    # These are the pairs most affected by LSB embedding
    same_pair = np.sum((u // 2) == (v // 2)) # Pairs sharing the same value/2 bucket
    total_pairs = len(u) # Total number of adjacent pairs

    # Count pairs where u < v and both in same pair bucket
    e_u_less = np.sum(((u // 2) == (v // 2)) & (u < v)) # u is even, v is odd
    e_u_more = np.sum(((u // 2) == (v // 2)) & (u > v)) # u is odd, v is even

    # Solve quadratic equation for embedding rate p
    # Based on how e_u_less and e_u_more relate to p mathematically
    a = total_pairs
    b = -(e_u_less + e_u_more + 2 * same_pair)
    c = same_pair

    discriminant = b ** 2 - 4 * a * c # Quadratic discriminant

    if discriminant >= 0 and a != 0:
        p1 = (-b + np.sqrt(discriminant)) / (2 * a)
        p2 = (-b - np.sqrt(discriminant)) / (2 * a)
        embedding_rate = min(p1, p2) if min(p1, p2) > 0 else max(p1, p2) # Take positive root
        embedding_rate = max(0.0, min(1.0, embedding_rate)) # Clamp to 0-1 range
    else:
        embedding_rate = 0.0 # Could not estimate

    likely_stego = embedding_rate > SPA_THRESHOLD

    return {
        "estimated_embedding_rate": embedding_rate,
        "likely_stego": likely_stego
    }



def even_odd_analysis(img):
    """ Even-Odd ratio analysis
        Counts pixels with even vs odd values
        Natural images have a slightly uneven ratio due to natural pixel distribution
        LSB embedding forces the ratio closer to exactly 50/50
    """
    flat = img.flatten().astype(np.int32) # Flatten to 1D array

    even_count = np.sum(flat % 2 == 0) # Count pixels with even value
    odd_count = np.sum(flat % 2 == 1)  # Count pixels with odd value
    total = len(flat) # Total pixel count

    even_ratio = even_count / total # Proportion of even pixels
    odd_ratio = odd_count / total   # Proportion of odd pixels

    deviation = abs(even_ratio - 0.5) # Deviation from perfect 50/50 split
    # Natural images deviate slightly from 0.5
    # Stego images are suspiciously close to exactly 0.5

    likely_stego = deviation < EVEN_ODD_THRESHOLD

    return {
        "even_ratio": even_ratio,
        "odd_ratio": odd_ratio,
        "deviation_from_50_50": deviation,
        "likely_stego": likely_stego
    }


def snv_linearity_analysis(img):
    """ Sample Number Variance linearity analysis
        In natural images, variance of pixel values across spatial regions follows a non-linear curve
        LSB embedding introduces artificial linearity into this variance pattern
        We measure R² of a linear fit — high R² means suspiciously linear = likely stego
    """
    gray = np.mean(img, axis=2).astype(np.int32) # Convert to grayscale by averaging RGB channels
    h, w = gray.shape

    block_size = 16 # Size of spatial blocks to analyse
    variances = [] # Will hold variance of each block

    for i in range(0, h - block_size, block_size): # Iterate over rows
        for j in range(0, w - block_size, block_size): # Iterate over columns
            block = gray[i:i + block_size, j:j + block_size].flatten() # Extract block
            variances.append(np.var(block)) # Compute variance of this block

    if len(variances) < 2: # Not enough blocks to analyse
        return {"r_squared": 0.0, "likely_stego": False}

    variances = np.array(variances)
    x = np.arange(len(variances)) # Block indices as x axis

    # Fit a linear regression to the variance sequence
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, variances)
    r_squared = r_value ** 2 # R² measures how well a straight line fits the variance curve
    # Natural images have low R² (non-linear variance)
    # Stego images have high R² (variance is artificially linearised by embedding)

    likely_stego = r_squared > SNV_THRESHOLD

    return {
        "r_squared": r_squared,
        "slope": slope,
        "intercept": intercept,
        "likely_stego": likely_stego
    }



def combined_verdict(results: dict) -> tuple:
    """ Combines individual method verdicts into a single overall verdict
        Each method that says likely_stego gets one vote
        Final verdict is based on majority of votes
    """
    methods = ["lsb", "chi_square", "rs", "spa", "even_odd", "snv"] # All method names
    votes = sum(1 for m in methods if results[m]["likely_stego"]) # Count stego votes
    total = len(methods) # Total number of methods

    confidence = votes / total # Confidence as proportion of agreeing methods

    if votes >= 4: # Majority says stego
        verdict = "LIKELY STEGO"
    elif votes >= 2:
        verdict = "UNCERTAIN"
    else:
        verdict = "LIKELY CLEAN"

    return verdict, votes, total, confidence



def plot_single_image_analysis(img, results):
    """ Plots all single image analysis results in one window """
    flat = img.flatten().astype(np.int32) # Flatten image for plotting
    lsb_plane = flat & 1 # Extract LSB plane

    fig, axes = plt.subplots(2, 3, figsize=(18, 10)) # 2 rows, 3 columns of subplots
    fig.suptitle("Single Image Steganalysis Report", fontsize=14)

    # Plot 1 — LSB plane distribution
    ax = axes[0, 0]
    ax.bar([0, 1], [np.sum(lsb_plane == 0), np.sum(lsb_plane == 1)], color=["blue", "orange"]) # Count 0s and 1s in LSB plane
    ax.set_title(f"LSB Plane Distribution\n{'STEGO' if results['lsb']['likely_stego'] else 'CLEAN'}")
    ax.set_xlabel("LSB value")
    ax.set_ylabel("Count")
    ax.set_xticks([0, 1])

    # Plot 2 — Pixel value histogram with pair highlighting
    ax = axes[0, 1]
    hist, _ = np.histogram(flat, bins=256, range=(0, 256))
    ax.bar(range(256), hist, color="grey", alpha=0.7) # Plot full histogram
    ax.set_title(f"Chi-Square Pair Analysis\np={results['chi_square']['p_value']:.4f} — {'STEGO' if results['chi_square']['likely_stego'] else 'CLEAN'}")
    ax.set_xlabel("Pixel intensity")
    ax.set_ylabel("Count")

    # Plot 3 — RS groups bar chart
    ax = axes[0, 2]
    rs = results["rs"]
    ax.bar(["R", "S", "R-inv", "S-inv"], [rs["r"], rs["s"], rs["r_inv"], rs["s_inv"]], color=["blue", "red", "cyan", "orange"])
    ax.set_title(f"RS Analysis\nEmbedding rate ≈ {rs['estimated_embedding_rate']*100:.1f}% — {'STEGO' if rs['likely_stego'] else 'CLEAN'}")
    ax.set_ylabel("Normalised group count")

    # Plot 4 — SPA embedding rate
    ax = axes[1, 0]
    spa_rate = results["spa"]["estimated_embedding_rate"]
    ax.bar(["Clean", "Embedded"], [1 - spa_rate, spa_rate], color=["green", "red"]) # Show estimated clean vs embedded proportion
    ax.set_title(f"Sample Pair Analysis\nEmbedding rate ≈ {spa_rate*100:.1f}% — {'STEGO' if results['spa']['likely_stego'] else 'CLEAN'}")
    ax.set_ylabel("Proportion")
    ax.set_ylim(0, 1)

    # Plot 5 — Even-Odd ratio
    ax = axes[1, 1]
    eo = results["even_odd"]
    ax.bar(["Even", "Odd"], [eo["even_ratio"], eo["odd_ratio"]], color=["blue", "orange"])
    ax.axhline(0.5, color="red", linestyle="--", label="Perfect 50/50") # Reference line at 50/50
    ax.set_title(f"Even-Odd Ratio\nDeviation={eo['deviation_from_50_50']:.4f} — {'STEGO' if eo['likely_stego'] else 'CLEAN'}")
    ax.set_ylabel("Ratio")
    ax.set_ylim(0.45, 0.55)
    ax.legend()

    # Plot 6 — SNV linearity
    ax = axes[1, 2]
    gray = np.mean(img, axis=2).astype(np.int32) # Convert to grayscale
    h, w = gray.shape
    block_size = 16
    variances = []

    for i in range(0, h - block_size, block_size):
        for j in range(0, w - block_size, block_size):
            block = gray[i:i + block_size, j:j + block_size].flatten()
            variances.append(np.var(block))

    variances = np.array(variances)
    x = np.arange(len(variances))
    ax.scatter(x, variances, s=1, color="blue", alpha=0.5) # Plot block variances as scatter

    slope = results["snv"]["slope"]
    intercept = results["snv"].get("intercept", np.mean(variances))
    ax.plot(x, slope * x + intercept, color="red", linewidth=1.5, label=f"R²={results['snv']['r_squared']:.3f}") # Plot linear fit
    ax.set_title(f"SNV Linearity\nR²={results['snv']['r_squared']:.3f} — {'STEGO' if results['snv']['likely_stego'] else 'CLEAN'}")
    ax.set_xlabel("Block index")
    ax.set_ylabel("Block variance")
    ax.legend()

    plt.tight_layout()
    plt.show()


def plot_two_image_analysis(hist_a, hist_b, diff):
    """ Plots two image histogram comparison in one window """
    x = np.arange(256) # Pixel intensity values on x axis

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1) # First subplot — overlaid histograms
    plt.bar(x, hist_a, color="blue", alpha=1.0, label="Image A (Original)", zorder=1)
    plt.bar(x, hist_b, facecolor="none", edgecolor="orange", hatch="//", linewidth=0.5, label="Image B (Suspect)", zorder=3)
    plt.title("Histogram Comparison")
    plt.xlabel("Pixel intensity (0–255)")
    plt.ylabel("Number of pixels")
    plt.legend()

    plt.subplot(1, 2, 2) # Second subplot — absolute difference
    plt.bar(x, diff, color="black")
    plt.title("Histogram Difference (|A - B|)")
    plt.xlabel("Pixel intensity (0–255)")
    plt.ylabel("Absolute difference in pixel count")

    plt.tight_layout()
    plt.show()


def analyze_single_image(image_path: str):
    """ Full single image steganalysis pipeline using all six methods """
    img = load_image(image_path) # Load image as numpy array

    print("\n--- Single Image Steganalysis ---")
    print("Running all methods...")

    # Run all six methods
    results = {
        "lsb":        lsb_plane_analysis(img),
        "chi_square": chi_square_attack(img),
        "rs":         rs_analysis(img),
        "spa":        sample_pair_analysis(img),
        "even_odd":   even_odd_analysis(img),
        "snv":        snv_linearity_analysis(img)
    }

    # Print individual verdicts
    print("\n--- Individual Method Verdicts ---")
    print(f"LSB Plane Analysis    : {'LIKELY STEGO' if results['lsb']['likely_stego']        else 'LIKELY CLEAN'} | Block variance std={results['lsb']['block_variance_std']:.4f}")
    print(f"Chi-Square Attack     : {'LIKELY STEGO' if results['chi_square']['likely_stego']  else 'LIKELY CLEAN'} | p={results['chi_square']['p_value']:.4f}")
    print(f"RS Analysis           : {'LIKELY STEGO' if results['rs']['likely_stego']          else 'LIKELY CLEAN'} | Embedding rate ≈ {results['rs']['estimated_embedding_rate']*100:.1f}%")
    print(f"Sample Pair Analysis  : {'LIKELY STEGO' if results['spa']['likely_stego']         else 'LIKELY CLEAN'} | Embedding rate ≈ {results['spa']['estimated_embedding_rate']*100:.1f}%")
    print(f"Even-Odd Ratio        : {'LIKELY STEGO' if results['even_odd']['likely_stego']    else 'LIKELY CLEAN'} | Deviation={results['even_odd']['deviation_from_50_50']:.4f}")
    print(f"SNV Linearity         : {'LIKELY STEGO' if results['snv']['likely_stego']         else 'LIKELY CLEAN'} | R²={results['snv']['r_squared']:.4f}")

    # Print combined verdict
    verdict, votes, total, confidence = combined_verdict(results)
    print(f"\n--- Combined Verdict ---")
    print(f"Votes       : {votes}/{total} methods flagged as stego")
    print(f"Confidence  : {confidence*100:.0f}%")
    print(f"Verdict     : {verdict}")

    plot_single_image_analysis(img, results) # Show all plots in one window


def analyze_two_images(path_original: str, path_suspect: str):
    """ Two image histogram comparison pipeline """
    img1 = load_image(path_original) # Load original image
    img2 = load_image(path_suspect)  # Load suspect image

    hist_a, hist_b, diff = histogram_difference(img1, img2) # Compute histogram difference
    score = stego_score(diff) # Compute modification score

    print("\n--- Two Image Steganalysis Report ---")
    print(f"Histogram change score : {score:.2f}")
    print(f"Verdict                : {'LIKELY STEGO' if score > STEGO_THRESHOLD else 'LIKELY CLEAN'}")

    plot_two_image_analysis(hist_a, hist_b, diff) # Show histogram plots



if __name__ == "__main__":
    print("\n--- Steganalysis ---")
    print("1: Single image analysis")
    print("2: Two image comparison")

    choice = input("> ").strip().lower()

    if choice in ["1", "single"]:
        path = input("Image path: ").strip()
        analyze_single_image(path)

    elif choice in ["2", "two", "compare"]:
        path_original = input("Original image path: ").strip()
        path_suspect = input("Suspect image path: ").strip()
        analyze_two_images(path_original, path_suspect)

    else:
        print("Invalid choice")