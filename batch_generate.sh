#!/bin/bash
# batch_generate.sh
# FrameCraft — Batch Reel Generator
# Runs test_script.py for each topic and logs results
# Safe to interrupt — completed reels are already saved

# Topics in order — Ragnar Lothbrok series
TOPICS=(
    "Freydís - Part 1 of 4: The Daughter of Erik the Red Who Refused to Live in His Shadow 
        Focus:
        - Her powerful Viking family
        - Sister of Leif Erikson
        - Growing up among explorers and warriors"
    "Freydís - Part 2 of 4: The Viking Woman Who Sailed to Vinland
        Focus:
        - The dangerous voyage to North America
        - Viking settlements in Vinland
        - Life in an unknown land"
)

LOG_FILE="outputs/batch_log_$(date +%Y%m%d_%H%M%S).txt"
mkdir -p outputs

echo "🚀 FrameCraft Batch Generator Started" | tee $LOG_FILE
echo "📅 $(date)" | tee -a $LOG_FILE
echo "🎬 Generating ${#TOPICS[@]} reels..." | tee -a $LOG_FILE
echo "================================================" | tee -a $LOG_FILE

SUCCESS=0
FAILED=0

for i in "${!TOPICS[@]}"; do
    TOPIC="${TOPICS[$i]}"
    PART=$((i + 1))
    
    echo "" | tee -a $LOG_FILE
    echo "🎬 Part $PART of ${#TOPICS[@]}: $TOPIC" | tee -a $LOG_FILE
    echo "⏰ Started: $(date)" | tee -a $LOG_FILE
    echo "------------------------------------------------" | tee -a $LOG_FILE

    # Temporarily override topic in test_script.py
    # by passing it as environment variable
    TOPIC="$TOPIC" python3 test_script.py 2>&1 | tee -a $LOG_FILE
    
    if [ $? -eq 0 ]; then
        echo "✅ Part $PART COMPLETE" | tee -a $LOG_FILE
        SUCCESS=$((SUCCESS + 1))
    else
        echo "❌ Part $PART FAILED — continuing to next" | tee -a $LOG_FILE
        FAILED=$((FAILED + 1))
    fi

    echo "⏰ Finished: $(date)" | tee -a $LOG_FILE

    # Wait 30 seconds between runs
    # Lets APIs recover and avoids rate limiting
    if [ $PART -lt ${#TOPICS[@]} ]; then
        echo "⏳ Waiting 30 seconds before next reel..." | tee -a $LOG_FILE
        sleep 180
    fi
done

echo "" | tee -a $LOG_FILE
echo "================================================" | tee -a $LOG_FILE
echo "🏁 BATCH COMPLETE" | tee -a $LOG_FILE
echo "✅ Success: $SUCCESS" | tee -a $LOG_FILE
echo "❌ Failed:  $FAILED" | tee -a $LOG_FILE
echo "📁 Log saved: $LOG_FILE" | tee -a $LOG_FILE
echo "📁 Reels in: outputs/reels/" | tee -a $LOG_FILE
