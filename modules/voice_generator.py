# modules/voice_generator.py
# FrameCraft — Voice Generation Module
#
# This module converts script narration text into audio files
# using the ElevenLabs API. It processes each segment separately
# so audio duration can be measured and synced perfectly with video.
#
# Flow:
#   Script segments → ElevenLabs API → MP3 files (one per segment)
#   Each MP3 is saved to outputs/audio/{timestamp}_{topic}/ folder
#   Once final video is assembled, audio segments are auto-cleaned up
#
# Error handling:
#   - API failures retry 3 times before raising exception
#   - Empty audio responses are caught and retried
#   - File write errors are caught with clear messages
#   - Partial failures clean up incomplete files
#
# Author: Ferdous
# Part of: FrameCraft Pipeline

import os
import time
import requests
from datetime import datetime
from config.settings import ELEVENLABS_API_KEY

# ElevenLabs API endpoint for text to speech
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Harry - Fierce Warrior — perfect for Viking history narration
# To change voice, replace this ID with any voice_id from ElevenLabs
DEFAULT_VOICE_ID = "SOYHLrjzK2X1ezoPC6cr"

# How many times to retry a failed API call before giving up
MAX_RETRIES = 3

# Seconds to wait between retries — gives API time to recover
RETRY_DELAY = 2


def generate_audio(text: str, segment_id: int, output_dir: str, voice_id: str = DEFAULT_VOICE_ID) -> str:
    """
    Converts a single text segment into an MP3 audio file.
    Retries up to MAX_RETRIES times on failure.
    
    Args:
        text:       The narration text to convert to speech
        segment_id: The segment number (1-5) used in filename
        output_dir: Folder where the MP3 file will be saved
        voice_id:   ElevenLabs voice ID to use for narration
    
    Returns:
        The full file path of the saved MP3 file
    
    Raises:
        Exception if all retries fail or audio file is empty
    """

    # Validate inputs before making API call
    # Catches bugs early rather than letting them cause weird errors later
    if not text or not text.strip():
        raise ValueError(f"Segment {segment_id}: narration text is empty")
    
    if not ELEVENLABS_API_KEY:
        raise ValueError("ElevenLabs API key is missing — check your .env file")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    # Retry loop — tries up to MAX_RETRIES times before giving up
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  Generating audio for segment {segment_id} (attempt {attempt}/{MAX_RETRIES})...")
            
            response = requests.post(
                f"{ELEVENLABS_URL}/{voice_id}",
                headers=headers,
                json=body,
                timeout=30  # timeout after 30 seconds — prevents hanging forever
            )

            # Check HTTP status — 200 means success
            if response.status_code != 200:
                raise Exception(
                    f"API returned status {response.status_code}: {response.text}"
                )

            # Check we actually got audio data back — not an empty response
            if len(response.content) < 1000:
                raise Exception(
                    f"Audio response too small ({len(response.content)} bytes) — likely empty audio"
                )

            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Save audio to MP3 file
            output_path = os.path.join(output_dir, f"segment_{segment_id}.mp3")
            with open(output_path, "wb") as f:
                f.write(response.content)

            # Verify file was actually written correctly
            if not os.path.exists(output_path):
                raise Exception(f"File was not saved correctly: {output_path}")

            file_size_kb = os.path.getsize(output_path) / 1024
            print(f"  ✅ Segment {segment_id} saved ({file_size_kb:.1f} KB): {output_path}")
            return output_path

        except Exception as e:
            last_error = e
            print(f"  ⚠️  Attempt {attempt} failed: {e}")
            
            if attempt < MAX_RETRIES:
                print(f"  Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)

    # All retries exhausted — raise the last error we saw
    raise Exception(
        f"Segment {segment_id} failed after {MAX_RETRIES} attempts. "
        f"Last error: {last_error}"
    )

def generate_segment_audio_edge_tts(text: str, segment_id: int, output_dir: str) -> str:
    """
    Fallback TTS using Microsoft edge-tts.
    Free, no API key, good quality neural voice.
    Used automatically when ElevenLabs quota is insufficient.

    Voice: William (Australian male) — deep, authoritative,
    perfect for dramatic history narration.

    Args:
        text:       Narration text to convert
        segment_id: Segment number for filename
        output_dir: Folder to save audio

    Returns:
        Path to saved MP3 file
    """
    import asyncio
    import edge_tts

    EDGE_VOICE = "en-AU-WilliamNeural"

    print(f"  edge-tts generating segment {segment_id}...")

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"segment_{segment_id}.mp3")

    async def generate():
        tts = edge_tts.Communicate(text, voice=EDGE_VOICE)
        await tts.save(output_path)

    asyncio.run(generate())

    if not os.path.exists(output_path):
        raise Exception(f"edge-tts failed to save segment {segment_id}")

    size_kb = os.path.getsize(output_path) / 1024
    print(f"  ✅ Segment {segment_id} saved ({size_kb:.0f} KB): {output_path}")
    return output_path

