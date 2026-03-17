# test_unit_blocks.py
# Tests the new icon-based unit block design
# Run: python3 test_unit_blocks.py
# Output: outputs/test_blocks.png

from PIL import Image, ImageDraw
import os

# ── Settings ──────────────────────────────────────────────────────────────────
BLOCK_SIZE   = 90       # square block size in pixels
CORNER_RAD   = 8        # rounded corners
ICON_PADDING = 12       # padding around icon inside block
COLOR_ALLY   = (52, 101, 164)    # blue
COLOR_ENEMY  = (176, 31, 36)     # red
ICONS_DIR    = "assets/block-icons"

# ── Canvas ────────────────────────────────────────────────────────────────────
canvas = Image.new("RGBA", (800, 400), (200, 175, 130, 255))  # parchment bg
draw   = ImageDraw.Draw(canvas)


def remove_white_bg(img, threshold=240):
    """Remove white/near-white background → transparent PNG"""
    img = img.convert("RGBA")
    pixels = list(img.getdata())
    new_pixels = []
    for r, g, b, a in pixels:
        if r > threshold and g > threshold and b > threshold:
            new_pixels.append((r, g, b, 0))  # transparent
        else:
            new_pixels.append((r, g, b, a))
    img.putdata(new_pixels)
    return img


def draw_block(canvas, cx, cy, icon_path, is_ally, is_commander=False, flip=False):
    """
    Draws a square unit block centered at (cx, cy).
    Commanders get special gold frame treatment.
    """
    color  = COLOR_ALLY if is_ally else COLOR_ENEMY
    border = (30, 70, 130) if is_ally else (130, 15, 18)
    half   = BLOCK_SIZE // 2

    x1, y1 = cx - half, cy - half
    x2, y2 = cx + half, cy + half

    draw = ImageDraw.Draw(canvas)

    if is_commander:
        # Special commander frame — larger, gold border, darker bg
        # Outer gold ring
        draw.rounded_rectangle(
            [(x1-4, y1-4), (x2+4, y2+4)],
            radius=CORNER_RAD+4,
            fill=(180, 140, 20),   # gold
            outline=(220, 180, 40),
            width=3
        )
        # Inner dark background
        draw.rounded_rectangle(
            [(x1, y1), (x2, y2)],
            radius=CORNER_RAD,
            fill=(20, 20, 40),     # dark navy
            outline=(220, 180, 40),
            width=2
        )
        # Corner decorations — small gold squares
        for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
            draw.rectangle(
                [(cx+dx*(half-8)-3, cy+dy*(half-8)-3),
                 (cx+dx*(half-8)+3, cy+dy*(half-8)+3)],
                fill=(220, 180, 40)
            )
    else:
        # Normal unit block
        draw.rounded_rectangle(
            [(x1, y1), (x2, y2)],
            radius=CORNER_RAD,
            fill=color,
            outline=border,
            width=2
        )

    # Load and prepare icon
    icon = Image.open(icon_path).convert("RGBA")
    icon = remove_white_bg(icon)
    # Flip horizontally for enemy units
    if flip:
        icon = icon.transpose(Image.FLIP_LEFT_RIGHT)
    # Chariot icons are small — force bigger zoom
    if "chariot" in icon_path.lower():
        icon_size = BLOCK_SIZE - 4   # almost full block size


    # Resize icon — chariots get extra zoom
    if "chariot" in icon_path.lower():
        icon_size = BLOCK_SIZE - 6
    else:
        icon_size = BLOCK_SIZE - (ICON_PADDING * 2)
    ratio = min(icon_size / icon.width, icon_size / icon.height)
    new_w = int(icon.width  * ratio)
    new_h = int(icon.height * ratio)
    # For small icons force them bigger
    if new_w < icon_size - 10:
        new_w = icon_size - 10
        new_h = int(new_w / (icon.width / icon.height))
    icon = icon.resize((new_w, new_h), Image.LANCZOS)

    # Center icon
    ix = cx - icon.width  // 2
    iy = cy - icon.height // 2
    canvas.paste(icon, (ix, iy), icon)

# ── Draw all unit types ───────────────────────────────────────────────────────
units = [
    # Ally units (blue) — top row
    (80,  100, "spear.jpg",        True,  "Infantry",  False, False),
    (200, 100, "archer.jpg",       True,  "Archers",   False, False),
    (320, 100, "cavelry-left.jpg", True,  "Cavalry",   False, False),
    (440, 100, "chariot-left.png", True,  "Chariot",   False, False),
    (560, 100, "Alexander.jpg",    True,  "Alexander", True,  False),

    # Enemy units (red) — use same icons but FLIPPED
    (80,  260, "spear.jpg",        False, "Infantry",  False, True),
    (200, 260, "archer.jpg",       False, "Archers",   False, True),
    (320, 260, "cavelry-left.jpg", False, "Cavalry",   False, True),
    (440, 260, "chariot-left.png", False, "Chariot",   False, True),
    (560, 260, "Darius.jpg",       False, "Darius",    True,  False),
]

from PIL import ImageFont
try:
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
except:
    font = ImageFont.load_default()

for cx, cy, icon_file, is_ally, label, is_commander, flip in units:
    icon_path = os.path.join(ICONS_DIR, icon_file)
    draw_block(canvas, cx, cy, icon_path, is_ally, is_commander, flip)

    # Label below block
    d = ImageDraw.Draw(canvas)
    bbox = d.textbbox((0,0), label, font=font)
    lw = bbox[2] - bbox[0]
    d.text((cx - lw//2, cy + BLOCK_SIZE//2 + 6), label,
           font=font, fill=(255,255,255))

# Save
os.makedirs("outputs", exist_ok=True)
canvas.convert("RGB").save("outputs/test_blocks.png")
print("✅ Saved: outputs/test_blocks.png")
print("Upload to check how blocks look!")