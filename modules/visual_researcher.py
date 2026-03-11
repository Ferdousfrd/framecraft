# modules/visual_researcher.py
# FrameCraft — Visual Research Module
#
# This module runs BEFORE script generation.
# It researches historical accuracy for characters, armies, and settings
# so the script writer can generate visually correct image prompts.
#
# Flow:
#   Topic + characters detected
#       → Groq researches historical appearances
#       → Returns structured visual reference data
#       → Script generator uses this data in visual descriptions
#
# This solves the problem of Flux generating generic warriors
# instead of historically accurate characters like Alexander the Great
# on his white horse Bucephalus in Macedonian bronze armor.
#
# Author: Ferdous
# Part of: FrameCraft Pipeline

import os
import json
from groq import Groq
from config.settings import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def research_visual_context(topic: str, language: str = "en") -> dict:
    """
    Researches historical visual context for a given topic.
    Returns detailed appearance descriptions for characters, armies,
    settings and props so image AI generates historically accurate visuals.

    Args:
        topic:    The story topic e.g. "Alexander the Great at Gaugamela"
        language: Language code (for context only, research always in English)

    Returns:
        Dictionary with visual research data:
        {
            "main_character": {
                "name": "Alexander the Great",
                "appearance": "young man in his mid-20s, clean shaven...",
                "clothing": "Macedonian bronze breastplate, red cape...",
                "weapon": "sarissa spear, sword at hip",
                "mount": "Bucephalus, large black horse with white star on forehead",
                "distinctive": "intense gaze, slightly upturned nose, muscular"
            },
            "supporting_characters": [...],
            "enemy_army": {
                "name": "Persian Empire",
                "appearance": "diverse soldiers from across Persian empire...",
                "clothing": "colorful silk robes, scale armor, pointed helmets...",
                "weapons": "curved scimitars, composite bows, spears",
                "special": "war elephants, scythed chariots, vast numbers"
            },
            "setting": {
                "location": "flat plain of Gaugamela, modern day Iraq",
                "terrain": "flat dusty plain, dry grass, no trees",
                "time_period": "331 BC",
                "weather": "hot dry Middle Eastern climate"
            },
            "era_details": "Greek Macedonian era 300s BC, bronze age weapons..."
        }
    """

    print(f"\n🔍 Researching visual context for: {topic}")

    prompt = f"""
    You are a historical visual researcher for a cinematic history channel.
    Your job is to research the exact visual appearance of historical figures,
    armies, and settings so an AI image generator can create accurate images.

    Research topic: {topic}

    Return ONLY a JSON object with this exact structure, nothing else:
    {{
        "main_character": {{
            "name": "full name of main historical figure",
            "appearance": "detailed physical description: age, face, hair, build",
            "clothing": "exact historically accurate armor/clothing description",
            "weapon": "historically accurate weapons they carried",
            "mount": "horse or other mount if applicable, with description",
            "distinctive": "unique identifying features that make them recognizable"
        }},
        "supporting_characters": [
            {{
                "name": "name",
                "appearance": "appearance",
                "clothing": "clothing",
                "role": "their role in the story"
            }}
        ],
        "enemy_army": {{
            "name": "name of opposing force",
            "appearance": "how soldiers looked physically",
            "clothing": "their armor and clothing",
            "weapons": "their weapons",
            "special": "any special units like elephants, chariots, cavalry"
        }},
        "ally_army": {{
            "name": "name of allied force if any",
            "appearance": "how soldiers looked",
            "clothing": "their armor and clothing",
            "weapons": "their weapons",
            "formation": "how they fought, famous formations"
        }},
        "setting": {{
            "location": "exact historical location name",
            "terrain": "what the landscape looked like",
            "time_period": "exact date or period",
            "weather": "typical climate/weather for that region"
        }},
        "era_details": "brief description of the historical era, technology level, visual style",
        "image_prompt_prefix": "a single sentence to prepend to ALL image prompts to ensure historical accuracy. Example: 'Ancient Greek Macedonian era 331 BC, bronze age armor, Mediterranean setting'"
    }}

    Be extremely specific and historically accurate.
    Focus on visual details that an image AI needs to generate correct images.
    Include colors, materials, specific armor types, horse breeds if known.
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )

            raw = response.choices[0].message.content.strip()

            # Clean JSON if wrapped in markdown
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            research = json.loads(raw)

            # Print summary
            main = research.get("main_character", {})
            enemy = research.get("enemy_army", {})
            setting = research.get("setting", {})

            print(f"  ✅ Research complete!")
            print(f"  👤 Main character: {main.get('name', 'Unknown')}")
            print(f"  ⚔️  Enemy: {enemy.get('name', 'Unknown')}")
            print(f"  📍 Setting: {setting.get('location', 'Unknown')}")
            print(f"  🎨 Prefix: {research.get('image_prompt_prefix', '')}")

            return research

        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON parse failed attempt {attempt + 1}: {e}")
            if attempt == 2:
                print(f"  ❌ Research failed — using empty context")
                return _empty_research()

        except Exception as e:
            print(f"  ⚠️  Research attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                print(f"  ❌ Research failed — using empty context")
                return _empty_research()

    return _empty_research()


def format_character_description(research: dict) -> str:
    """
    Formats research data into a concise character description string
    that gets injected into the script generator prompt.

    Args:
        research: Research dictionary from research_visual_context()

    Returns:
        Formatted string describing characters and setting for script writer
    """

    if not research or research.get("empty"):
        return ""

    lines = []
    lines.append("HISTORICAL VISUAL REFERENCE — use these in ALL visual descriptions:")

    # Main character
    main = research.get("main_character", {})
    if main.get("name"):
        desc_parts = [
            main.get("appearance", ""),
            main.get("clothing", ""),
            main.get("weapon", ""),
            main.get("mount", ""),
            main.get("distinctive", "")
        ]
        desc = ", ".join(p for p in desc_parts if p)
        lines.append(f"\nMAIN CHARACTER — {main['name']}:")
        lines.append(f"  Always describe as: {desc}")

    # Enemy army
    enemy = research.get("enemy_army", {})
    if enemy.get("name"):
        enemy_parts = [
            enemy.get("appearance", ""),
            enemy.get("clothing", ""),
            enemy.get("weapons", ""),
            enemy.get("special", "")
        ]
        enemy_desc = ", ".join(p for p in enemy_parts if p)
        lines.append(f"\nENEMY ARMY — {enemy['name']}:")
        lines.append(f"  Always describe as: {enemy_desc}")

    # Ally army
    ally = research.get("ally_army", {})
    if ally.get("name"):
        ally_parts = [
            ally.get("appearance", ""),
            ally.get("clothing", ""),
            ally.get("weapons", ""),
            ally.get("formation", "")
        ]
        ally_desc = ", ".join(p for p in ally_parts if p)
        lines.append(f"\nALLY ARMY — {ally['name']}:")
        lines.append(f"  Always describe as: {ally_desc}")

    # Setting
    setting = research.get("setting", {})
    if setting.get("location"):
        lines.append(f"\nSETTING — {setting['location']}:")
        lines.append(f"  Terrain: {setting.get('terrain', '')}")
        lines.append(f"  Period: {setting.get('time_period', '')}")

    # Image prefix
    prefix = research.get("image_prompt_prefix", "")
    if prefix:
        lines.append(f"\nIMAGE STYLE PREFIX (add to every visual): {prefix}")

    return "\n".join(lines)


def _empty_research() -> dict:
    """Returns empty research dict when research fails."""
    return {
        "empty": True,
        "main_character": {},
        "enemy_army": {},
        "ally_army": {},
        "setting": {},
        "era_details": "",
        "image_prompt_prefix": ""
    }


if __name__ == "__main__":
    # Test the module
    test_topic = "Alexander the Great - the battle of Gaugamela 331 BC"
    research = research_visual_context(test_topic)

    print("\n" + "="*50)
    print("FORMATTED CHARACTER DESCRIPTION:")
    print("="*50)
    print(format_character_description(research))
