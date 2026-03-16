# test_script.py
# FrameCraft — Pipeline Test
# Tests: script generation → fact check → voice generation

import json
import os
from modules.script_generator import generate_script, print_script
from modules.fact_checker import check_facts, print_fact_check
from modules.voice_generator import generate_voice_for_script, print_audio_summary
from modules.video_fetcher import fetch_videos_for_script, print_video_summary
from modules.assembler import assemble_reel

# --- CONFIG ---
topic = os.environ.get("TOPIC", "Battle of Stamford Bridge 1066")
max_attempts = 3
best_script = None
best_fact_check = None
best_score = 0
previous_issues = None
approved_script = None

print(f"\n🎬 FrameCraft Pipeline Test")
print(f"{'='*50}")
print(f"Topic: {topic}")
print(f"{'='*50}\n")

# STEP 1 + 2 — Generate and fact check script
for attempt in range(1, max_attempts + 1):
    print(f"\n⚔️  ATTEMPT {attempt} of {max_attempts}")
    print(f"{'-'*50}")

    print(f"Generating script{'  (fix mode)' if previous_issues else ''}...")
    script = generate_script(topic, issues=previous_issues)
    print_script(script)

    # Fact checking temporarily disabled — saves Groq tokens
    print(f"✅ Script auto-approved (fact check disabled)")
    approved_script = script
    break


# STEP 3 — Generate voice if script was approved
if approved_script:
    print(f"\n🎙️  STEP 3 — Voice Generation")
    print(f"{'-'*50}")
    audio_result = generate_voice_for_script(approved_script)
    print_audio_summary(audio_result)

# STEP 4 — Fetch video clips
    print(f"\n🎬  STEP 4 — Video Fetching")
    print(f"{'-'*50}")
    video_result = fetch_videos_for_script(approved_script)
    print_video_summary(video_result)
else:
    print(f"\n⚠️  Skipping — no approved script.")




# STEP 5 — Assemble final reel
# Pass audio paths so Whisper transcribes each segment for captions
if audio_result:
    approved_script['audio_paths'] = audio_result['audio_paths']

if approved_script:
    print(f"\n🎬  STEP 5 — Assembling Final Reel")
    print(f"{'-'*50}")
    final_reel = assemble_reel(
        script=approved_script,
        audio_result=audio_result,
        video_result=video_result
    )
    print(f"\n🔥 YOUR FIRST IRONNORTH REEL IS READY!")
    print(f"📁 {final_reel}")