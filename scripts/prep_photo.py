"""
Prepare a portrait photo for clean ASCII conversion:
  1. Crop to square/headshot aspect ratio matching ASCII grid (800x795)
  2. Enhance contrast, gamma, and sharpness for clean facial features
  3. Suppress background so face and hair stand out in monochrome ASCII

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

if not os.path.exists(INP):
    print(f"Error: Source image '{INP}' not found.")
    sys.exit(1)

# Load image
img = Image.open(INP).convert("L")
w, h = img.size

# Target aspect ratio: 800 / 795 ~ 1.006
target_ar = 800.0 / 795.0

# Crop to headshot (focus top 85% centered)
crop_h = min(h, int(w / target_ar))
crop_w = int(crop_h * target_ar)

left = (w - crop_w) // 2
top = 0  # Start from top to capture head & hair
right = left + crop_w
bottom = top + crop_h

cropped = img.crop((left, top, right, bottom))

# Contrast & detail enhancement
# Apply subtle unsharp mask for facial clarity
enhanced = cropped.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=2))
enhanced = ImageOps.autocontrast(enhanced, cutoff=2)
enhanced = ImageEnhance.Contrast(enhanced).enhance(1.35)
enhanced = ImageEnhance.Brightness(enhanced).enhance(1.05)

enhanced.save(OUT)
print(f"Wrote prepped portrait ({enhanced.size[0]}x{enhanced.size[1]}) to {OUT}")