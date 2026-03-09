# test_script.py
# FrameCraft — Pipeline Test Script
#
# Tests the full script generation + fact checking pipeline.
# Uses a feedback loop — if script fails fact check, issues are fed
# back to the AI so it can fix them specifically rather than
# generating blindly again.
#
# Flow:
#   Attempt 1 → Fresh generation
#   Attempt 2 → Regenerate with issues fed back (fix mode)
#   Attempt 3 → Final attempt with all issues fed back
#   All fail  → Save best attempt to outputs/ for manual review

import json
import os
from modules.script_generator import generate_script, print_script
from modules.fact_checker import check_facts, print_fact_check

# --- CONFIG ---
topic = "Viking raid on Paris 845 AD"
max_attempts = 3

# Track best attempt in case all fail
# We save the highest scoring script even if none pass
best_script = None
best_fact_check = None
best_score = 0

print(f"\n🎬 FrameCraft Script Pipeline")
print(f"{'='*50}")
print(f"Topic: {topic}")
print(f"Max attempts: {max_attempts}")
print(f"{'='*50}\n")

# Store issues from previous attempt to feed back into next generation
previous_issues = None

for attempt in range(1, max_attempts + 1):
    print(f"\n⚔️  ATTEMPT {attempt} of {max_attempts}")
    print(f"{'-'*50}")

    # Generate script — pass previous issues if we have them
    # On attempt 1: issues=None → fresh generation
    # On attempt 2+: issues=previous_issues → fix mode
    print(f"Generating script{'  (fix mode)' if previous_issues else ''}...")
    script = generate_script(topic, issues=previous_issues)
    print_script(script)

    # Fact check the generated script
    print(f"Fact checking...")
    fact_check = check_facts(script)
    print_fact_check(fact_check)

    # Track the best scoring script across all attempts
    # So we never lose a good script even if it doesn't pass
    if fact_check['accuracy_score'] > best_score:
        best_score = fact_check['accuracy_score']
        best_script = script
        best_fact_check = fact_check

    # Check if this attempt passed
    if fact_check['is_approved']:
        print(f"\n✅ Script approved on attempt {attempt}!")
        print(f"Accuracy: {fact_check['accuracy_score']}/10")
        print(f"Ready for voice generation! 🎙️")
        break
    else:
        # Save issues to feed into next attempt
        previous_issues = fact_check['issues']
        
        if attempt < max_attempts:
            issue_count = len(fact_check['issues'])
            print(f"\n❌ Failed — {issue_count} issues found. Fixing and retrying...")
        else:
            # All attempts exhausted — save best script for manual review
            print(f"\n❌ All {max_attempts} attempts failed.")
            print(f"Best score achieved: {best_score}/10")
            print(f"Saving best attempt for manual review...")

            # Create outputs directory if it doesn't exist
            os.makedirs("outputs", exist_ok=True)

            # Save best script to file for manual review
            review_file = f"outputs/review_{topic[:30].replace(' ', '_')}.json"
            with open(review_file, "w") as f:
                json.dump({
                    "topic": topic,
                    "best_score": best_score,
                    "script": best_script,
                    "fact_check": best_fact_check
                }, f, indent=2)
            
            print(f"💾 Saved to: {review_file}")
            print(f"Review manually and decide to approve or skip this topic.")