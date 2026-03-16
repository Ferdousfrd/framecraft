# modules/script_generator.py
# FrameCraft — Script Generation Module
#
# Uses Google Gemini for script generation (higher token limits than Groq).
# Generates story-driven 60-second narration scripts with 5 segments.
# Supports multi-part series with correct story arc per part.
#
# Author: Ferdous
# Part of: FrameCraft Pipeline

import json
import re
from google import genai
from google.genai import types
from config.settings import GEMINI_API_KEY
client = genai.Client(api_key=GEMINI_API_KEY)
from modules.visual_researcher import research_visual_context, format_character_description


def _detect_series_info(topic: str) -> dict:
    """
    Detects if topic is part of a series and extracts part info.
    Returns dict with: is_series, part_num, total_parts, series_name
    """
    import re
    info = {"is_series": False, "part_num": 1, "total_parts": 1, "series_name": ""}

    # Match "Part X of Y" or "Part X/Y"
    match = re.search(r'part\s+(\d+)\s+of\s+(\d+)', topic, re.IGNORECASE)
    if match:
        info["is_series"]   = True
        info["part_num"]    = int(match.group(1))
        info["total_parts"] = int(match.group(2))
        # Series name = everything before "Part"
        info["series_name"] = topic[:match.start()].strip(" -—:")

    return info


def _build_series_instructions(series: dict) -> str:
    """Builds story arc instructions based on which part this is."""

    if not series["is_series"]:
        return ""

    part     = series["part_num"]
    total    = series["total_parts"]
    is_first = part == 1
    is_last  = part == total

    instructions = f"""
SERIES STORY ARC — This is Part {part} of {total}:
- Tell ONLY what happens in Part {part}. Do NOT jump ahead to later parts.
- The full story arc spans all {total} parts. Stay in your lane.
- Each segment covers only events that belong to Part {part}'s chapter.
"""

    if is_first:
        instructions = f"""
SERIES STORY ARC — This is Part {part} of {total}:
- Tell ONLY what happens in Part {part}. Do NOT jump ahead to later parts.
- The full story arc spans all {total} parts. Stay in your lane.
- Each segment covers only events that belong to Part {part}'s chapter.
"""

    if is_first:
        instructions += """
PART 1 RULES:
- Segment 1: Hook — establish the world and stakes dramatically
- Segment 2: Introduce the main character with vivid detail — this is the ONLY part where you describe who they are
- Segment 3: Show their first challenge or formative moment
- Segment 4: First major achievement or turning point
- Segment 5: Cliffhanger ending — hint at what's coming in Part 2
  Example: "But his greatest test had not yet begun..."
  Example: "Little did he know, destiny had other plans..."
"""

    elif is_last:
        instructions += f"""
PART {part} RULES (FINAL PART):
- Segment 1: Pick up where Part {part-1} left off — new scene, new challenge, NO re-introduction
- Segments 2-4: Build to the final climax of the whole story
- Segment 5: Powerful conclusion — legacy, what they left behind, why we remember them
  This is the PAYOFF for viewers who watched all {total} parts

CHARACTER RULE — CRITICAL:
- Viewer already knows who the character is from Part 1 — DO NOT re-introduce them
- NEVER write "[name], son of..." or describe their appearance again
- Jump straight into the action and events of this chapter
- Every segment should show EVENTS not character portraits
"""
    else:
        instructions += f"""
PART {part} RULES (MIDDLE PART):
- Segment 1: Pick up where Part {part-1} left off — new scene, new challenge, NO re-introduction
- Segments 2-4: This part's unique events only — new locations, new battles, new challenges
- Segment 5: New cliffhanger — something even bigger is coming in Part {part+1}
  Example: "But nothing could prepare him for what came next..."

CHARACTER RULE — CRITICAL:
- Viewer already knows who the character is from Part 1 — DO NOT re-introduce them
- NEVER write "[name], son of..." or describe their appearance again
- NEVER do a character portrait shot in Parts 2, 3 or 4
- Every segment shows EVENTS and ACTION — not who the character is
"""


    return instructions


