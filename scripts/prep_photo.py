"""
Prepare a portrait photo for clean ASCII conversion:
  1. Handle RGBA transparent background by compositing onto pure white
  2. Crop to headshot aspect ratio matching ASCII grid (800x795)
  3. Boost local contrast and sharpen facial features
  4. Ensure background is 255 (pure white -> spaces in ASCII ramp)

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.
"""
import os
import sys
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
# Check for source-photo.png first, then source-photo.jpg
default_inp = os.path.join(HERE, "..", "source-photo.png")
if not os.path.exists(default_inp):
    default_inp = os.path.join(HERE, "..", "source-photo.jpg")

INP = sys.argv[1] if len(sys.argv) > 1 else default_inp
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

if not os.path.exists(INP):
    print(f"Error: Source image '{INP}' not found.")
    sys.exit(1)

# Open image
raw = Image.open(INP)

# Composite RGBA onto pure white background
if raw.mode in ("RGBA", "LA") or (raw.mode == "P" and "transparency" in raw.info):
    raw = raw.convert("RGBA")
    white_bg = Image.new("RGBA", raw.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(white_bg, raw)
    img = comp.convert("L")
else:
    img = raw.convert("L")

w, h = img.size
target_ar = 800.0 / 795.0

# Calculate crop
crop_h = min(h, int(w / target_ar))
crop_w = int(crop_h * target_ar)

left = (w - crop_w) // 2
top = 0
right = left + crop_w
bottom = top + crop_h

cropped = img.crop((left, top, right, bottom))

# Contrast & detail enhancement
enhanced = cropped.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=2))
enhanced = ImageOps.autocontrast(enhanced, cutoff=1)
enhanced = ImageEnhance.Contrast(enhanced).enhance(1.4)
enhanced = ImageEnhance.Brightness(enhanced).enhance(1.05)

enhanced.save(OUT)
print(f"Wrote prepped portrait ({enhanced.size[0]}x{enhanced.size[1]}) from {INP} to {OUT}")