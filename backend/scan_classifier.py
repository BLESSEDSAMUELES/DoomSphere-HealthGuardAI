"""
Scan Type Classifier Module
Classifies uploaded medical images into categories:
  - X-Ray, CT Scan, MRI, Ultrasound, PET Scan, Mammogram, DEXA, Fluoroscopy
Uses image characteristics (intensity distribution, texture features,
aspect ratio) combined with a rule-based + statistical approach.
"""

import numpy as np
from PIL import Image
import cv2


SCAN_TYPES = [
    "X-Ray",
    "CT Scan",
    "MRI",
    "Ultrasound",
    "PET Scan",
    "Mammogram",
    "DEXA Scan",
    "Fluoroscopy",
]

SCAN_DESCRIPTIONS = {
    "X-Ray": "A radiographic image using X-ray radiation to view internal body structures, commonly used for bones, chest, and dental imaging.",
    "CT Scan": "Computed Tomography scan providing cross-sectional images of the body using X-rays processed by computer.",
    "MRI": "Magnetic Resonance Imaging using strong magnetic fields and radio waves to generate detailed images of organs and tissues.",
    "Ultrasound": "Sonographic imaging using high-frequency sound waves to produce images of internal body structures.",
    "PET Scan": "Positron Emission Tomography scan showing metabolic activity, often used in oncology and neurology.",
    "Mammogram": "Specialized low-dose X-ray imaging of breast tissue for screening and diagnosis.",
    "DEXA Scan": "Dual-Energy X-ray Absorptiometry scan measuring bone mineral density.",
    "Fluoroscopy": "A real-time X-ray imaging technique used to observe moving body structures.",
}


def _compute_features(image: Image.Image) -> dict:
    """Extract image features for classification."""
    img_array = np.array(image.convert("L"))  # convert to grayscale
    h, w = img_array.shape
    aspect_ratio = w / h if h > 0 else 1.0

    # intensity statistics
    mean_intensity = np.mean(img_array)
    std_intensity = np.std(img_array)
    median_intensity = np.median(img_array)

    # histogram features
    hist, _ = np.histogram(img_array.flatten(), bins=256, range=(0, 256))
    hist_norm = hist / hist.sum()
    entropy = -np.sum(hist_norm[hist_norm > 0] * np.log2(hist_norm[hist_norm > 0]))

    # texture features (Laplacian variance = sharpness)
    laplacian_var = cv2.Laplacian(img_array, cv2.CV_64F).var()

    # edge density
    edges = cv2.Canny(img_array, 50, 150)
    edge_density = np.sum(edges > 0) / (h * w)

    # dark/bright region ratio
    dark_ratio = np.sum(img_array < 50) / (h * w)
    bright_ratio = np.sum(img_array > 200) / (h * w)

    # contrast
    p5 = np.percentile(img_array, 5)
    p95 = np.percentile(img_array, 95)
    contrast = p95 - p5

    return {
        "aspect_ratio": aspect_ratio,
        "mean_intensity": mean_intensity,
        "std_intensity": std_intensity,
        "median_intensity": median_intensity,
        "entropy": entropy,
        "laplacian_var": laplacian_var,
        "edge_density": edge_density,
        "dark_ratio": dark_ratio,
        "bright_ratio": bright_ratio,
        "contrast": contrast,
        "width": w,
        "height": h,
    }


