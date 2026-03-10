# test_assemble.py
# FrameCraft — Assembly Test Script
#
# Uses existing audio and video files to test assembly only.
# This avoids regenerating images/audio every time we tweak
# captions, music or other assembly settings.
#
# Usage:
#   python3 test_assemble.py
#
# Author: Ferdous

import os
from modules.assembler import assemble_reel



# --- USE EXISTING FILES --- 
# Point to most recent generated audio and video folders
AUDIO_DIR = "outputs/audio/20260310_002745_viking_raid_on_paris_845_ad"
VIDEO_DIR = "outputs/video/20260310_071130_viking_raid_on_paris_845_ad/smooth_clips"

# Build audio and video path lists in segment order
audio_paths = [os.path.join(AUDIO_DIR, f"segment_{i}.mp3") for i in range(1, 6)]
video_paths = [os.path.join(VIDEO_DIR, f"segment_{i}.mp4") for i in range(1, 6)]


# Verify all files exist before starting
print("🔍 Checking files...")
all_good = True
for i, (a, v) in enumerate(zip(audio_paths, video_paths), 1):
    a_ok = "✅" if os.path.exists(a) else "❌"
    v_ok = "✅" if os.path.exists(v) else "❌"
    print(f"  Segment {i}: audio {a_ok}  video {v_ok}")
    if not os.path.exists(a) or not os.path.exists(v):
        all_good = False

if not all_good:
    print("\n❌ Some files missing — check paths above")
    exit(1)

print("✅ All files found!\n")

# Hardcoded script for caption testing
# This matches the Viking Paris topic we've been generating
script = {
    "title": "Sacking the City of Light",
    "topic": "Viking raid on Paris 845 AD",
    "language": "en",
    "segments": [
        {
            "id": 1,
            "narration": "In 845 AD the Viking fleet of 120 longships sailed up the Seine River toward the heart of the Frankish kingdom striking terror into all who saw them approach.",
            "visual": "Viking longships on river",
            "duration": 12
        },
        {
            "id": 2,
            "narration": "Led by the legendary Norse chieftain Ragnar the Viking warriors were seasoned raiders who had already plundered the coasts of England and Ireland.",
            "visual": "Viking warriors marching",
            "duration": 12
        },
        {
            "id": 3,
            "narration": "The Frankish King Charles the Bald could only watch helplessly as the Vikings sacked the city of Paris burning churches and taking prisoners.",
            "visual": "Medieval city under siege",
            "duration": 12
        },
        {
            "id": 4,
            "narration": "Desperate to stop the carnage Charles agreed to pay a massive ransom of 7000 pounds of silver and gold — a sum that would shape European history.",
            "visual": "Gold and silver treasure",
            "duration": 12
        },
        {
            "id": 5,
            "narration": "The Vikings left Paris victorious and rich. This humiliating defeat planted the seeds of what would eventually become the kingdom of Normandy.",
            "visual": "Viking ships sailing away",
            "duration": 12
        }
    ]
}
# Pass audio paths so Whisper can transcribe each segment
script['audio_paths'] = audio_paths

# Build result dictionaries matching what the pipeline modules return
audio_result = {
    "audio_paths": audio_paths,
    "output_dir": AUDIO_DIR,
    "topic": script['topic']
}

video_result = {
    "video_paths": video_paths,
    "output_dir": VIDEO_DIR,
    "clips_dir": VIDEO_DIR,
    "images_dir": VIDEO_DIR,
    "topic": script['topic']
}

# Run assembly only — no API calls, instant start
print("🎬 Starting assembly with existing files...")
final_reel = assemble_reel(
    script=script,
    audio_result=audio_result,
    video_result=video_result
)

print(f"\n🔥 REEL READY!")
print(f"📁 {final_reel}")
print(f"\nOpen the file and check:")
print(f"  1. Is the shaking smooth now?")
print(f"  2. Are captions readable and properly wrapped?")
print(f"  3. Does audio sync with visuals?")