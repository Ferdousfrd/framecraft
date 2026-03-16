# modules/map_renderer.py
# FrameCraft — Battle Map Renderer (Pipeline 2)
#
# This module generates animated battle map clips.
# It takes a battle scene description and produces a video clip
# showing army positions, movements and tactics on an illustrated map.
#
# How it works:
#   1. Generate a base map image using Pixazo (parchment, illustrated style)
#   2. Draw army units on top using Pillow (colored blocks with labels)
#   3. Animate movements using FFmpeg (units slide across map)
#   4. Output: MP4 clip ready to be mixed with AI image clips
#
# Map coordinate system:
#   We use a 0-100 grid system (percentage of map width/height)
#   so positions are screen-size independent.
#   Example: position (25, 50) = 25% from left, 50% from top
#
# Army units:
#   Each unit is a colored rectangle with a label
#   Ally units = BLUE, Enemy units = RED
#   Commander units = larger with portrait border
#
# Movement animation:
#   Units slide from start position to end position over clip duration
#   Arrows fade in showing direction of movement
#   This gives the feeling of watching a live battle unfold
#
# Author: Ferdous
# Part of: FrameCraft Pipeline 2

import os
import json
import math
import subprocess
import shutil
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config.settings import PIXAZO_API_KEY

# ─── Sprite cache ─────────────────────────────────────────────────────────────
# Loaded once, reused every frame — avoids re-reading disk each frame
_sprite_cache: dict = {}

SPRITE_BASE = "assets/units/final"

# Maps unit label keywords → civ/sprite name
# Format: "keyword_in_label" → ("civ", "sprite_name")
SPRITE_MAP = {
    # Macedonian
    "alexander":          ("macedonian", "alexander"),
    "companion":          ("macedonian", "companion_cavalry"),
    "phalanx":            ("macedonian", "phalanx"),
    "hypaspist":          ("macedonian", "hypaspists"),
    "macedonian inf":     ("macedonian", "phalanx"),
    "macedonian cav":     ("macedonian", "companion_cavalry"),
    # Persian
    "darius":             ("persian",    "darius"),
    "immortal":           ("persian",    "immortals"),
    "persian arch":       ("persian",    "archers"),
    "persian cav":        ("persian",    "cavalry"),
    "chariot":            ("persian",    "scythed_chariot"),
    "elephant":           ("persian",    "war_elephant"),
    "persian inf":        ("persian",    "immortals"),
    # Spartan
    "leonidas":           ("spartan",    "leonidas"),
    "hoplite":            ("spartan",    "hoplites"),
    "spartan arch":       ("spartan",    "archers"),
    "spartan cav":        ("spartan",    "cavalry"),
    "synaspismos":        ("spartan",    "synaspismos"),
    "spartan inf":        ("spartan",    "hoplites"),
    # Roman
    "caesar":             ("roman",      "caesar"),
    "legion":             ("roman",      "legionaries"),
    "testudo":            ("roman",      "testudo"),
    "roman arch":         ("roman",      "archers"),
    "roman cav":          ("roman",      "cavalry"),
    "roman inf":          ("roman",      "legionaries"),
    # Viking
    "ragnar":             ("viking",     "ragnar"),
    "shield wall":        ("viking",     "shield_wall"),
    "berserker":          ("viking",     "berserkers"),
    "viking cav":         ("viking",     "cavalry"),
    "svinfylking":        ("viking",     "svinfylking"),
    "viking inf":         ("viking",     "shield_wall"),
    # Mongol
    "genghis":            ("mongol",     "genghis"),
    "horse archer":       ("mongol",     "horse_archers"),
    "mangudai":           ("mongol",     "mangudai"),
    "mongol cav":         ("mongol",     "heavy_cavalry"),
    "mongol inf":         ("mongol",     "horse_archers"),
}

def load_sprite(civ: str, name: str, is_ally: bool, scale: float = 1.0) -> Image.Image | None:
    """
    Loads a sprite from assets/units/final/{civ}/blue|red/{name}.png
    Caches result so disk is only read once per sprite.
    Returns None if sprite not found — caller falls back to Pillow drawing.
    """
    side = "blue" if is_ally else "red"
    key  = f"{civ}/{side}/{name}/{scale}"
    ...
    path = os.path.join(SPRITE_BASE, civ, side, f"{name}.png")
    if not os.path.exists(path):
        _sprite_cache[key] = None
        return None

    try:
        img = Image.open(path).convert("RGBA")
        r, g, b, a = img.split()
        a = a.point(lambda x: min(255, int(x * 1.6)))
        img = Image.merge("RGBA", (r, g, b, a))

        if scale != 1.0:
            w = int(img.width  * scale)
            h = int(img.height * scale)
            img = img.resize((w, h), Image.LANCZOS)
        _sprite_cache[key] = img
        return img
    except Exception as e:
        print(f"  ⚠️  Sprite load failed {path}: {e}")
        _sprite_cache[key] = None
        return None


def find_sprite(label: str, is_ally: bool, scale: float = 1.0) -> Image.Image | None:
    """
    Looks up the best sprite for a unit label string.
    Checks SPRITE_MAP for keyword matches (case-insensitive).
    Returns None if no match found.
    """
    label_lower = label.lower()
    for keyword, (civ, name) in SPRITE_MAP.items():
        if keyword in label_lower:
            return load_sprite(civ, name, is_ally, scale)
    return None


# ─── Output dimensions ────────────────────────────────────────────────────────
# Must match Pipeline 1 — vertical format for TikTok/Reels/Shorts
MAP_WIDTH  = 1080
MAP_HEIGHT = 1920

# ─── Map layout ───────────────────────────────────────────────────────────────

