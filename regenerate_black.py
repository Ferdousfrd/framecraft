# regenerate_black.py — black silhouette versions, no tinting
import os
from PIL import Image

INPUT_BASE  = "assets/units/final"
OUTPUT_BASE = "assets/units/black"

def to_black_silhouette(img):
    img = img.convert("RGBA")
    pixels = list(img.getdata())
    new_pixels = []
    for r, g, b, a in pixels:
        if r > 235 and g > 235 and b > 235:
            new_pixels.append((0, 0, 0, 0))  # white → transparent
        elif a > 30:
            new_pixels.append((0, 0, 0, 255))  # any visible pixel → black
        else:
            new_pixels.append((0, 0, 0, 0))
    img.putdata(new_pixels)
    return img

civs = [d for d in os.listdir(INPUT_BASE)
        if os.path.isdir(os.path.join(INPUT_BASE, d))]

for civ in civs:
    raw_dir = os.path.join(INPUT_BASE, civ, "raw")
    if not os.path.exists(raw_dir):
        continue
    for fname in os.listdir(raw_dir):
        if not fname.endswith(".png"):
            continue
        name   = fname.replace(".png", "")
        src    = os.path.join(raw_dir, fname)
        # facing right (ally)
        right_dir = os.path.join(OUTPUT_BASE, civ, "right")
        os.makedirs(right_dir, exist_ok=True)
        img = Image.open(src)
        sil = to_black_silhouette(img)
        sil.save(os.path.join(right_dir, fname))
        # facing left (enemy) — just flip
        left_dir = os.path.join(OUTPUT_BASE, civ, "left")
        os.makedirs(left_dir, exist_ok=True)
        sil.transpose(Image.FLIP_LEFT_RIGHT).save(
            os.path.join(left_dir, fname))
        print(f"  ✅ {civ}/{name}")

print("Done! Sprites saved to assets/units/black/")