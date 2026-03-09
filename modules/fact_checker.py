# modules/fact_checker.py
# Takes a generated script and verifies historical accuracy
# Uses a second AI call as a fact-checking layer — FrameCraft quality control

import json
from groq import Groq
from config.settings import GROQ_API_KEY

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

def check_facts(script: dict) -> dict:
    """
    Reviews a generated script for historical accuracy.
    
    Args:
        script: The script dictionary from generate_script()
    
    Returns:
        A dictionary with fact check results and cleaned script
    """

    # Build the full narration text for checking
    full_narration = " ".join([
        segment['narration'] 
        for segment in script['segments']
    ])

    prompt = f"""
    You are a strict historical fact checker for IronNorth, 
    a Viking and Finnish history channel.

    Review this script about: {script['topic']}

    SCRIPT TO CHECK:
    {full_narration}

    Your job:
    1. Identify any historically inaccurate claims
    2. Identify any unverified or uncertain claims  
    3. Suggest corrections where needed
    4. Give an overall accuracy score out of 10

    Return ONLY a JSON object in this exact format, nothing else:
    {{
        "accuracy_score": 8,
        "is_approved": true,
        "issues": [
            {{
                "type": "inaccurate or uncertain",
                "original": "the problematic claim from script",
                "issue": "what is wrong or uncertain",
                "correction": "the accurate version"
            }}
        ],
        "overall_notes": "brief overall assessment"
    }}

    If there are no issues, return empty array for issues.
    is_approved should be true if accuracy_score is 7 or above.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,  # low temperature = more precise, less creative
        max_tokens=1000
    )

    raw = response.choices[0].message.content

    # Strip markdown code blocks if present
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    fact_check = json.loads(raw)
    return fact_check


def print_fact_check(fact_check: dict) -> None:
    """
    Prints fact check results in a readable format.
    
    Args:
        fact_check: The fact check dictionary from check_facts()
    """
    print(f"\n{'='*50}")
    print(f"FACT CHECK RESULTS")
    print(f"{'='*50}")
    print(f"Accuracy Score: {fact_check['accuracy_score']}/10")
    print(f"Approved: {'✅ YES' if fact_check['is_approved'] else '❌ NO'}")
    print(f"Notes: {fact_check['overall_notes']}")
    
    if fact_check['issues']:
        print(f"\nISSUES FOUND ({len(fact_check['issues'])}):")
        print(f"{'-'*50}")
        for i, issue in enumerate(fact_check['issues'], 1):
            print(f"\nIssue {i}: {issue['type'].upper()}")
            print(f"Original:   {issue['original']}")
            print(f"Problem:    {issue['issue']}")
            print(f"Correction: {issue['correction']}")
    else:
        print(f"\n✅ No issues found!")
    print(f"{'='*50}\n")