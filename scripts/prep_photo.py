#!/usr/bin/env python3
"""
Prepare portrait photo for clean ASCII conversion as specified in Avi Vashishta's blog:
  1. Remove the background with high-fidelity color + GrabCut segmentation so subject is isolated.
  2. Bilateral-smooth away flat noise while keeping drawn lines/facial features sharp.
  3. Tone stretch over the subject only so skin lands in light ranges and facial features stay dark.
  4. Darken the line work (DoG ridges) -- eyelids, pupils, glasses, and smile are enhanced.
  5. Composite onto pure white (255) so the background maps cleanly to blank spaces.
  6. Square-crop around the subject with balanced margins.

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

    # 1. Color separation & GrabCut segmentation
    b, g, r = cv2.split(img.astype(np.float32))

    mask = np.zeros((h, w), np.uint8)
    mask[b - r > 8] = cv2.GC_BGD
    mask[r - b > 5] = cv2.GC_FGD
    mask[(b - r <= 8) & (r - b <= 5)] = cv2.GC_PR_FGD
    mask[0:15, :] = cv2.GC_BGD
    mask[:, 0:15] = cv2.GC_BGD
    mask[:, -15:] = cv2.GC_BGD

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, None, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_MASK)

    alpha = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel)
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, kernel)

    # 2. Grayscale & bilateral smoothing (remove noise while preserving edge gradients)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    smooth = gray
    for _ in range(3):
        smooth = cv2.bilateralFilter(smooth, 9, 40, 9)

    # 3. Tone stretch over the isolated subject only
    subj_pixels = smooth[alpha > 128]
    if len(subj_pixels) == 0:
        subj_pixels = smooth
    lo, hi = np.percentile(subj_pixels, [2, 92])
    tone = np.clip((smooth.astype(np.float32) - lo) / max(hi - lo, 1.0), 0, 1)

    # 4. Enhance facial line work (difference of Gaussians)
    line_weight = 0.6
    fine = cv2.GaussianBlur(smooth, (0, 0), 1.5).astype(np.float32)
    coarse = cv2.GaussianBlur(smooth, (0, 0), 6).astype(np.float32)
    lines = np.clip((coarse - fine) / 40.0, 0, 1)
    out = np.clip(tone - line_weight * lines, 0, 1) * 255.0

    # 5. Composite onto pure white (255)
    feathered = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
    out = out * feathered + 255.0 * (1.0 - feathered)

    # 6. Square crop centered on the subject with margin
    ys, xs = np.where(alpha > 20)
    if len(ys) > 0 and len(xs) > 0:
        side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 40
        cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
        canvas = np.full((side, side), 255, np.uint8)
        x0, y0 = cx - side // 2, cy - side // 2
        sx0, sy0 = max(x0, 0), max(y0, 0)
        sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
        canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)
    else:
        canvas = out.astype(np.uint8)

    cv2.imwrite(OUT, canvas)
    print(f"Successfully prepped photo -> {OUT} ({canvas.shape[1]}x{canvas.shape[0]})")


if __name__ == "__main__":
    prep()