def _build_visual_rules(topic: str) -> str:
    """
    Builds visual rules customized to the topic.
    Detects if topic is land-based vs sea-based to avoid wrong settings.
    """
    topic_lower = topic.lower()

    # Detect topic type to avoid wrong settings
    is_sea_topic    = any(w in topic_lower for w in ["raid", "sail", "ship", "sea", "fleet", "mediterranean", "voyage"])
    is_land_topic   = any(w in topic_lower for w in ["battle", "siege", "king", "throne", "death", "life", "legacy", "army"])
    is_greek_roman  = any(w in topic_lower for w in ["alexander", "roman", "caesar", "greek", "sparta", "athens", "persian"])
    is_viking       = any(w in topic_lower for w in ["viking", "norse", "ragnar", "bjorn", "ivar", "leif", "odin"])
    is_mongol       = any(w in topic_lower for w in ["mongol", "genghis", "khan", "horde"])

    # Setting-specific style notes
    setting_note = ""
    if is_greek_roman:
        setting_note = "Setting: Ancient Greek/Roman/Persian era — marble columns, bronze armor, Mediterranean landscapes, olive trees, dusty plains. NO longships, NO Viking elements."
    elif is_viking:
        setting_note = "Setting: Viking Age Scandinavia — wooden halls, fjords, iron helmets, fur cloaks, axes and shields, Norse runes."
        if not is_sea_topic:
            setting_note += " This story is LAND-BASED — show forests, halls, battlefields. Longships ONLY if narration specifically mentions sailing."
    elif is_mongol:
        setting_note = "Setting: Mongol Empire — vast steppes, felt gers/yurts, horse archers, lamellar armor, Central Asian landscapes."

    return f"""
VISUAL RULES — LOCKED, NO EXCEPTIONS:

STYLE: Every single segment MUST end with "dramatic oil painting style, masterpiece quality, rich textures, deep shadows"
- Think Rembrandt lighting meets Frank Frazetta epic fantasy art
- Rich colors: deep reds, golds, dark blues, warm firelight
- NEVER use words: photorealistic, cinematic, film still, photograph, digital art

{setting_note}

STORY-VISUAL SYNC — CRITICAL:
- Each visual must show EXACTLY what the narrator is saying at that moment
- If narration says "he led 300 warriors" → show 300 warriors, not 1 man
- If narration says "Paris burned" → show Paris burning, not a ship
- If narration says "he died alone" → show a single figure, not a battle

VARIETY — 5 DIFFERENT SCENES, NO REPEATS:
- Segment 1: WIDE mysterious establishing shot — dark, foreboding, epic scale. 
  Show the WORLD before the story begins. Misty fjords, dark stormy skies, 
  vast armies gathering at dawn, mysterious ancient landscapes. NO main character.
  Make viewer feel something BIG is about to happen.
- Segment 2: CHARACTER shot — introduce hero with their army/environment behind them
- Segment 3: CONFLICT — battle, clash, obstacle. Multiple warriors, chaos, action
- Segment 4: CLIMAX — the decisive moment, movement, peak drama
- Segment 5: AFTERMATH — consequence, legacy. Empty battlefield OR symbolic final image

NEVER repeat the same location, same composition, or same mood across segments.
NEVER show a lone figure standing on a ship unless narration describes exactly that.

SHOT COMPOSITION — always specify one:
- "wide establishing shot looking down" = shows scale
- "low angle looking up" = makes subject look powerful  
- "eye level medium shot" = intimate, personal
- "over the shoulder wide shot" = viewer in the scene
- "high angle wide shot" = shows battlefield scale
"""


