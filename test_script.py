# test_script.py
# FrameCraft — Pipeline Test
# Tests: script generation → fact check → voice generation

import json
import os
from modules.script_generator import generate_script, print_script
from modules.fact_checker import check_facts, print_fact_check
from modules.voice_generator import generate_voice_for_script, print_audio_summary
from modules.video_fetcher import fetch_videos_for_script, print_video_summary

# --- CONFIG ---
topic = "Viking raid on Paris 845 AD"
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

    print(f"Fact checking...")
    fact_check = check_facts(script)
    print_fact_check(fact_check)

    if fact_check['accuracy_score'] > best_score:
        best_score = fact_check['accuracy_score']
        best_script = script
        best_fact_check = fact_check

    if fact_check['is_approved']:
        print(f"\n✅ Script approved on attempt {attempt}!")
        approved_script = script
        break
    else:
        previous_issues = fact_check['issues']
        if attempt < max_attempts:
            print(f"\n❌ Failed — retrying with fixes...")
        else:
            print(f"\n❌ All attempts failed. Saving best for review...")
            os.makedirs("outputs", exist_ok=True)
            review_file = f"outputs/review_{topic[:30].replace(' ', '_')}.json"
            with open(review_file, "w") as f:
                json.dump({
                    "topic": topic,
                    "best_score": best_score,
                    "script": best_script,
                    "fact_check": best_fact_check
                }, f, indent=2)
            print(f"💾 Saved to: {review_file}")


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