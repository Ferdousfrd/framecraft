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
    You are a script writer for IronNorth, a short-form video channel 
    about Viking and Finnish history.

    Create a 60-second narration script about: {topic}

    STRICT RULES:
    - Split the script into exactly 5 segments
    - Each segment is 1-2 sentences maximum
    - Language must be {language}
    - Tone is dramatic, engaging, educational
    - Each segment needs a visual description for stock footage
    - Start with a hook that grabs attention immediately
    - Only use historically verified facts
    - If unsure about a specific detail, omit it rather than guess
    - Never invent names, dates, or events
    - Clearly distinguish between historical fact and legend

    {fix_instructions}

    Return ONLY a JSON object in this exact format, nothing else:
    {{
        "title": "short catchy title for the video",
        "topic": "{topic}",
        "language": "{language}",
        "segments": [
            {{
                "id": 1,
                "narration": "the words spoken in this segment",
                "visual": "description of what should be shown visually",
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