def generate_script(topic: str, language: str = "en", skip_research: bool = False, issues: list = None) -> dict:
    """
    Generates a 60-second story-driven narration script using Gemini.

    Args:
        topic:         The video topic e.g. "Bjorn Ironside Part 1 of 4"
        language:      Language code — "en", "bn", "fi"
        skip_research: Skip visual research (faster, less accurate)
        issues:        Fact-check issues from previous attempt to fix

    Returns:
        Script dictionary with 5 segments
    """

    # Detect series info
    series = _detect_series_info(topic)

    # Build fix instructions if retrying
    fix_instructions = ""
    if issues:
        fix_instructions = "\nFIX THESE ISSUES FROM PREVIOUS ATTEMPT:\n"
        for i, issue in enumerate(issues, 1):
            fix_instructions += f"""
Issue {i}: {issue['type'].upper()}
Original: {issue['original']}
Problem:  {issue['issue']}
Fix:      {issue['correction']}
"""

    # Research historical visual context
    visual_context = ""
    if not skip_research:
        research    = research_visual_context(topic, language)
        visual_context = format_character_description(research)
        if visual_context:
            print(f"  ✅ Visual research injected into script prompt")

    # Build full prompt
    prompt = f"""
You are a cinematic script writer for IronNorth, a viral short-form history channel.
Your reels make people feel like they are INSIDE history.
Write a 60-second script about: {topic}

{_build_series_instructions(series)}

NARRATION RULES:
- Exactly 5 segments
- Language: {language}
- Tone: dramatic, like a movie trailer narrator — powerful, not academic
- Segment 1: Hook — first 3 words MUST grab attention instantly
  Good: "Five thousand warriors...", "One sword blow...", "Paris was burning..."
  Bad: "In the year...", "Today we talk about...", "This is the story..."
- Segments 2-4: Build the specific story of THIS PART only — vivid details, names, numbers
- Segment 5: {"Cliffhanger ending hinting at Part " + str(series["part_num"]+1) if series["is_series"] and series["part_num"] < series["total_parts"] else "Powerful legacy closing — why we still remember them"}
- Only historically verified facts. Omit if unsure rather than invent.
- AVOID specific troop numbers unless historically verified (e.g. don't say "5000 warriors" — say "a vast army")
- AVOID specific dates unless certain — say "in the 9th century" not "in 847 AD"

{_build_visual_rules(topic)}

{visual_context}

{fix_instructions}

Return ONLY valid JSON, nothing else — no explanation, no markdown, no code blocks:
{{
    "title": "short punchy title max 6 words",
    "topic": "{topic}",
    "language": "{language}",
    "segments": [
        {{
            "id": 1,
            "narration": "words spoken by narrator",
            "visual": "detailed visual description ending with: dramatic oil painting style, masterpiece quality, rich textures",
            "duration": 12
        }},
        {{
            "id": 2,
            "narration": "words spoken by narrator",
            "visual": "detailed visual description ending with: dramatic oil painting style, masterpiece quality, rich textures",
            "duration": 12
        }},
        {{
            "id": 3,
            "narration": "words spoken by narrator",
            "visual": "detailed visual description ending with: dramatic oil painting style, masterpiece quality, rich textures",
            "duration": 12
        }},
        {{
            "id": 4,
            "narration": "words spoken by narrator",
            "visual": "detailed visual description ending with: dramatic oil painting style, masterpiece quality, rich textures",
            "duration": 12
        }},
        {{
            "id": 5,
            "narration": "words spoken by narrator",
            "visual": "detailed visual description ending with: dramatic oil painting style, masterpiece quality, rich textures",
            "duration": 12
        }}
    ]
}}
"""

    # Call Gemini
    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=4000,
                )
            )
            raw = response.text.strip()

            # Clean markdown if present
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            # Parse JSON
            try:
                script = json.loads(raw)
            except json.JSONDecodeError:
                # Fix common issues: smart quotes, apostrophes in strings
                raw_fixed = raw.replace("'", "\\'").replace("\u2019", "\\'").replace("\u201c", '\\"').replace("\u201d", '\\"')
                try:
                    script = json.loads(raw_fixed)
                except json.JSONDecodeError:
                    match = re.search(r'\{.*\}', raw, re.DOTALL)
                    if match:
                        try:
                            script = json.loads(match.group())
                        except json.JSONDecodeError:
                            import ast
                            script = ast.literal_eval(match.group())
                    else:
                        raise

            return script

        except Exception as e:
            print(f"  ⚠️  Gemini attempt {attempt} failed: {e}")
            if attempt == 3:
                raise


def print_script(script: dict) -> None:
    print(f"\n{'='*50}")
    print(f"TITLE: {script['title']}")
    print(f"TOPIC: {script['topic']}")
    print(f"LANGUAGE: {script['language']}")
    print(f"{'='*50}\n")
    for segment in script['segments']:
        print(f"SEGMENT {segment['id']} ({segment['duration']}s)")
        print(f"NARRATION: {segment['narration']}")
        print(f"VISUAL:    {segment['visual']}")
        print(f"{'-'*50}")
