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

# Initialize the Groq client with our API key
# This client is reused for all API calls in this module
client = Groq(api_key=GROQ_API_KEY)

def generate_script(topic: str, language: str = "en", issues: list = None) -> dict:
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

    # Main prompt sent to the AI
    # Double curly braces {{ }} are used because we're inside an f-string
    # and we need literal { } characters in the JSON template
    prompt = f"""
    You are a cinematic script writer for IronNorth, a viral short-form 
    history channel. Your reels make people feel like they are INSIDE history.
    Every visual must match the narration exactly — like a movie scene.

    Create a 60-second script about: {topic}

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
    - If narration mentions Ragnar — visual shows Ragnar specifically
    - If narration mentions longships on a river — visual shows longships on river
    - If narration mentions Paris burning — visual shows medieval city on fire
    - Describe the scene like a movie shot: who is in it, what are they doing,
      what is the setting, what is the mood, what time of day
    - ALWAYS medieval or ancient setting — zero modern elements
    - NEVER: modern buildings, Eiffel Tower, aerial views, present day anything
    - NEVER: generic "Viking warriors" — be specific to the narration moment
    - Style: oil painting, cinematic lighting, dramatic atmosphere
    - Example good visual: "Ragnar Lothbrok standing at the prow of his longship,
      Seine river ahead, smoke rising from burning villages on both banks,
      golden dawn light, oil painting style"
    - Example bad visual: "Aerial footage of Paris with Viking ships"

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