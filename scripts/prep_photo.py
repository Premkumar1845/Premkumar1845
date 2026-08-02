"""
Prepare a portrait photo for clean ASCII conversion:
  1. remove the background or isolate subject
  2. boost local contrast so a face gains highlights and shadows
  3. composite onto pure white (white -> spaces in ASCII ramp)

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.
Run once whenever the source photo changes; the ASCII SVG itself is static.

Usage:
    python scripts/prep_photo.py [input.jpg] [output.png]
"""
import os
import sys
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

if not os.path.exists(INP):
    print(f"Source image '{INP}' not found. Generating default prepped avatar...")
    # Create a nice clean 400x400 avatar icon placeholder if no source-photo.jpg exists yet
    img = Image.new("L", (400, 400), 255)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    # Draw head & shoulders silhouette outline for placeholder
    draw.ellipse([130, 80, 270, 220], fill=60)      # Head
    draw.ellipse([70, 230, 330, 420], fill=80)      # Shoulders
    draw.ellipse([145, 95, 255, 205], fill=150)     # Face highlight
    img.save(OUT)
    print("Wrote default avatar to", OUT)
    sys.exit(0)

try:
    import cv2
    from rembg import remove
    cut = remove(Image.open(INP).convert("RGBA"))
    rgb = np.array(cut.convert("RGB"))
    alpha = np.array(cut.split()[-1])
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18)
    mask = (alpha.astype(np.float32) / 255.0)
    mask = cv2.GaussianBlur(mask, (0, 0), 1.0)
    out = gray.astype(np.float32) * mask + 255.0 * (1.0 - mask)
    out = np.clip(out, 0, 255).astype(np.uint8)
    Image.fromarray(out, mode="L").save(OUT)
    print("Wrote prepped image using rembg+cv2 to", OUT)
except Exception as e:
    print(f"Advanced libraries unavailable ({e}), using PIL fallback...")
    img = Image.open(INP).convert("L")
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    img.save(OUT)
    print("Wrote prepped image using PIL fallback to", OUT)