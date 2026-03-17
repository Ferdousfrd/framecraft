# modules/battle_researcher.py
# FrameCraft Pipeline 2 — Battle Research Module
#
# PURPOSE:
#   Researches a historical battle and returns structured data.
#   This is STEP 1 — only facts, positions, army data.
#   NO long narration strings here — those are generated separately.
#
# KEY DESIGN DECISION:
#   We keep all string values SHORT (under 8 words) to avoid
#   JSON parse errors from long strings with commas.
#   Long descriptions come later in battle_script.py
#
# Author: Ferdous
# Part of: FrameCraft Pipeline 2

import os
import re
import json
from google import genai
from google.genai import types
from config.settings import GEMINI_API_KEY

# ── Gemini client ─────────────────────────────────────────────────────────────
client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "gemini-2.5-flash"


def research_battle(topic: str) -> dict:
    """
    Researches a historical battle.
    Returns structured facts — NO long strings, NO narration.
    Short fields only to avoid JSON parsing issues.

    Args:
        topic: e.g. "Battle of Gaugamela 331 BC"

    Returns:
        Dict with battle facts, army data, and phase summaries
    """

    print(f"\n{'='*55}")
    print(f"⚔️  BATTLE RESEARCHER")
    print(f"{'='*55}")
    print(f"📖 Researching: {topic}")

    for attempt in range(1, 4):
        print(f"\n  🔄 Attempt {attempt}/3...")
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=_build_prompt(topic),
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                    response_mime_type="application/json"
                )
            )

            raw = response.text.strip()
            print(f"  📥 Received {len(raw)} chars")

            # Clean markdown wrappers if present
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            try:
                research = json.loads(raw)
            except json.JSONDecodeError as e:
                lines = raw.split('\n')
                err_line = e.lineno - 1
                print(f"  ❌ Problem on line {e.lineno}: {e.msg}")
                for i in range(max(0, err_line-2), min(len(lines), err_line+3)):
                    print(f"    {i+1}: {lines[i]}")
                raise

            print(f"  ✅ Parse successful!")
            _print_summary(research)
            return research

        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON error: {e}")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")

    print(f"  ❌ All attempts failed")
    return _empty(topic)


def _build_prompt(topic: str) -> str:
    """
    Builds a prompt that returns ONLY short string values.
    This prevents JSON parse errors from long strings with commas.
    All coordinates are on a 0-100 grid (x=left-right, y=top-bottom).
    Ally army starts LEFT side, enemy starts RIGHT side.
    """
    return f"""Research this battle: {topic}

Return ONLY valid JSON. Rules:
- ALL string values must be SHORT - maximum 8 words each
- No apostrophes anywhere
- No commas inside string values
- Numbers for coordinates not strings

{{
    "battle_name": "short battle name",
    "date": "date or year",
    "location": "place name country",
    "terrain_type": "terrain description max 6 words",
    "weather": "weather max 4 words",
    "outcome": "winner and result max 6 words",
    "significance": "why important max 6 words",

    "ally": {{
        "name": "army name",
        "commander": "commander name",
        "strength": 47000,
        "infantry": 40000,
        "cavalry": 7000,
        "special": "special units or none",
        "civ_type": "macedonian"
    }},

    "enemy": {{
        "name": "army name",
        "commander": "commander name",
        "strength": 100000,
        "infantry": 80000,
        "cavalry": 15000,
        "special": "special units or none",
        "civ_type": "persian"
    }},

    "phases": [
        {{
            "num": 1,
            "name": "phase name max 4 words",
            "ally_move": "ally action max 6 words",
            "enemy_move": "enemy action max 6 words",
            "key_event": "key event max 6 words",
            "ally_infantry_x": 25,
            "ally_infantry_y": 50,
            "ally_cav_left_x": 25,
            "ally_cav_left_y": 30,
            "ally_cav_right_x": 25,
            "ally_cav_right_y": 70,
            "ally_commander_x": 15,
            "ally_commander_y": 30,
            "enemy_infantry_x": 75,
            "enemy_infantry_y": 50,
            "enemy_cav_left_x": 75,
            "enemy_cav_left_y": 30,
            "enemy_cav_right_x": 75,
            "enemy_cav_right_y": 70,
            "enemy_commander_x": 85,
            "enemy_commander_y": 50
        }}
    ]
}}

Replace with accurate historical data for: {topic}
Include exactly 3 phases only. Keep all responses extremely brief.
Ally army x coordinates: 15-45 (LEFT side of map).
Enemy army x coordinates: 55-85 (RIGHT side of map).
y coordinates: 10-90 (top to bottom of map).
civ_type must be one of: macedonian persian spartan roman viking mongol
"""


def _print_summary(r: dict) -> None:
    """Prints a clean summary of research results."""
    print(f"\n  {'─'*45}")
    print(f"  ⚔️  {r.get('battle_name', '?')}  |  {r.get('date', '?')}")
    print(f"  📍 {r.get('location', '?')}")
    print(f"  🏆 {r.get('outcome', '?')}")
    print(f"  🔵 {r.get('ally', {}).get('name', '?')} — {r.get('ally', {}).get('commander', '?')}")
    print(f"  🔴 {r.get('enemy', {}).get('name', '?')} — {r.get('enemy', {}).get('commander', '?')}")
    phases = r.get('phases', [])
    print(f"  📋 {len(phases)} phases:")
    for p in phases:
        print(f"     Phase {p.get('num', '?')}: {p.get('name', '?')} — {p.get('key_event', '?')}")
    print(f"  {'─'*45}")


def save_research(research: dict, output_dir: str = "outputs/battle_research") -> str:
    """Saves research JSON to disk for inspection and reuse."""
    os.makedirs(output_dir, exist_ok=True)
    name     = research.get('battle_name', 'unknown').lower().replace(' ', '_')[:40]
    filepath = os.path.join(output_dir, f"{name}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(research, f, indent=2, ensure_ascii=False)
    print(f"\n  💾 Saved: {filepath}")
    return filepath


def load_research(filepath: str) -> dict:
    """Loads previously saved research — avoids re-calling API during testing."""
    print(f"  📂 Loading: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def _empty(topic: str) -> dict:
    """Returns empty dict when research fails."""
    return {
        "empty": True,
        "battle_name": topic,
        "date": "", "location": "", "terrain_type": "",
        "ally": {}, "enemy": {}, "phases": []
    }


# ══════════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Test: python3 -m modules.battle_researcher
    """
    research = research_battle("Battle of Gaugamela 331 BC")

    if research.get("empty"):
        print("\n❌ Research failed")
    else:
        filepath = save_research(research)
        print(f"\n✅ Success! Check: {filepath}")