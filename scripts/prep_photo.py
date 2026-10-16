#!/usr/bin/env python3
"""
Prepare portrait photo for ultra-clean, recognizable ASCII art:
  1. Remove slate-blue studio backdrop cleanly using HSV + color-difference isolation.
  2. Morphologically clean foreground and keep connected subject (hair, face, neck, shirt, blazer).
  3. Crop centered headshot portrait (y: 15..420, x: 80..380) so face fills 75% of the frame.
  4. Apply CLAHE local contrast + gentle unsharp mask to bring out eyes, eyebrows, nose, and lips.
  5. Composite onto pure white (255) so the background maps cleanly to blank spaces.

Output: source-prepped.png (consumed by make_ascii_svg.py)
"""
import os
import sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets", "avatar.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")


def prep():
    img = cv2.imread(INP)
    if img is None:
        print(f"Error: Could not read image at {INP}", file=sys.stderr)
        sys.exit(1)

    h, w = img.shape[:2]

    # 1. Clean backdrop isolation (slate-blue backdrop detection)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    b, g, r = cv2.split(img.astype(np.float32))

    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    b_minus_r = b - r

    is_bg = (hue >= 95) & (hue <= 128) & (sat >= 52) & (b_minus_r >= 15)

    fg = (~is_bg).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel)

    # Keep only the main connected person component
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(fg)
    main_label = 0
    max_area = 0
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area > max_area:
            max_area = area
            main_label = i

    person_mask = (labels == main_label).astype(np.uint8) * 255
    contours, _ = cv2.findContours(person_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled_mask = np.zeros_like(person_mask)
    cv2.drawContours(filled_mask, contours, -1, 255, thickness=cv2.FILLED)

    # 2. Crop headshot portrait to maximize face resolution
    # Focus tightly on head, face, neck, collar, and top of blazer
    crop_y0, crop_y1 = 15, 420
    crop_x0, crop_x1 = 80, 380

    cropped_img = img[crop_y0:crop_y1, crop_x0:crop_x1]
    cropped_mask = filled_mask[crop_y0:crop_y1, crop_x0:crop_x1]

    # 3. Grayscale & CLAHE local contrast enhancement
    gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(6, 6))
    enhanced = clahe.apply(gray)

    # 4. Crisp edge sharpening for distinct eyes, eyebrows, and smile
    gaussian = cv2.GaussianBlur(enhanced, (0, 0), 1.0)
    sharp = cv2.addWeighted(enhanced, 1.4, gaussian, -0.4, 0)

    # 5. Composite onto pure white (255)
    feathered = cv2.GaussianBlur(cropped_mask.astype(np.float32) / 255.0, (0, 0), 0.8)
    out = sharp.astype(np.float32) * feathered + 255.0 * (1.0 - feathered)
    out = np.clip(out, 0, 255).astype(np.uint8)

    cv2.imwrite(OUT, out)
    print(f"Successfully prepped portrait -> {OUT} ({out.shape[1]}x{out.shape[0]})")


if __name__ == "__main__":
    prep()
