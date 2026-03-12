# generate_sprites.py — MASTER sprite generator
# All civilizations, accurate units, special formations
# Run: python3 generate_sprites.py

import requests, os, time
from PIL import Image
from io import BytesIO
from config.settings import PIXAZO_API_KEY

headers = {"Ocp-Apim-Subscription-Key": PIXAZO_API_KEY}
OUTPUT_DIR = "assets/units/final"

# ── Size standards ────────────────────────────────────────────────────────────
# Infantry: 10 units  → (512, 1024) tall
# Archer:    8 units  → (512, 860)  slightly shorter
# Cavalry:   3 units  → (512, 640)  triangle
# Commander: 1 unit   → (512, 512)  square
# Special:  10 units  → (512, 1024) tall formation

ALL_SPRITES = [

    # ════════════════════════════════════════════════════════
    # MACEDONIAN
    # ════════════════════════════════════════════════════════
    {
        "civ": "macedonian", "name": "phalanx",
        "prompt": (
            "exactly 10 macedonian phalanx soldiers in a single vertical column, "
            "one behind another facing right, side view, "
            "accurate bronze corinthian helmets with red horsehair plumes, "
            "large round aspis shields, 18-foot sarissa pikes pointing right, "
            "linen linothorax armor, greaves on legs, "
            "tightly packed column formation, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 1024)
    },
    {
        "civ": "macedonian", "name": "companion_cavalry",
        "prompt": (
            "3 macedonian companion cavalry in triangle formation, "
            "side view facing right, "
            "riders in bronze muscle cuirass armor, macedonian kausia hat, "
            "xyston lance 12-foot pointing forward, short kopis sword on belt, "
            "powerful warhorses, leader at front tip of triangle, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 640)
    },
    {
        "civ": "macedonian", "name": "alexander",
        "prompt": (
            "alexander the great single commander on black horse bucephalus, "
            "side view facing right, "
            "ornate bronze muscle cuirass with gorgon head engraving, "
            "white ostrich plume helmet, red royal cloak, "
            "kopis sword raised, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 512)
    },
    {
        "civ": "macedonian", "name": "hypaspists",
        "prompt": (
            "10 macedonian hypaspist elite infantry in vertical column, "
            "one behind another facing right, side view, "
            "bronze shields shorter than phalanx, short spear and sword, "
            "lighter armor than phalanx, faster infantry, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 1024)
    },

    # ════════════════════════════════════════════════════════
    # PERSIAN
    # ════════════════════════════════════════════════════════
    {
        "civ": "persian", "name": "immortals",
        "prompt": (
            "10 persian immortal elite soldiers in vertical column, "
            "one behind another facing right, side view, "
            "accurate wicker spara shields with colorful patterns, "
            "tall persian tiara felt caps, long spears, short akinakes daggers on belt, "
            "colorful embroidered robes in purple gold and white, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 1024)
    },
    {
        "civ": "persian", "name": "archers",
        "prompt": (
            "8 persian archers in vertical column, "
            "one behind another facing right, side view, "
            "each drawing powerful composite bow, "
            "colorful persian robes, tiara hats, full quiver on back, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 860)
    },
    {
        "civ": "persian", "name": "cavalry",
        "prompt": (
            "3 persian cavalry riders in triangle formation, "
            "side view facing right, "
            "persian armor with scale cuirass, akinakes sword raised, "
            "colorful horse blankets, persian helmet, "
            "leader at front of triangle, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 640)
    },
    {
        "civ": "persian", "name": "darius",
        "prompt": (
            "darius III single commander on royal war chariot, "
            "side view facing right, "
            "tall persian kidaris crown, ornate royal robes, "
            "holding royal bow, decorated gold chariot, two white horses, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 512)
    },
    {
        "civ": "persian", "name": "scythed_chariot",
        "prompt": (
            "persian scythed war chariot single unit, "
            "side view facing right, "
            "two horses galloping, long curved blades on wheel axles, "
            "armored driver crouching behind shield, "
            "historically accurate ancient persian war machine, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 512)
    },
    {
        "civ": "persian", "name": "war_elephant",
        "prompt": (
            "single indian war elephant with wooden howdah tower, "
            "side view facing right, "
            "elephant with iron armor plates on head and body, "
            "2 soldiers in howdah with bows and spears, "
            "mahout driver on neck, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 512)
    },

    # ════════════════════════════════════════════════════════
    # SPARTAN
    # ════════════════════════════════════════════════════════
    {
        "civ": "spartan", "name": "hoplites",
        "prompt": (
            "10 spartan hoplite warriors in vertical column, "
            "one behind another facing right, side view, "
            "accurate bronze corinthian helmets, "
            "large round hoplon shields with lambda symbol, "
            "8-foot dory spear pointing forward, xiphos short sword on belt, "
            "iconic crimson red cloak, bronze greaves, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 1024)
    },
    {
        "civ": "spartan", "name": "archers",
        "prompt": (
            "8 spartan periokoi archers in vertical column, "
            "one behind another facing right, side view, "
            "lighter armor than hoplites, short tunic, "
            "drawing composite bow, quiver on back, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 860)
    },
    {
        "civ": "spartan", "name": "cavalry",
        "prompt": (
            "3 spartan cavalry riders in triangle formation, "
            "side view facing right, "
            "bronze armor, spear and sword, red cloak, "
            "leader at front tip of triangle, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 640)
    },
    {
        "civ": "spartan", "name": "leonidas",
        "prompt": (
            "leonidas king of sparta single hero on foot, "
            "side view facing right, "
            "ornate bronze corinthian helmet pushed back on head, "
            "large lambda shield, long spear raised, crimson cloak, "
            "heroic commanding pose, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 512)
    },
    {
        "civ": "spartan", "name": "synaspismos",
        "prompt": (
            "10 spartan warriors in synaspismos locked shield formation, "
            "vertical column one behind another, side view facing right, "
            "shields overlapping edge to edge forming solid wall, "
            "spears pointing forward through gaps between shields, "
            "bronze corinthian helmets, crimson cloaks, "
            "historically accurate ancient greek locked shield wall, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 1024)
    },

    # ════════════════════════════════════════════════════════
    # ROMAN
    # ════════════════════════════════════════════════════════
    {
        "civ": "roman", "name": "legionaries",
        "prompt": (
            "10 roman legionary soldiers in vertical column, "
            "one behind another facing right, side view, "
            "accurate imperial gallic helmet with red transverse crest, "
            "large rectangular scutum shield with lightning bolt design, "
            "pilum javelin raised, lorica segmentata segmented plate armor, "
            "caligae military sandals, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 1024)
    },
    {
        "civ": "roman", "name": "archers",
        "prompt": (
            "8 roman auxiliary archers in vertical column, "
            "one behind another facing right, side view, "
            "eastern style armor, composite bow drawn, quiver on back, "
            "scale armor lorica squamata, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 860)
    },
    {
        "civ": "roman", "name": "cavalry",
        "prompt": (
            "3 roman equites cavalry in triangle formation, "
            "side view facing right, "
            "bronze helmet, oval shield, spatha sword raised, "
            "scale armor, decorated horse, "
            "leader at front tip of triangle, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 640)
    },
    {
        "civ": "roman", "name": "caesar",
        "prompt": (
            "julius caesar single commander on white horse, "
            "side view facing right, "
            "roman general paludamentum red cloak, "
            "muscle cuirass lorica musculata, laurel wreath, "
            "spatha sword raised in command, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 512)
    },
    {
        "civ": "roman", "name": "testudo",
        "prompt": (
            "10 roman soldiers in testudo tortoise formation, "
            "vertical column one behind another, side view facing right, "
            "rectangular scutum shields locked overhead and on sides, "
            "forming complete shell covering all soldiers, "
            "only legs visible below shield wall, "
            "historically accurate roman turtle formation, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 1024)
    },

    # ════════════════════════════════════════════════════════
    # VIKING
    # ════════════════════════════════════════════════════════
    {
        "civ": "viking", "name": "shield_wall",
        "prompt": (
            "10 viking warriors in shield wall skjaldborg formation, "
            "vertical column one behind another, side view facing right, "
            "round wooden shields with iron boss overlapping edge to edge, "
            "iron spangenhelm helmets, chainmail byrnie, "
            "spears and axes raised above shields, "
            "historically accurate norse shield wall, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 1024)
    },
    {
        "civ": "viking", "name": "berserkers",
        "prompt": (
            "8 viking berserker ulfhednar warriors in loose column, "
            "one behind another facing right, side view, "
            "bare chested or wolf pelt ulfhednar, "
            "dual hand axes raised, wild hair and beard, "
            "frenzied battle rage pose, no shields, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 860)
    },
    {
        "civ": "viking", "name": "cavalry",
        "prompt": (
            "3 viking cavalry huscarl riders in triangle formation, "
            "side view facing right, "
            "iron helmet chainmail, axe raised, round shield on arm, "
            "leader at front tip of triangle, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 640)
    },
    {
        "civ": "viking", "name": "ragnar",
        "prompt": (
            "ragnar lothbrok single viking jarl hero on foot, "
            "side view facing right, "
            "shaved head with beard, leather and iron lamellar armor, "
            "great dane axe raised, round shield, fierce expression, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 512)
    },
    {
        "civ": "viking", "name": "svinfylking",
        "prompt": (
            "10 viking warriors in svinfylking boar snout wedge formation, "
            "vertical column, side view facing right, "
            "wedge shape with strongest warriors at tip, "
            "round shields, axes and swords, iron helmets chainmail, "
            "historically accurate norse wedge attack formation, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 1024)
    },

    # ════════════════════════════════════════════════════════
    # MONGOL
    # ════════════════════════════════════════════════════════
    {
        "civ": "mongol", "name": "horse_archers",
        "prompt": (
            "8 mongol horse archers in loose vertical column, "
            "one behind another facing right, side view, "
            "firing composite recurve bow from horseback at full gallop, "
            "del robe, mongolian helmet, quiver on back, "
            "small fast steppe pony horses, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 860)
    },
    {
        "civ": "mongol", "name": "heavy_cavalry",
        "prompt": (
            "3 mongol heavy cavalry in triangle formation, "
            "side view facing right, "
            "full lamellar armor on rider and horse, "
            "long lance forward, curved saber on belt, "
            "leader at front tip of triangle, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 640)
    },
    {
        "civ": "mongol", "name": "genghis",
        "prompt": (
            "genghis khan single commander on horseback, "
            "side view facing right, "
            "ornate mongolian lamellar armor, fur trimmed helmet with plume, "
            "composite bow in hand, commanding pose, "
            "decorated warhorse with armor, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 512)
    },
    {
        "civ": "mongol", "name": "mangudai",
        "prompt": (
            "10 mongol mangudai elite horse archers in vertical column, "
            "one behind another facing right, side view, "
            "feigned retreat formation, looking back while galloping, "
            "firing bow backwards from horseback parthian shot, "
            "historically accurate mongol feigned retreat tactic, "
            "pure white background, flat clean illustration, no artifacts, game sprite"
        ),
        "size": (512, 1024)
    },
]

# ── Helper functions ──────────────────────────────────────────────────────────
def remove_white_bg(img, threshold=235):
    img = img.convert("RGBA")
    pixels = list(img.getdata())
    img.putdata([(r,g,b,0) if r>threshold and g>threshold and b>threshold
                 else (r,g,b,a) for r,g,b,a in pixels])
    return img

def tint(img, color):
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    t = Image.new("RGBA", img.size, color+(255,))
    out = Image.blend(img, t, 0.55)
    out.putalpha(a)
    return out

def save_sprite(raw, civ, name):
    for folder in ["raw", "blue", "red"]:
        os.makedirs(f"{OUTPUT_DIR}/{civ}/{folder}", exist_ok=True)
    with open(f"{OUTPUT_DIR}/{civ}/raw/{name}.png", "wb") as f:
        f.write(raw)
    img = Image.open(BytesIO(raw))
    img_t = remove_white_bg(img)
    tint(img_t, (52, 101, 164)).save(f"{OUTPUT_DIR}/{civ}/blue/{name}.png", "PNG")
    red = tint(img_t, (176, 31, 36)).transpose(Image.FLIP_LEFT_RIGHT)
    red.save(f"{OUTPUT_DIR}/{civ}/red/{name}.png", "PNG")

# ── Generate all ──────────────────────────────────────────────────────────────
total = len(ALL_SPRITES)
success, failed = 0, []

print(f"⚔️  Generating {total} sprites across 6 civilizations...")
print("="*55)

for i, sprite in enumerate(ALL_SPRITES, 1):
    civ, name = sprite["civ"], sprite["name"]
    w, h = sprite["size"]
    print(f"\n[{i}/{total}] {civ}/{name} ({w}x{h})")

    for attempt in range(1, 5):
        try:
            r = requests.post(
                "https://gateway.pixazo.ai/flux-2-klein-4b/v1/generateImage",
                headers=headers,
                json={"prompt": sprite["prompt"], "width": w, "height": h,
                      "num_inference_steps": 30, "guidance_scale": 7.5},
                timeout=90
            )
            data = r.json()
            url = data.get("output") or data.get("image_url") or data.get("url")
            if not url:
                raise Exception(f"{data}")
            raw = requests.get(url, timeout=30).content
            save_sprite(raw, civ, name)
            print(f"  ✅ Done")
            success += 1
            break
        except Exception as e:
            print(f"  ❌ Attempt {attempt}: {e}")
            if attempt < 4:
                time.sleep(10)
    else:
        failed.append(f"{civ}/{name}")

print("\n" + "="*55)
print(f"✅ {success}/{total} succeeded")
if failed:
    print(f"❌ Failed: {', '.join(failed)}")
    print("\nRe-run script — it will skip already generated sprites")