MAP_AREA_HEIGHT = MAP_HEIGHT   # full frame is map
INFO_AREA_TOP   = MAP_HEIGHT   # no info bar

# ─── Army unit visual settings ────────────────────────────────────────────────
UNIT_WIDTH       = 120   # px width of each army unit block
UNIT_HEIGHT      = 50    # px height of each army unit block
UNIT_FONT_SIZE   = 22    # font size for unit labels
UNIT_CORNER_RAD  = 8     # rounded corner radius on unit blocks

# ─── Colors ───────────────────────────────────────────────────────────────────
COLOR_ALLY         = (52,  101, 164)   # Blue — allied/player army
COLOR_ALLY_BORDER  = (30,   70, 130)   # Darker blue for unit border
COLOR_ENEMY        = (176,  31,  36)   # Red — enemy army
COLOR_ENEMY_BORDER = (130,  15,  18)   # Darker red for unit border
COLOR_ARROW_ALLY   = (100, 180, 255)   # Light blue movement arrows
COLOR_ARROW_ENEMY  = (255, 120, 120)   # Light red movement arrows
COLOR_TEXT_LIGHT   = (255, 255, 255)   # White text on colored units
COLOR_INFO_BG      = (15,   15,  25)   # Near black info bar background
COLOR_TITLE_TEXT   = (220, 180,  80)   # Gold title text
COLOR_SUBTITLE     = (180, 180, 180)   # Grey subtitle text

# ─── Animation settings ───────────────────────────────────────────────────────
FPS            = 30     # frames per second — smooth animation
DEFAULT_DURATION = 8    # seconds per map segment if not specified


# ══════════════════════════════════════════════════════════════════════════════
# BASE MAP GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_base_map(battle_description: str, output_path: str) -> str:
    """
    Generates an illustrated parchment-style battle map using Pixazo AI.
    This is the background image that army units will be drawn on top of.

    The map should look like an old illustrated medieval/ancient map:
    - Parchment/aged paper texture
    - Hand-drawn style terrain (hills, rivers, forests)
    - No army units — just the landscape
    - Muted earthy colors (brown, green, tan)
    - Top-down bird's eye view

    Args:
        battle_description: Text describing the battlefield terrain
                           e.g. "flat plain near river, hills to north, 
                                 small forest to east, ancient Iraq terrain"
        output_path:        Where to save the base map JPG

    Returns:
        Path to saved base map image
    """

    print(f"\n🗺️  Generating base map...")
    print(f"  Description: {battle_description[:60]}...")

    # Build the image prompt for Pixazo
    # We want an illustrated map, NOT a realistic photo
    # Parchment style = aged paper look, hand drawn terrain
    map_prompt = (
        f"top-down illustrated battle map, {battle_description}, "
        "parchment paper texture, aged brown tones, hand-drawn cartography style, "
        "medieval illustrated map, terrain features visible (hills, rivers, plains), "
        "muted earth tones, tan and brown and dark green, "
        "no army units, no soldiers, no text labels, no modern elements, "
        "bird's eye view, flat lay, detailed terrain illustration, "
        "fantasy map style, old world map aesthetic, "
        "high detail, 4k quality"
    )

    print(f"  Sending to Pixazo...")

    headers = {"Ocp-Apim-Subscription-Key": PIXAZO_API_KEY}
    payload = {
        "prompt": map_prompt,
        "width": MAP_WIDTH,
        "height": MAP_AREA_HEIGHT,   # Only map area height, not full frame
        "num_inference_steps": 30,
        "guidance_scale": 7.5
    }

    # Try up to 3 times in case of API hiccups
    for attempt in range(1, 4):
        try:
            print(f"  Attempt {attempt}/3...")
            response = requests.post(
                "https://gateway.pixazo.ai/flux-2-klein-4b/v1/generateImage",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                print(f"  ⚠️  Pixazo returned {response.status_code}: {response.text[:100]}")
                continue

            data = response.json()
            image_url = data.get("output") or data.get("image_url") or data.get("url")

            if not image_url:
                print(f"  ⚠️  No image URL in response: {list(data.keys())}")
                continue

            # Download the image
            print(f"  Downloading map image...")
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code != 200:
                print(f"  ⚠️  Download failed: {img_response.status_code}")
                continue

            # Save to disk
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_response.content)

            print(f"  ✅ Base map saved: {output_path}")
            return output_path

        except requests.exceptions.Timeout:
            print(f"  ⚠️  Timeout on attempt {attempt}")
        except Exception as e:
            print(f"  ⚠️  Attempt {attempt} failed: {e}")

    # All attempts failed — generate a fallback map using Pillow
    print(f"  ❌ Pixazo failed — generating fallback map")
    return generate_fallback_map(output_path)


