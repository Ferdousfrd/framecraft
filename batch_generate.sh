#!/bin/bash
# batch_generate.sh
# FrameCraft — Batch Reel Generator
# Runs test_script.py for each topic and logs results
# Safe to interrupt — completed reels are already saved

# Topics in order — Ragnar Lothbrok series
TOPICS=(
    "Sons of Ragnar Part 1 of 10: Bjorn Ironside - the son of Ragnar Lothbrok who became unconquerable, sailed the Mediterranean and made Rome tremble"
    "Sons of Ragnar Part 2 of 10: Ivar the Boneless - the most feared and cunning of Ragnar's sons who conquered England without being able to walk"
    "Sons of Ragnar Part 3 of 10: Rollo - the son who betrayed the Vikings, became a French duke and whose bloodline became the British royal family"
    "Sons of Ragnar Part 4 of 10: Sigurd Snake-in-the-Eye - the son born with a mysterious mark in his eye and his legendary life"
    "Sons of Ragnar Part 5 of 10: Ubbe - the peacemaker son of Ragnar who sailed to unknown lands and built a new Viking world"
    "Sons of Ragnar Part 6 of 10: The Great Heathen Army - when all of Ragnar's sons united to avenge their father and invaded England with 10000 warriors"
    "Sons of Ragnar Part 7 of 10: Ivar the Boneless conquers York - how a man who could not walk became the king of England"
    "Sons of Ragnar Part 8 of 10: Bjorn Ironside raids the Mediterranean - the most ambitious Viking expedition ever attempted"
    "Sons of Ragnar Part 9 of 10: The death of Ivar the Boneless - the end of the most feared Viking who ever lived"
    "Sons of Ragnar Part 10 of 10: The legacy of Ragnar's sons - how five brothers changed the entire map of Europe forever"
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
