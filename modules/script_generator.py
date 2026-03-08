# modules/script_generator.py
# Takes a topic and generates a structured 60-second narration script
# Using Groq API (free) - will switch to Claude API later

import json
from groq import Groq
from config.settings import GROQ_API_KEY

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

def generate_script(topic: str, language: str = "en") -> dict:
    """
    Generates a 60-second narration script for a given topic.
    
    Args:
        topic: The video topic e.g. "Viking raid on Paris 845 AD"
        language: Language code - "en" English, "bn" Bengali, "fi" Finnish
    
    Returns:
        A dictionary containing the full script split into segments
    """

    prompt = f"""
    You are a script writer for IronNorth, a short-form video channel 
    about Viking and Finnish history.

    Create a 60-second narration script about: {topic}

    Rules:
    - Split the script into exactly 5 segments
    - Each segment is 1-2 sentences maximum
    - Language must be {language}
    - Tone is dramatic, engaging, educational
    - Each segment needs a visual description for stock footage
    - Start with a hook that grabs attention immediately

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

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Groq's best free model
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,  # creativity level - 0 is robotic, 1 is very creative
        max_tokens=1000
    )

    # Extract the text response
    raw = response.choices[0].message.content

    # Parse JSON response
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