def generate_fallback_map(output_path: str) -> str:
    """
    Generates a simple fallback map using Pillow if Pixazo fails.
    Uses gradients and basic shapes to simulate terrain.
    Not as beautiful as AI generated but functional for testing.

    Args:
        output_path: Where to save the fallback map

    Returns:
        Path to saved fallback map
    """

    print(f"  Drawing fallback map with Pillow...")

    img = Image.new("RGB", (MAP_WIDTH, MAP_AREA_HEIGHT), (205, 175, 120))
    draw = ImageDraw.Draw(img)

    # Draw a simple terrain — flat plain with some features
    # Background — sandy plain color
    for y in range(MAP_AREA_HEIGHT):
        shade = int(205 + (y / MAP_AREA_HEIGHT) * 20)
        shade = min(shade, 225)
        draw.line([(0, y), (MAP_WIDTH, y)], fill=(shade, shade - 30, shade - 80))

    # Draw a river cutting through
    river_points = []
    for x in range(0, MAP_WIDTH, 10):
        y = int(MAP_AREA_HEIGHT * 0.4 + math.sin(x / 100) * 60)
        river_points.append((x, y))

    if len(river_points) > 1:
        for i in range(len(river_points) - 1):
            draw.line([river_points[i], river_points[i+1]], 
                     fill=(80, 120, 180), width=12)

    # Draw some hills in the background
    for hx, hy, hr in [(200, 150, 80), (800, 200, 60), (900, 100, 100), (300, 80, 70)]:
        draw.ellipse([(hx-hr, hy-hr//2), (hx+hr, hy+hr//2)], 
                    fill=(140, 160, 100))

    # Draw some trees
    for tx, ty in [(150, 400), (160, 430), (170, 410),
                   (850, 350), (870, 370), (860, 390)]:
        draw.ellipse([(tx-15, ty-20), (tx+15, ty+10)], fill=(80, 120, 60))

    # Add parchment texture feel — slight vignette
    overlay = Image.new("RGBA", (MAP_WIDTH, MAP_AREA_HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for i in range(30):
        alpha = int(i * 3)
        overlay_draw.rectangle([(i, i), (MAP_WIDTH-i, MAP_AREA_HEIGHT-i)],
                               outline=(0, 0, 0, alpha))

    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", 
                exist_ok=True)
    img.save(output_path, "JPEG", quality=95)

    print(f"  ✅ Fallback map saved: {output_path}")
    return output_path


# ══════════════════════════════════════════════════════════════════════════════
# ARMY UNIT DRAWING
# ══════════════════════════════════════════════════════════════════════════════

def grid_to_pixel(gx: float, gy: float) -> tuple:
    """
    Converts grid coordinates (0-100) to pixel coordinates.
    Grid (0,0) = top-left of map area
    Grid (100,100) = bottom-right of map area

    Using percentages makes positions work at any resolution.

    Args:
        gx: Grid X position (0-100)
        gy: Grid Y position (0-100)

    Returns:
        (pixel_x, pixel_y) tuple
    """
    px = int((gx / 100) * MAP_WIDTH)
    py = int((gy / 100) * MAP_AREA_HEIGHT)
    return (px, py)


def load_font(size: int):
    """
    Loads best available font. Falls back gracefully if not found.

    Args:
        size: Font size in pixels

    Returns:
        PIL ImageFont object
    """
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ══════════════════════════════════════════════════════════════════════════════
# UNIT SILHOUETTE FUNCTIONS
# All units face RIGHT by default (ally direction)
# Enemy units pass facing_right=False to mirror them
# ══════════════════════════════════════════════════════════════════════════════

def draw_spearman(draw, x, y, color, scale=1.0, facing_right=True):
    """
    Single armored spearman — helmet with crest, shield, diagonal spear.
    Used in infantry formations (phalanx, shield wall, legion).
    """
    s = scale
    d = 1 if facing_right else -1
    # Helmet
    draw.ellipse([(x-int(4*s), y-int(20*s)),
                  (x+int(4*s), y-int(12*s))], fill=color)
    # Helmet crest
    draw.line([(x, y-int(20*s)),
               (x+int(d*3*s), y-int(26*s))],
              fill=color, width=max(1, int(2*s)))
    # Armored body
    draw.rectangle([(x-int(4*s), y-int(12*s)),
                    (x+int(4*s), y+int(0*s))], fill=color)
    # Shield on facing side
    sx1 = min(x+int(d*3*s), x+int(d*11*s))
    sx2 = max(x+int(d*3*s), x+int(d*11*s))
    draw.ellipse([(sx1, y-int(12*s)), (sx2, y+int(2*s))], fill=color)
    # Spear diagonal upward
    draw.line([(x-int(d*2*s), y-int(8*s)),
               (x+int(d*14*s), y-int(22*s))],
              fill=color, width=max(1, int(2*s)))
    draw.polygon([
        (x+int(d*14*s), y-int(22*s)),
        (x+int(d*10*s), y-int(20*s)),
        (x+int(d*12*s), y-int(17*s)),
    ], fill=color)
    # Legs
    draw.line([(x-int(2*s), y+int(0*s)),
               (x-int(4*s), y+int(10*s))],
              fill=color, width=max(1, int(3*s)))
    draw.line([(x+int(2*s), y+int(0*s)),
               (x+int(4*s), y+int(10*s))],
              fill=color, width=max(1, int(3*s)))


def draw_cavalry_sil(draw, x, y, color, scale=1.0, facing_right=True):
    """
    Single cavalry rider on horseback with lance forward.
    Used in cavalry formations (companion cavalry, Persian cavalry).
    """
    s = scale
    d = 1 if facing_right else -1
    # Horse body
    draw.ellipse([(x-int(14*s), y-int(2*s)),
                  (x+int(10*s), y+int(10*s))], fill=color)
    # Horse neck
    draw.line([(x+int(d*8*s), y-int(2*s)),
               (x+int(d*12*s), y-int(12*s))],
              fill=color, width=max(1, int(6*s)))
    # Horse head
    hx1 = min(x+int(d*9*s), x+int(d*17*s))
    hx2 = max(x+int(d*9*s), x+int(d*17*s))
    draw.ellipse([(hx1, y-int(18*s)), (hx2, y-int(8*s))], fill=color)
    # Four legs
    for lx in [-8, -2, 4, 8]:
        draw.line([(x+int(lx*s), y+int(10*s)),
                   (x+int(lx*s), y+int(20*s))],
                  fill=color, width=max(1, int(3*s)))
    # Rider body
    draw.ellipse([(x-int(4*s), y-int(18*s)),
                  (x+int(4*s), y-int(10*s))], fill=color)
    draw.rectangle([(x-int(4*s), y-int(10*s)),
                    (x+int(4*s), y-int(2*s))], fill=color)
    # Lance forward
    draw.line([(x-int(d*2*s), y-int(8*s)),
               (x+int(d*22*s), y-int(14*s))],
              fill=color, width=max(1, int(2*s)))
    draw.polygon([
        (x+int(d*22*s), y-int(14*s)),
        (x+int(d*17*s), y-int(12*s)),
        (x+int(d*19*s), y-int(9*s)),
    ], fill=color)


def draw_archer_sil(draw, x, y, color, scale=1.0, facing_right=True):
    """
    Single archer — lighter armor, bow drawn back ready to fire.
    Used in archer/skirmisher formations.
    """
    s = scale
    d = 1 if facing_right else -1
    # Head
    draw.ellipse([(x-int(4*s), y-int(18*s)),
                  (x+int(4*s), y-int(10*s))], fill=color)
    # Body
    draw.line([(x, y-int(10*s)), (x, y+int(2*s))],
              fill=color, width=max(1, int(4*s)))
    # Bow arm extended
    draw.line([(x-int(d*8*s), y-int(6*s)),
               (x+int(d*2*s), y-int(8*s))],
              fill=color, width=max(1, int(2*s)))
    # Bow arc
    bx1 = min(x+int(d*2*s), x+int(d*12*s))
    bx2 = max(x+int(d*2*s), x+int(d*12*s))
    draw.arc([(bx1, y-int(14*s)), (bx2, y-int(2*s))],
             start=270 if facing_right else 90,
             end=90   if facing_right else 270,
             fill=color, width=max(1, int(2*s)))
    # Arrow nocked
    draw.line([(x-int(d*6*s), y-int(7*s)),
               (x+int(d*8*s), y-int(7*s))],
              fill=color, width=max(1, int(2*s)))
    # Legs
    draw.line([(x, y+int(2*s)), (x-int(3*s), y+int(10*s))],
              fill=color, width=max(1, int(2*s)))
    draw.line([(x, y+int(2*s)), (x+int(3*s), y+int(10*s))],
              fill=color, width=max(1, int(2*s)))


def draw_unit_block(draw,
                    cx: int, cy: int,
                    label: str,
                    is_ally: bool,
                    size: str = "normal",
                    unit_type: str = "infantry",
                    commander_type: str = "horse") -> None:
    """
    Draws a complete VERTICAL army unit token on the map.

    Ally tokens face RIGHT toward enemy.
    Enemy tokens face LEFT toward ally.

    Token layout:
    ┌──────┐
    │ ░░░░ │  ← silhouette formation (infantry 5x2, cavalry 3, archer 3x2)
    │ ░░░░ │
    │──────│
    │ NAME │  ← label
    └──────┘

    Commander = small circle with ★ and name below (no big block)

    Args:
        draw:           PIL ImageDraw object
        cx, cy:         Center pixel position on map
        label:          Unit name e.g. "Phalanx", "Alexander"
        is_ally:        True = blue facing right, False = red facing left
        size:           "small", "normal", "large"
        unit_type:      "infantry", "cavalry", "archer", "commander"
        commander_type: "horse", "chariot", "elephant" (for commanders)
    """

    facing_right = is_ally
    white        = (255, 255, 255)
    gold         = (220, 180, 80)
    fill_color   = COLOR_ALLY        if is_ally else COLOR_ENEMY
    border_color = COLOR_ALLY_BORDER if is_ally else COLOR_ENEMY_BORDER

    if unit_type == "commander":
        # ── Small circle commander token ────────────────────────────────────
        # Much smaller than regular units — just a distinctive marker
        r = 42
        # Shadow
        draw.ellipse([(cx-r+3, cy-r+3), (cx+r+3, cy+r+3)],
                     fill=(0, 0, 0, 120))
        # Gold outer ring
        draw.ellipse([(cx-r-3, cy-r-3), (cx+r+3, cy+r+3)],
                     fill=gold)
        # Colored inner circle
        draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)],
                     fill=fill_color, outline=border_color, width=2)
        # Star
        draw.text((cx-10, cy-18), "★",
                  font=load_font(28), fill=gold)
        # 3-letter abbreviation
        abbr      = label[:3].upper()
        abbr_font = load_font(20)
        bbox      = draw.textbbox((0, 0), abbr, font=abbr_font)
        draw.text((cx-(bbox[2]-bbox[0])//2, cy+2),
                  abbr, font=abbr_font, fill=white)
        # Full name below circle
        name_font = load_font(22)
        nbbox     = draw.textbbox((0, 0), label, font=name_font)
        draw.text((cx-(nbbox[2]-nbbox[0])//2, cy+r+6),
                  label, font=name_font, fill=gold)

    else:
        # ── Sprite-based unit token ──────────────────────────────────────────
        # Scale: small=0.75, normal=1.0, large=1.3
        # Sprite target height on map — controls how big units appear
        size_mult  = {"small": 0.75, "normal": 1.0, "large": 1.3}.get(size, 1.0)
        target_h   = int(100 * size_mult)   # how tall the sprite should be on map

        # Try to find a real sprite for this unit
        # Scale is computed so sprite height = target_h
        sprite = find_sprite(label, is_ally)

        if sprite is not None:
            # ── REAL SPRITE PATH ────────────────────────────────────────────
            # Resize to target height, preserve aspect ratio
            aspect  = sprite.width / sprite.height
            new_h   = target_h
            new_w   = int(new_h * aspect)
            sprite  = sprite.resize((new_w, new_h), Image.LANCZOS)

            # Center sprite on (cx, cy)
            paste_x = cx - new_w // 2
            paste_y = cy - new_h // 2

            # We need the canvas Image object — get it from draw
            # Store sprite paste operations for after draw calls
            # (PIL can't paste onto ImageDraw directly — we mark it)
            # Use a workaround: attach to draw object
            if not hasattr(draw, '_sprite_pastes'):
                draw._sprite_pastes = []
            draw._sprite_pastes.append((sprite, paste_x, paste_y))

            # Label below sprite
            lbl_font = load_font(int(24 * size_mult))
            bbox     = draw.textbbox((0, 0), label, font=lbl_font)
            lw       = bbox[2] - bbox[0]
            lbl_y    = cy + new_h // 2 + 6
            # Shadow
            # Label LEFT of sprite, rotated vertical
            lbl_font = load_font(int(20 * size_mult))
            txt_img  = Image.new("RGBA", (200, 30), (0, 0, 0, 0))
            txt_draw = ImageDraw.Draw(txt_img)
            for ox, oy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
                txt_draw.text((ox, oy), label, font=lbl_font, fill=(0,0,0))
            txt_draw.text((0, 0), label, font=lbl_font, fill=(255,255,255))
            txt_rot = txt_img.rotate(90, expand=True)
            lx = cx - new_w // 2 - txt_rot.width - 4
            ly = cy - txt_rot.height // 2
            draw._sprite_pastes.append((txt_rot, lx, ly))

        else:
            # ── FALLBACK: original Pillow card drawing ───────────────────────
            w = int(110 * size_mult)
            h = int(155 * size_mult)
            x1, y1 = cx - w//2, cy - h//2
            x2, y2 = cx + w//2, cy + h//2

            draw.rounded_rectangle([(x1+4, y1+4), (x2+4, y2+4)],
                                   radius=10, fill=(0, 0, 0, 120))
            draw.rounded_rectangle([(x1, y1), (x2, y2)],
                                   radius=10, fill=fill_color,
                                   outline=border_color, width=3)

            form_cy = y1 + int(h * 0.38)
            if unit_type == "cavalry":
                count = 3
                sx_sp = int(30 * size_mult)
                ox    = cx - sx_sp * (count-1) // 2
                for i in range(count):
                    draw_cavalry_sil(draw, ox + i*sx_sp,
                                     form_cy + int(5*size_mult),
                                     white, scale=0.42*size_mult,
                                     facing_right=facing_right)
            elif unit_type == "archer":
                cols, rows = 3, 2
                sx_sp = int(28 * size_mult)
                sy_sp = int(40 * size_mult)
                ox    = cx - sx_sp * (cols-1) // 2
                oy    = form_cy - sy_sp // 2
                for row in range(rows):
                    for col in range(cols):
                        draw_archer_sil(draw, ox + col*sx_sp,
                                        oy + row*sy_sp,
                                        white, scale=0.55*size_mult,
                                        facing_right=facing_right)
            else:   # infantry default
                cols, rows = 5, 2
                sx_sp = int(14 * size_mult)
                sy_sp = int(28 * size_mult)
                ox    = cx - sx_sp * (cols-1) // 2
                oy    = form_cy - sy_sp * (rows-1) // 2
                for row in range(rows):
                    for col in range(cols):
                        draw_spearman(draw, ox + col*sx_sp,
                                      oy + row*sy_sp,
                                      white, scale=0.50*size_mult,
                                      facing_right=facing_right)

            div_y = y1 + int(h * 0.72)
            draw.line([(x1+8, div_y), (x2-8, div_y)],
                      fill=(255, 255, 255, 80), width=1)
            lbl_font = load_font(int(22 * size_mult))
            bbox     = draw.textbbox((0, 0), label, font=lbl_font)
            lw       = bbox[2] - bbox[0]
            draw.text((cx - lw//2 + 1, div_y + 9), label,
                      font=lbl_font, fill=(0, 0, 0))
            draw.text((cx - lw//2, div_y + 8), label,
                      font=lbl_font, fill=white)



def draw_movement_arrow(draw: ImageDraw,
                        start_px: tuple,
                        end_px: tuple,
                        is_ally: bool,
                        thickness: int = 6) -> None:
    """
    Draws an arrow showing army movement direction on the map.
    Arrows are semi-transparent so the map shows through.

    Args:
        draw:      PIL ImageDraw object
        start_px:  (x, y) arrow start pixel position
        end_px:    (x, y) arrow end pixel position  
        is_ally:   True = blue arrow, False = red arrow
        thickness: Arrow line thickness in pixels
    """

    color = COLOR_ARROW_ALLY if is_ally else COLOR_ARROW_ENEMY

    # Draw the main line
    draw.line([start_px, end_px], fill=color, width=thickness)

    # Calculate arrowhead
    dx = end_px[0] - start_px[0]
    dy = end_px[1] - start_px[1]
    length = math.sqrt(dx*dx + dy*dy)

    if length < 1:
        return

    # Normalize direction
    nx = dx / length
    ny = dy / length

    # Arrowhead size
    arrow_size = 20

    # Two points of arrowhead
    left_x  = int(end_px[0] - arrow_size * (nx - ny * 0.5))
    left_y  = int(end_px[1] - arrow_size * (ny + nx * 0.5))
    right_x = int(end_px[0] - arrow_size * (nx + ny * 0.5))
    right_y = int(end_px[1] - arrow_size * (ny - nx * 0.5))

    draw.polygon([end_px, (left_x, left_y), (right_x, right_y)], fill=color)


# ══════════════════════════════════════════════════════════════════════════════
# INFO BAR (bottom of frame)
# ══════════════════════════════════════════════════════════════════════════════

def draw_info_bar(draw: ImageDraw,
                  battle_name: str,
                  phase_label: str,
                  ally_name: str,
                  enemy_name: str) -> None:
    """
    Draws the info bar at the bottom of the frame (below the map).
    Shows battle name, current phase, and army name legend.

    Layout:
    ┌─────────────────────────────────────┐
    │  BATTLE OF GAUGAMELA  331 BC        │
    │  Phase: Alexander spots the gap     │
    │  ■ Macedonian    ■ Persian Empire   │
    └─────────────────────────────────────┘

    Args:
        draw:        PIL ImageDraw object
        battle_name: e.g. "Battle of Gaugamela, 331 BC"
        phase_label: e.g. "Alexander spots the gap"
        ally_name:   e.g. "Macedonian Army"
        enemy_name:  e.g. "Persian Empire"
    """

    # Draw dark background for info area
    draw.rectangle(
        [(0, INFO_AREA_TOP), (MAP_WIDTH, MAP_HEIGHT)],
        fill=COLOR_INFO_BG
    )

    # Draw separator line between map and info
    draw.line(
        [(0, INFO_AREA_TOP), (MAP_WIDTH, INFO_AREA_TOP)],
        fill=(220, 180, 80),  # Gold line
        width=3
    )

    # Battle name — large gold text centered
    title_font = load_font(42)
    title_bbox = draw.textbbox((0, 0), battle_name.upper(), font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (MAP_WIDTH - title_w) // 2
    title_y = INFO_AREA_TOP + 30

    # Shadow
    draw.text((title_x + 2, title_y + 2), battle_name.upper(),
             font=title_font, fill=(0, 0, 0))
    # Text
    draw.text((title_x, title_y), battle_name.upper(),
             font=title_font, fill=COLOR_TITLE_TEXT)

    # Phase label — smaller white text centered
    phase_font = load_font(32)
    phase_bbox = draw.textbbox((0, 0), phase_label, font=phase_font)
    phase_w = phase_bbox[2] - phase_bbox[0]
    phase_x = (MAP_WIDTH - phase_w) // 2
    phase_y = title_y + 60

    draw.text((phase_x, phase_y), phase_label,
             font=phase_font, fill=COLOR_SUBTITLE)

    # Army legend — ally on left, enemy on right
    legend_font = load_font(28)
    legend_y = phase_y + 55

    # Ally legend (left side)
    ally_box_x = 80
    draw.rounded_rectangle(
        [(ally_box_x, legend_y), (ally_box_x + 35, legend_y + 35)],
        radius=4, fill=COLOR_ALLY
    )
    draw.text((ally_box_x + 45, legend_y + 3), ally_name,
             font=legend_font, fill=COLOR_TEXT_LIGHT)

    # Enemy legend (right side)
    enemy_text_bbox = draw.textbbox((0, 0), enemy_name, font=legend_font)
    enemy_text_w = enemy_text_bbox[2] - enemy_text_bbox[0]
    enemy_box_x = MAP_WIDTH - 80 - 35 - 10 - enemy_text_w
    draw.rounded_rectangle(
        [(enemy_box_x, legend_y), (enemy_box_x + 35, legend_y + 35)],
        radius=4, fill=COLOR_ENEMY
    )
    draw.text((enemy_box_x + 45, legend_y + 3), enemy_name,
             font=legend_font, fill=COLOR_TEXT_LIGHT)


# ══════════════════════════════════════════════════════════════════════════════
# FRAME GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def render_frame(base_map_path: str,
                 units: list,
                 arrows: list,
                 battle_name: str,
                 phase_label: str,
                 ally_name: str,
                 enemy_name: str) -> Image:
    """
    Renders a single frame of the battle map.
    Composites: base map + unit blocks + arrows + info bar

    Args:
        base_map_path: Path to the AI generated base map image
        units: List of unit dicts:
               [{"label": "Cavalry", "gx": 25, "gy": 50, 
                 "is_ally": True, "size": "normal"}, ...]
        arrows: List of arrow dicts:
                [{"start": (gx, gy), "end": (gx, gy), "is_ally": True}, ...]
        battle_name:  Battle title for info bar
        phase_label:  Current phase description for info bar
        ally_name:    Ally army name for legend
        enemy_name:   Enemy army name for legend

    Returns:
        PIL Image object of the complete frame
    """

    # Load and resize base map to exact dimensions
    base_map = Image.open(base_map_path).convert("RGBA")
    base_map = base_map.resize((MAP_WIDTH, MAP_AREA_HEIGHT), Image.LANCZOS)

    # Create full frame canvas (map area + info area)
    frame = Image.new("RGBA", (MAP_WIDTH, MAP_HEIGHT), (0, 0, 0, 255))
    frame.paste(base_map, (0, 0))

    # Create overlay for units and arrows (transparent)
    overlay = Image.new("RGBA", (MAP_WIDTH, MAP_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw._sprite_pastes = []   # collect sprite pastes

    # Draw arrows first (behind units)
    for arrow in arrows:
        start_px = grid_to_pixel(arrow["start"][0], arrow["start"][1])
        end_px   = grid_to_pixel(arrow["end"][0],   arrow["end"][1])
        draw_movement_arrow(draw, start_px, end_px, arrow["is_ally"])

    # Draw unit blocks — sprites are queued in draw._sprite_pastes
    for unit in units:
        cx, cy = grid_to_pixel(unit["gx"], unit["gy"])
        double = unit.get("double", False)
        if double:
            # Paste sprite twice side by side, share one label
            sprite = find_sprite(unit["label"], unit["is_ally"])
            if sprite:
                th = int(100 * {"small":0.75,"normal":1.0,"large":1.3}.get(unit.get("size","normal"),1.0))
                aspect = sprite.width / sprite.height
                sh = th; sw = int(sh * aspect)
                sprite = sprite.resize((sw, sh), Image.LANCZOS)
                if not hasattr(draw, '_sprite_pastes'):
                    draw._sprite_pastes = []
                # Two side by side
                draw._sprite_pastes.append((sprite, cx - sw, cy - sh//2))
                draw._sprite_pastes.append((sprite, cx,     cy - sh//2))
                # One label on left
                lbl_font = load_font(20)
                txt_img  = Image.new("RGBA", (200, 30), (0,0,0,0))
                ImageDraw.Draw(txt_img).text((0,0), unit["label"],
                                             font=lbl_font, fill=(255,255,255))
                txt_rot  = txt_img.rotate(90, expand=True)
                draw._sprite_pastes.append((txt_rot, cx - sw - txt_rot.width - 4,
                                            cy - txt_rot.height//2))
        else:
            draw_unit_block(
                draw, cx, cy,
                label=unit["label"],
                is_ally=unit["is_ally"],
                size=unit.get("size", "normal")
            )

    # Paste real sprites onto overlay AFTER all draw calls
    for sprite_img, px, py in draw._sprite_pastes:
        overlay.paste(sprite_img, (px, py), sprite_img)

    # Title overlay on top of map (no black bar)
    title_font = load_font(38)
    sub_font   = load_font(26)
    draw.rectangle([(0, 0), (MAP_WIDTH, 110)], fill=(0, 0, 0, 160))
    bb = draw.textbbox((0,0), battle_name.upper(), font=title_font)
    draw.text(((MAP_WIDTH-(bb[2]-bb[0]))//2, 12),
              battle_name.upper(), font=title_font, fill=(220,180,80))
    sub = f"{ally_name}  vs  {enemy_name}"
    bb2 = draw.textbbox((0,0), sub, font=sub_font)
    draw.text(((MAP_WIDTH-(bb2[2]-bb2[0]))//2, 62),
              sub, font=sub_font, fill=(200,200,200))

    # Composite overlay onto frame
    frame = Image.alpha_composite(frame, overlay)
    frame = frame.convert("RGB")

    return frame


# ══════════════════════════════════════════════════════════════════════════════
# MAP CLIP GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def render_map_clip(scene: dict,
                    base_map_path: str,
                    output_path: str,
                    duration: int = DEFAULT_DURATION) -> str:
    """
    Renders a complete animated map clip for one battle scene.
    
    Animation: units smoothly slide from start positions to end positions
    over the clip duration. Arrows fade in halfway through.

    Scene dict format:
    {
        "battle_name": "Battle of Gaugamela, 331 BC",
        "phase_label": "Alexander spots the gap",
        "ally_name": "Macedonian Army",
        "enemy_name": "Persian Empire",
        "units_start": [
            {"label": "Alexander", "gx": 20, "gy": 60, 
             "is_ally": True, "size": "large"},
            {"label": "Phalanx",   "gx": 35, "gy": 55, 
             "is_ally": True, "size": "normal"},
            {"label": "Darius",    "gx": 75, "gy": 50, 
             "is_ally": False, "size": "large"},
            {"label": "Immortals", "gx": 60, "gy": 55, 
             "is_ally": False, "size": "normal"},
        ],
        "units_end": [
            {"label": "Alexander", "gx": 50, "gy": 45, ...},  # moved!
            {"label": "Phalanx",   "gx": 50, "gy": 55, ...},  # moved!
            {"label": "Darius",    "gx": 75, "gy": 50, ...},  # stayed
            {"label": "Immortals", "gx": 60, "gy": 55, ...},  # stayed
        ],
        "arrows": [
            {"start": (20, 60), "end": (50, 45), "is_ally": True},
        ]
    }

    Args:
        scene:         Scene dictionary (see format above)
        base_map_path: Path to base map image
        output_path:   Where to save the output MP4
        duration:      Clip duration in seconds

    Returns:
        Path to rendered MP4 clip
    """

    print(f"\n🎬 Rendering map clip: {scene.get('phase_label', 'Unknown phase')}")
    print(f"  Duration: {duration}s")
    print(f"  Units: {len(scene.get('units_start', []))} units")
    print(f"  Arrows: {len(scene.get('arrows', []))} movement arrows")

    # Create temp directory for individual frames
    temp_dir = output_path.replace(".mp4", "_frames")
    os.makedirs(temp_dir, exist_ok=True)

    total_frames = duration * FPS
    print(f"  Generating {total_frames} frames ({FPS}fps × {duration}s)...")

    units_start = scene.get("units_start", [])
    units_end   = scene.get("units_end",   units_start)  # if no end, units don't move
    arrows      = scene.get("arrows", [])

    battle_name  = scene.get("battle_name",  "The Battle")
    phase_label  = scene.get("phase_label",  "")
    ally_name    = scene.get("ally_name",    "Allied Army")
    enemy_name   = scene.get("enemy_name",   "Enemy Army")

    # Generate each frame
    for frame_num in range(total_frames):
        # Progress 0.0 → 1.0 over the clip duration
        t = frame_num / max(total_frames - 1, 1)

        # Smooth easing — starts fast, slows at end (ease out)
        # This makes unit movements look more natural
        t_eased = 1 - (1 - t) ** 2

        # Interpolate unit positions between start and end
        current_units = []
        for i, unit_start in enumerate(units_start):
            # Get corresponding end position (or same if not moving)
            if i < len(units_end):
                unit_end = units_end[i]
            else:
                unit_end = unit_start

            # Lerp (linear interpolate) position
            current_gx = unit_start["gx"] + (unit_end["gx"] - unit_start["gx"]) * t_eased
            current_gy = unit_start["gy"] + (unit_end["gy"] - unit_start["gy"]) * t_eased

            current_units.append({
                **unit_start,
                "gx": current_gx,
                "gy": current_gy
            })

        # Arrows fade in during second half of clip
        # Before halfway = no arrows, After halfway = arrows appear
        current_arrows = arrows if t > 0.5 else []

        # Render this frame
        frame_img = render_frame(
            base_map_path,
            current_units,
            current_arrows,
            battle_name,
            phase_label,
            ally_name,
            enemy_name
        )

        # Save frame as PNG
        frame_path = os.path.join(temp_dir, f"frame_{frame_num:05d}.png")
        frame_img.save(frame_path, "PNG")

        # Progress update every 30 frames
        if frame_num % 30 == 0:
            print(f"  Frame {frame_num}/{total_frames} ({int(t*100)}%)")

    print(f"  Assembling frames into video...")

    # Use FFmpeg to assemble PNG frames into MP4
    cmd = [
        "ffmpeg",
        "-framerate", str(FPS),
        "-i", os.path.join(temp_dir, "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-y",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up frames
    shutil.rmtree(temp_dir)

    if result.returncode != 0:
        raise Exception(f"FFmpeg frame assembly failed: {result.stderr[-300:]}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  ✅ Map clip rendered: {output_path} ({size_mb:.1f} MB)")

    return output_path


# ══════════════════════════════════════════════════════════════════════════════
# TEST / DEMO
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Test the map renderer with a sample Battle of Gaugamela scene.
    Run: python3 -m modules.map_renderer
    Output: outputs/test_map/test_map_clip.mp4
    """

    print("🗺️  MAP RENDERER TEST")
    print("="*50)
    print("Testing with: Battle of Gaugamela, 331 BC")
    print("="*50)

    # Output directory
    test_dir = "outputs/test_map"
    os.makedirs(test_dir, exist_ok=True)

    # Step 1: Generate base map
    base_map_path = os.path.join(test_dir, "base_map.jpg")
    generate_base_map(
        battle_description=(
            "flat open plain in ancient Iraq, "
            "small river to the north, gentle hills in background, "
            "dry grass terrain, ancient mesopotamia landscape"
        ),
        output_path=base_map_path
    )

    # Step 2: Define battle scene
    # This represents the moment Alexander charges the gap in Persian lines
    test_scene = {
        "battle_name":  "Battle of Gaugamela, 331 BC",
        "phase_label":  "Alexander charges the gap",
        "ally_name":    "Macedonian Army",
        "enemy_name":   "Persian Empire",

        # Starting positions — armies facing each other
        "units_start": [
            {"label": "Alexander",  "gx": 20, "gy": 45, "is_ally": True,  "size": "large"},
            {"label": "Companion Cav", "gx": 22, "gy": 55, "is_ally": True,  "size": "normal"},
            {"label": "Phalanx",    "gx": 38, "gy": 50, "is_ally": True,  "size": "normal"},
            {"label": "Left Flank", "gx": 55, "gy": 50, "is_ally": True,  "size": "small"},
            {"label": "Darius",     "gx": 78, "gy": 45, "is_ally": False, "size": "large"},
            {"label": "Immortals",  "gx": 65, "gy": 50, "is_ally": False, "size": "normal"},
            {"label": "Persian Cav","gx": 80, "gy": 60, "is_ally": False, "size": "normal"},
            {"label": "Infantry",   "gx": 70, "gy": 50, "is_ally": False, "size": "normal"},
        ],

        # End positions — Alexander has charged into the gap
        "units_end": [
            {"label": "Alexander",  "gx": 55, "gy": 42, "is_ally": True,  "size": "large"},
            {"label": "Companion Cav", "gx": 57, "gy": 52, "is_ally": True,  "size": "normal"},
            {"label": "Phalanx",    "gx": 50, "gy": 50, "is_ally": True,  "size": "normal"},
            {"label": "Left Flank", "gx": 55, "gy": 50, "is_ally": True,  "size": "small"},
            {"label": "Darius",     "gx": 85, "gy": 38, "is_ally": False, "size": "large"},
            {"label": "Immortals",  "gx": 65, "gy": 50, "is_ally": False, "size": "normal"},
            {"label": "Persian Cav","gx": 80, "gy": 60, "is_ally": False, "size": "normal"},
            {"label": "Infantry",   "gx": 70, "gy": 50, "is_ally": False, "size": "normal"},
        ],

        # Movement arrows
        "arrows": [
            {"start": (20, 45), "end": (55, 42), "is_ally": True},   # Alexander charges
            {"start": (22, 55), "end": (57, 52), "is_ally": True},   # Cavalry follows
            {"start": (78, 45), "end": (85, 38), "is_ally": False},  # Darius retreats
        ]
    }

    # Step 3: Render the map clip
    output_clip = os.path.join(test_dir, "test_map_clip.mp4")
    render_map_clip(
        scene=test_scene,
        base_map_path=base_map_path,
        output_path=output_clip,
        duration=8
    )

    print(f"\n{'='*50}")
    print(f"✅ TEST COMPLETE!")
    print(f"{'='*50}")
    print(f"📁 Base map: {base_map_path}")
    print(f"🎬 Map clip: {output_clip}")
    print(f"\nWatch the clip to verify:")
    print(f"  - Map background looks like illustrated parchment")
    print(f"  - Blue units = Macedonian, Red units = Persian")
    print(f"  - Units animate from start to end positions")
    print(f"  - Arrows appear halfway through showing movement")
    print(f"  - Info bar shows battle name and phase at bottom")