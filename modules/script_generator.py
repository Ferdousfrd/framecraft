# modules/script_generator.py
# FrameCraft — Script Generation Module
# 
# This module is responsible for generating 60-second narration scripts
# using the Groq AI API. It supports two modes:
#   1. Fresh generation — generates a brand new script for a topic
#   2. Fix mode — takes a failed script + its issues and regenerates with fixes
#
# Author: Ferdous
# Part of: FrameCraft Pipeline

import json
from groq import Groq
from config.settings import GROQ_API_KEY
from modules.visual_researcher import research_visual_context, format_character_description

# Initialize the Groq client with our API key
# This client is reused for all API calls in this module
client = Groq(api_key=GROQ_API_KEY)

def generate_script(topic: str, language: str = "en", skip_research: bool = False, issues: list = None) -> dict:
    """
    Generates a 60-second narration script for a given topic.
    
    Args:
        topic:    The video topic e.g. "Viking raid on Paris 845 AD"
        language: Language code — "en" English, "bn" Bengali, "fi" Finnish
        issues:   Optional list of fact-check issues from previous attempt.
                  If provided, AI will try to fix these specific problems.
    
    Returns:
        A dictionary containing the full script split into 5 segments.
        Each segment has: narration, visual description, duration
    """

    # Build the fix instructions if we have issues from a previous attempt
    # This is the feedback loop — we tell the AI exactly what went wrong
    fix_instructions = ""
    if issues:
        fix_instructions = """
        IMPORTANT — Previous version of this script had these problems.
        You MUST fix all of them in this new version:
        """
        for i, issue in enumerate(issues, 1):
            fix_instructions += f"""
        Issue {i}: {issue['type'].upper()}
        Original claim: {issue['original']}
        Problem: {issue['issue']}
        Required fix: {issue['correction']}
        """

    # Research historical visual context before writing script
    visual_context = ""
    if not skip_research:
        research = research_visual_context(topic, language)
        visual_context = format_character_description(research)
        if visual_context:
            print(f"  ✅ Visual research injected into script prompt")

    # Main prompt sent to the AI
    # Double curly braces {{ }} are used because we're inside an f-string
    # and we need literal { } characters in the JSON template

    prompt = f"""
    You are a cinematic script writer for IronNorth, a viral short-form 
    history channel. Your reels make people feel like they are INSIDE history.
    Every visual must match the narration exactly — like a movie scene.

    Create a 60-second script about: {topic}

    SERIES AWARENESS:
    - If the topic mentions "Part X of Y" this is part of a multi-part series
    - Start Part 1 with a strong hook introducing the character
    - Parts 2-4 should briefly reference previous parts naturally in narration
    - Final part should feel like an epic conclusion
    - Each part must end with a subtle cliffhanger or "what comes next" feeling
      so viewers follow for the next part
    - Example ending: "But this was only the beginning...", 
      "His greatest challenge was yet to come...",
      "The snake pit awaited..."

    NARRATION RULES:
    - Exactly 5 segments, each 1-2 sentences
    - Language: {language}
    - Tone: dramatic, cinematic, like a movie trailer narrator
    - Segment 1: Hook — first 3 words must stop the scroll. Start with tension,
      danger, or an astonishing fact. Example: "120 Viking longships...",
      "One man stood...", "Paris was burning..."
    - Segments 2-4: Build the story with vivid details — names, numbers, emotions
    - Segment 5: Powerful closing — the consequence, the legacy, why it matters
    - Only historically verified facts. Never invent names, dates or events.
    - If unsure about a detail, omit it rather than guess.

    VISUAL RULES — THIS IS CRITICAL:
    - Each visual must show EXACTLY what the narration describes at that moment
    - PHOTOREALISTIC style — like a movie still, NOT painting or illustration
    - Real skin texture, real fabric, real dirt, real lighting — cinematic realism
    - NEVER say oil painting, illustration, artwork, animated or drawn
    - Each of the 5 segments MUST show a completely different scene
    - Different location, different subject, different mood per segment
    - Never generate the same scene twice — each segment tells a new visual story
    - Segment 1 ≠ Segment 2 ≠ Segment 3 ≠ Segment 4 ≠ Segment 5

    VARIETY RULE — CRITICAL:
    - Each of the 5 segments MUST show a completely different scene
    - Different location, different subject, different mood per segment
    - Segment 1: establishing world — ships, army, landscape, NO main character yet
    - Segment 2: introduce character — character portrait in their environment
    - Segment 3: conflict/challenge — battle, storm, obstacle, enemy
    - Segment 4: climax — the decisive moment, action, peak drama
    - Segment 5: aftermath — consequence, legacy, emotional closing
    - NEVER show the same location twice
    - NEVER show character alone on ship more than once
    
    SHOT TYPES — vary these across segments for cinematic feel:
    - Segment 1: WIDE establishing shot — show the scale, the world, the setting
    - Segment 2: MEDIUM shot — character getting ready to fight in front of an army, in battlefield
    - Segment 3: WIDE shot — dramatic detail
    - Segment 4: ACTION shot — movement, battle, charge, dramatic moment
    - Segment 5: WIDE or MEDIUM closing shot — powerful final image
    
    CHARACTER CONSISTENCY:
    - Only describe character appearance in segment 2 (introduction)
    - Segments 1, 3, 4, 5 — DO NOT describe the character's face or clothing
    - Instead show the WORLD, the BATTLE, the ENVIRONMENT, the CONSEQUENCE
    - Segment 1: NO character at all — just the world/army/landscape
    - Segment 3: battle scene with multiple warriors — no named character
    - Segment 4: action moment — character from behind or silhouette only
    - Segment 5: aftermath — empty battlefield, legacy, symbolic image
    
    CAMERA ANGLE — always specify:
    - "low angle looking up" = makes subject look powerful/intimidating
    - "eye level" = intimate, personal, relatable  
    - "high angle looking down" = shows scale of army/battlefield
    - "over the shoulder" = puts viewer in the scene
    
    LIGHTING AND MOOD:
    - Dawn/golden hour = hope, new beginning, epic journey
    - Dusk/red sky = danger, battle, blood, end of era
    - Overcast/grey = grim, determined, foreboding
    - Torchlight/fire = chaos, raid, burning, victory
    {visual_context}
    SETTING DETAILS:
    - Always specify time period appropriate details
    - Viking era: longships, fur cloaks, iron helmets, axes, shields
    - Always medieval/ancient — zero modern elements
    - NEVER: modern buildings, aerial city views, present day anything
    
    EXAMPLE GOOD VISUALS:
    - Segment 1 wide: "Wide shot of 300 Viking longships filling a dark fjord 
      at dawn, mist rising from black water, hundreds of warriors at oars, 
      red shields lining the hulls, photorealistic cinematic, low angle"
    - Segment 2 medium-wide: "Ragnar Lothbrok, tall lean Viking, dark hair short beard, 
      worn leather and iron armor, standing at ship stern commanding his crew, 
      10 warriors rowing behind him, ocean horizon ahead, golden dawn light, 
      medium-wide shot showing character AND crew, photorealistic"
    - Segment 3: MEDIUM ACTION shot — two warriors fighting, weapons clashing, battle scene, never a close up of just hands
    - Segment 4 action wide: "Wide battlefield shot, hundreds of Viking warriors 
      clashing with enemy army, swords and axes raised, dust and smoke filling 
      the air, bodies in motion everywhere, chaos of battle, low angle wide shot, 
      photorealistic, no single character focus"
    - Segment 5 wide: "High angle wide shot of Viking camp at night, 
      hundreds of fires burning, longships beached on river bank, 
      Paris burning in distance, aftermath of battle, dead bodies on the ground, crows flying, atmospheric photorealistic"
      
    EXAMPLE BAD VISUALS:
    - "Viking warriors fighting" — too generic
    - "Aerial footage of Paris" — modern/aerial
    - "Oil painting of battle scene" — wrong style
    - "Animated battle map" — wrong style

    {fix_instructions}

    Return ONLY a JSON object in this exact format, nothing else:
    {{
        "title": "short punchy title, max 6 words, makes people want to watch",
        "topic": "{topic}",
        "language": "{language}",
        "segments": [
            {{
                "id": 1,
                "narration": "the words spoken in this segment",
                "visual": "cinematic shot description matching narration exactly",
                "duration": 12
            }},
            {{
                "id": 2,
                "narration": "the words spoken in this segment",
                "visual": "description of what should be shown visually",
                "duration": 12
            }},
            {{
                "id": 3,
                "narration": "the words spoken in this segment",
                "visual": "description of what should be shown visually",
                "duration": 12
            }},
            {{
                "id": 4,
                "narration": "the words spoken in this segment",
                "visual": "description of what should be shown visually",
                "duration": 12
            }},
            {{
                "id": 5,
                "narration": "the words spoken in this segment",
                "visual": "description of what should be shown visually",
                "duration": 12
            }}
        ]
    }}
    """

    # Make the API call to Groq
    # temperature=0.7 means moderately creative — not robotic, not too random
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )

    # Extract the raw text response from the API response object
    raw = response.choices[0].message.content

    # Strip markdown code blocks if AI wrapped response in ``` blocks
    # This is a common AI behavior we need to handle
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    # Parse the JSON string into a Python dictionary
    script = json.loads(raw)
    
    return script


def print_script(script: dict) -> None:
    """
    Prints a script in a readable format for review.
    
    Args:
        script: The script dictionary returned by generate_script()
    """
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