def classify_scan_type(image: Image.Image) -> dict:
    """
    Classify the type of medical scan.
    Returns dict with scan_type, confidence, and description.
    """
    features = _compute_features(image)

    scores = {st: 0.0 for st in SCAN_TYPES}

    # --- Rule-based scoring using extracted features ---

    mean_i = features["mean_intensity"]
    std_i = features["std_intensity"]
    contrast = features["contrast"]
    entropy = features["entropy"]
    edge_density = features["edge_density"]
    dark_ratio = features["dark_ratio"]
    bright_ratio = features["bright_ratio"]
    laplacian = features["laplacian_var"]

    # X-Ray: high contrast, lots of dark area (background), moderate edges
    if dark_ratio > 0.3 and contrast > 150:
        scores["X-Ray"] += 3.0
    if mean_i < 100 and std_i > 50:
        scores["X-Ray"] += 2.0
    if edge_density > 0.05 and edge_density < 0.25:
        scores["X-Ray"] += 1.5

    # CT Scan: circular cross-section, moderate intensity, high detail
    if 0.85 < features["aspect_ratio"] < 1.15:  # roughly square
        scores["CT Scan"] += 2.0
    if 60 < mean_i < 160 and std_i > 40:
        scores["CT Scan"] += 2.0
    if entropy > 6.0:
        scores["CT Scan"] += 1.5
    if edge_density > 0.1:
        scores["CT Scan"] += 1.0

    # MRI: high contrast soft tissue, variable intensity, high entropy
    if entropy > 5.5 and contrast > 120:
        scores["MRI"] += 2.5
    if std_i > 45 and mean_i > 50 and mean_i < 180:
        scores["MRI"] += 2.0
    if laplacian > 100:
        scores["MRI"] += 1.5

    # Ultrasound: speckle noise, lower contrast, grainy texture
    if entropy < 6.0 and std_i < 50:
        scores["Ultrasound"] += 2.5
    if laplacian < 200 and edge_density < 0.1:
        scores["Ultrasound"] += 2.0
    if mean_i > 40 and mean_i < 140:
        scores["Ultrasound"] += 1.0
    if dark_ratio > 0.2 and dark_ratio < 0.6:
        scores["Ultrasound"] += 1.0

    # PET Scan: bright hotspots on dark background, colorful if pseudo-colored
    if bright_ratio > 0.05 and dark_ratio > 0.4:
        scores["PET Scan"] += 3.0
    if mean_i < 80 and std_i > 60:
        scores["PET Scan"] += 2.0

    # Mammogram: specific intensity range, breast-shaped FOV
    if mean_i > 30 and mean_i < 120:
        scores["Mammogram"] += 1.5
    if dark_ratio > 0.4 and contrast > 100 and contrast < 200:
        scores["Mammogram"] += 2.0
    if features["aspect_ratio"] > 0.6 and features["aspect_ratio"] < 1.0:
        scores["Mammogram"] += 1.0

    # DEXA Scan: lower resolution feel, moderate contrast
    if contrast < 150 and entropy < 5.5:
        scores["DEXA Scan"] += 2.0
    if edge_density < 0.08:
        scores["DEXA Scan"] += 1.5

    # Fluoroscopy: similar to X-ray but lower quality, less contrast
    if dark_ratio > 0.2 and contrast > 80 and contrast < 180:
        scores["Fluoroscopy"] += 1.5
    if mean_i < 120 and std_i > 30 and std_i < 60:
        scores["Fluoroscopy"] += 1.5

    # Normalize scores
    total = sum(scores.values())
    if total == 0:
        # default to X-Ray if no clear signal
        scores["X-Ray"] = 1.0
        total = 1.0

    confidences = {k: round(v / total * 100, 1) for k, v in scores.items()}

    # Get the best match
    best_type = max(confidences, key=confidences.get)
    best_confidence = confidences[best_type]

    # Sort all results
    sorted_results = sorted(confidences.items(), key=lambda x: x[1], reverse=True)

    return {
        "scan_type": best_type,
        "confidence": best_confidence,
        "description": SCAN_DESCRIPTIONS.get(best_type, ""),
        "all_scores": sorted_results,
        "features": {
            "mean_intensity": round(features["mean_intensity"], 1),
            "contrast": round(features["contrast"], 1),
            "entropy": round(features["entropy"], 2),
            "edge_density": round(features["edge_density"], 4),
            "resolution": f"{features['width']}x{features['height']}",
        },
    }