def generate_voice_for_script(script: dict, output_dir: str = None) -> dict:
    """
    Generates audio files for all segments in a script.
    Uses timestamped folders so each run is saved separately.
    
    Args:
        script:     The script dictionary from generate_script()
        output_dir: Override folder path. If None, auto-generates
                    timestamped folder like: outputs/audio/20240115_143022_viking_raid
    
    Returns:
        Dictionary with:
            audio_paths: list of MP3 file paths in segment order
            output_dir:  the folder where files were saved
            topic:       the topic string for reference
    
    Raises:
        Exception if any segment fails after all retries
    """

    # Validate script structure before starting
    if not script.get('segments'):
        raise ValueError("Script has no segments — cannot generate audio")
    
    if len(script['segments']) == 0:
        raise ValueError("Script segments list is empty")

    # Check ElevenLabs credits before starting
    # Count total characters needed for all segments
    total_chars = sum(len(seg['narration']) for seg in script['segments'])
    print(f"\n  Checking TTS provider...")
    print(f"  Total characters needed: {total_chars}")

    use_elevenlabs = False
    try:
        sub = requests.get(
            'https://api.elevenlabs.io/v1/user/subscription',
            headers={'xi-api-key': ELEVENLABS_API_KEY}
        ).json()
        remaining = sub['character_limit'] - sub['character_count']
        print(f"  ElevenLabs credits remaining: {remaining}")

        if remaining >= total_chars:
            print(f"  ✅ Enough credits — using ElevenLabs (Harry voice)")
            use_elevenlabs = True
        else:
            print(f"  ⚠️  Not enough credits ({remaining} remaining, {total_chars} needed)")
            print(f"  ✅ Using edge-tts (William voice) for all segments")
    except Exception as e:
        print(f"  ⚠️  Could not check credits: {e} — defaulting to edge-tts")

    # Build timestamped output folder if not provided
    # Format: outputs/audio/20240115_143022_viking_raid_on_paris
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_topic = script['topic'].replace(' ', '_')[:30].lower()
        output_dir = os.path.join("outputs", "audio", f"{timestamp}_{clean_topic}")

    print(f"\n🎙️  Generating voice for: {script['title']}")
    print(f"📁 Output folder: {output_dir}")
    print(f"{'-'*50}")

    audio_paths = []
    failed_segments = []

    for segment in script['segments']:
        try:
            if use_elevenlabs:
                path = generate_audio(
                    text=segment['narration'],
                    segment_id=segment['id'],
                    output_dir=output_dir
                )
            else:
                path = generate_segment_audio_edge_tts(
                    text=segment['narration'],
                    segment_id=segment['id'],
                    output_dir=output_dir
                )
            audio_paths.append(path)

        except Exception as e:
            # Track which segments failed
            failed_segments.append(segment['id'])
            print(f"  ❌ Segment {segment['id']} failed permanently: {e}")

    # If any segments failed, clean up partial files and raise error
    # Partial audio sets are useless — better to fail clean than produce broken content
    if failed_segments:
        print(f"\n⚠️  Cleaning up partial audio files...")
        for path in audio_paths:
            if os.path.exists(path):
                os.remove(path)
        raise Exception(
            f"Voice generation failed for segments: {failed_segments}. "
            f"Partial files cleaned up. Please retry."
        )

    print(f"\n✅ All {len(audio_paths)} audio segments generated!")
    print(f"📁 Saved to: {output_dir}")

    # Return dict with all info assembler will need
    return {
        "audio_paths": audio_paths,
        "output_dir": output_dir,
        "topic": script['topic']
    }


def cleanup_audio(output_dir: str) -> None:
    """
    Deletes all audio segment files after final video is assembled.
    Keeps outputs folder clean — only final reels are kept long term.
    
    Args:
        output_dir: The audio folder to delete
    """
    if not os.path.exists(output_dir):
        print(f"⚠️  Audio folder not found, skipping cleanup: {output_dir}")
        return

    try:
        import shutil
        shutil.rmtree(output_dir)
        print(f"🧹 Audio segments cleaned up: {output_dir}")
    except Exception as e:
        # Cleanup failure is not critical — just warn, don't crash
        print(f"⚠️  Could not clean up audio folder: {e}")


def print_audio_summary(result: dict) -> None:
    """
    Prints a summary of all generated audio files.
    
    Args:
        result: The dictionary returned by generate_voice_for_script()
    """
    audio_paths = result['audio_paths']
    
    print(f"\n{'='*50}")
    print(f"AUDIO GENERATION SUMMARY")
    print(f"Topic: {result['topic']}")
    print(f"{'='*50}")
    
    total_size = 0
    for i, path in enumerate(audio_paths, 1):
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            total_size += size_kb
            print(f"Segment {i}: {os.path.basename(path)} ({size_kb:.1f} KB)")
        else:
            print(f"Segment {i}: ❌ FILE NOT FOUND — {path}")
    
    print(f"{'-'*50}")
    print(f"Total audio size: {total_size:.1f} KB")
    print(f"📁 Location: {result['output_dir']}")
    print(f"{'='*50}\n")