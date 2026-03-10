#!/bin/bash
# batch_generate.sh
# FrameCraft — Batch Reel Generator
# Runs test_script.py for each topic and logs results
# Safe to interrupt — completed reels are already saved

# Topics in order — Ragnar Lothbrok series
TOPICS=(
    "Ragnar Lothbrok Part 1 of 5: Who was Ragnar Lothbrok and why is he the most legendary Viking who ever lived. Hook the audience to follow the full story series."
    "Ragnar Lothbrok Part 2 of 5: His childhood origins mysterious birth early skills and the traits that made him destined for greatness. Reference Part 1 briefly."
    "Ragnar Lothbrok Part 3 of 5: His first raid on England the battle that launched his legend and made his name feared across Europe. Reference the series so far."
    "Ragnar Lothbrok Part 4 of 5: The legendary siege of Paris 845 AD his greatest triumph that shocked the entire world. Reference the series so far."
    "Ragnar Lothbrok Part 5 of 5: His capture death in the snake pit and the legacy he left behind. Epic conclusion to the full series."
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
        sleep 30
    fi
done

echo "" | tee -a $LOG_FILE
echo "================================================" | tee -a $LOG_FILE
echo "🏁 BATCH COMPLETE" | tee -a $LOG_FILE
echo "✅ Success: $SUCCESS" | tee -a $LOG_FILE
echo "❌ Failed:  $FAILED" | tee -a $LOG_FILE
echo "📁 Log saved: $LOG_FILE" | tee -a $LOG_FILE
echo "📁 Reels in: outputs/reels/" | tee -a $LOG_FILE
