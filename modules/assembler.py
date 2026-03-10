# modules/assembler.py
# FrameCraft — Video Assembly Module
#
# This is the final module in the pipeline. It takes all generated
# audio and video segments and assembles them into one complete reel.
#
# Flow:
#   Audio segments + Video clips
#       → Merge each clip with its audio (perfect sync)
#       → Concatenate all merged clips into one video
#       → Burn captions onto video (Pillow PNG overlay approach)
#       → Add background music (low volume)
#       → Output: final_reel.mp4 ready to upload
#
# FFmpeg is used for all video operations — it's free, fast and
# industry standard. Every major video platform uses FFmpeg internally.
#
# Caption approach:
#   We use Pillow to generate PNG caption images per segment,
#   then overlay them via FFmpeg. This gives full control over
#   text wrapping, padding, and multi-line layout — much more
#   reliable than FFmpeg's drawtext filter for complex text.
#
# Error handling:
#   - Each step validated before proceeding to next
#   - Temp files cleaned up on failure
#   - Clear error messages for each possible failure point
#
# Author: Ferdous
# Part of: FrameCraft Pipeline

import os
import json
import subprocess
import textwrap
import shutil
from datetime import datetime
from mutagen.mp3 import MP3
from PIL import Image, ImageDraw, ImageFont

# Video dimensions — must match video_fetcher.py settings
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920

# Caption styling
CAPTION_FONT_SIZE = 46
CAPTION_PADDING_SIDE = 60       # px from left/right screen edge
CAPTION_PADDING_BOTTOM = 140    # px from bottom screen edge
CAPTION_BOX_PADDING = 24        # px inside caption box around text
CAPTION_LINE_SPACING = 14       # px between lines
CAPTION_CHARS_PER_LINE = 32     # characters per line before wrapping


def get_audio_duration(audio_path: str) -> float:
    """
    Gets the exact duration of an MP3 file in seconds.
    We use this to trim video clips to exactly match audio length
    so narration and visuals are perfectly synced.

    Args:
        audio_path: Path to MP3 file

    Returns:
        Duration in seconds as float e.g. 11.43
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    audio = MP3(audio_path)
    return audio.info.length


def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Merges a video clip with its audio file.
    Video is padded with frozen last frame if audio is longer than clip.
    This prevents audio getting cut off mid-sentence.

    Args:
        video_path:  Path to video clip (.mp4)
        audio_path:  Path to audio segment (.mp3)
        output_path: Path for merged output (.mp4)

    Returns:
        Path to merged video file
    """

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video clip not found: {video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    duration = get_audio_duration(audio_path)
    print(f"    Audio duration: {duration:.2f}s")

    # tpad=stop_mode=clone freezes the last frame if audio is longer than video
    # This way narration always finishes before next segment starts
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex",
        "[0:v]tpad=stop_mode=clone:stop_duration=5[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-y",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg merge failed: {result.stderr[-300:]}")

    print(f"    ✅ Merged: {os.path.basename(output_path)}")
    return output_path


def concatenate_clips(clip_paths: list, output_path: str) -> str:
    """
    Concatenates multiple video clips into one continuous video.
    Uses FFmpeg concat demuxer — lossless, no re-encoding needed.

    Args:
        clip_paths:  List of merged clip paths in order
        output_path: Path for final concatenated video

    Returns:
        Path to concatenated video
    """

    if not clip_paths:
        raise ValueError("No clips to concatenate")

    concat_list_path = output_path.replace(".mp4", "_concat_list.txt")

    with open(concat_list_path, "w") as f:
        for clip_path in clip_paths:
            abs_path = os.path.abspath(clip_path)
            f.write(f"file '{abs_path}'\n")

    print(f"  Concatenating {len(clip_paths)} clips...")

    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        "-y",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(concat_list_path):
        os.remove(concat_list_path)

    if result.returncode != 0:
        raise Exception(f"FFmpeg concat failed: {result.stderr[-300:]}")

    duration = get_video_duration(output_path)
    print(f"  ✅ Concatenated video: {duration:.1f}s total")
    return output_path


def get_video_duration(video_path: str) -> float:
    """
    Gets the duration of a video file in seconds using FFprobe.

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds as float
    """

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        video_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFprobe failed: {result.stderr}")

    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def load_font(size: int):
    """
    Loads best available bold font. Falls back gracefully.

    Args:
        size: Font size in pixels

    Returns:
        PIL ImageFont object
    """
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    print("  ⚠️  No system font found — using default. Install fonts-dejavu for best results.")
    return ImageFont.load_default()


def generate_caption_image(text: str, seg_id: int, output_path: str) -> str:
    """
    Generates a transparent PNG caption image for one segment.
    Uses Pillow for full control over layout, wrapping and styling.

    Caption box features:
    - Centered horizontally on screen
    - Positioned in lower third with padding from bottom edge
    - Semi-transparent dark background for readability
    - White text with drop shadow
    - Proper word wrapping — no text cut off

    Args:
        text:        Narration text for this segment
        seg_id:      Segment number (for filename)
        output_path: Where to save the PNG

    Returns:
        Path to saved caption PNG
    """

    font = load_font(CAPTION_FONT_SIZE)
    line_height = CAPTION_FONT_SIZE + CAPTION_LINE_SPACING

    # Wrap text into lines
    wrapped_lines = textwrap.wrap(text, width=CAPTION_CHARS_PER_LINE)
    if not wrapped_lines:
        wrapped_lines = [""]

    # Calculate caption box size
    # Use a dummy image to measure text width accurately
    dummy = Image.new("RGBA", (10, 10))
    dummy_draw = ImageDraw.Draw(dummy)

    max_line_width = 0
    for line in wrapped_lines:
        bbox = dummy_draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        if line_w > max_line_width:
            max_line_width = line_w

    total_text_height = len(wrapped_lines) * line_height
    box_w = max_line_width + (CAPTION_BOX_PADDING * 2)
    box_h = total_text_height + (CAPTION_BOX_PADDING * 2)

    # Create full-frame transparent image
    img = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Position box: centered horizontally, near bottom
    box_x = (IMAGE_WIDTH - box_w) // 2
    box_y = IMAGE_HEIGHT - box_h - CAPTION_PADDING_BOTTOM

    # Draw rounded semi-transparent background box
    draw.rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        fill=(0, 0, 0, 185)  # black at ~72% opacity
    )

    # Draw each line centered in box
    for i, line in enumerate(wrapped_lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        text_x = (IMAGE_WIDTH - line_w) // 2
        text_y = box_y + CAPTION_BOX_PADDING + (i * line_height)

        # Drop shadow for readability
        draw.text((text_x + 2, text_y + 2), line, font=font, fill=(0, 0, 0, 220))
        # White text on top
        draw.text((text_x, text_y), line, font=font, fill=(255, 255, 255, 255))

    img.save(output_path, "PNG")
    return output_path


def burn_captions(video_path: str, script: dict, output_path: str) -> str:
    """
    Burns karaoke-style captions onto video using Whisper word timestamps.
    Shows 3-4 words at a time, perfectly synced to speech.

    Flow:
        For each segment audio:
            1. Whisper transcribes with word-level timestamps
            2. Group words into short phrases (3-4 words)
            3. Generate PNG caption image per phrase
            4. Overlay each PNG during its exact time window

    Args:
        video_path:  Path to concatenated video
        script:      Script dictionary with segments and narration
        output_path: Path for captioned output video

    Returns:
        Path to captioned video
    """

    print(f"  Transcribing audio for word-level captions...")

    import whisper
    model = whisper.load_model("base")

    temp_dir = output_path.replace(".mp4", "_caption_temp")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        all_captions = []  # list of {path, start, end} for every phrase
        time_offset = 0.0  # running time offset as segments concatenate

        audio_paths = script.get('audio_paths', [])

        for seg_idx, segment in enumerate(script['segments']):
            audio_path = audio_paths[seg_idx] if seg_idx < len(audio_paths) else None

            if not audio_path or not os.path.exists(audio_path):
                # No audio path — fall back to evenly spaced words
                print(f"  ⚠️  No audio for segment {seg_idx+1}, using timed fallback")
                seg_duration = float(segment['duration'])
                text = segment['narration']
                words = text.split()
                words_per_phrase = 4
                phrases = [words[i:i+words_per_phrase] for i in range(0, len(words), words_per_phrase)]
                phrase_duration = seg_duration / len(phrases) if phrases else seg_duration

                for p_idx, phrase_words in enumerate(phrases):
                    phrase_text = ' '.join(phrase_words)
                    start = time_offset + (p_idx * phrase_duration)
                    end = start + phrase_duration
                    cap_path = os.path.join(temp_dir, f"cap_{seg_idx}_{p_idx}.png")
                    generate_caption_image(phrase_text, p_idx, cap_path)
                    all_captions.append({"path": cap_path, "start": start, "end": end})

                time_offset += seg_duration
                continue

            # Transcribe with Whisper
            print(f"  Transcribing segment {seg_idx+1}...")
            result = model.transcribe(audio_path, word_timestamps=True)

            # Collect all words with timestamps
            words = []
            for seg in result['segments']:
                for word in seg['words']:
                    words.append({
                        "word": word['word'].strip(),
                        "start": word['start'],
                        "end": word['end']
                    })

            if not words:
                time_offset += float(segment['duration'])
                continue

            # Group into phrases of 4 words
            WORDS_PER_PHRASE = 4
            for i in range(0, len(words), WORDS_PER_PHRASE):
                phrase_words = words[i:i + WORDS_PER_PHRASE]
                phrase_text = ' '.join(w['word'] for w in phrase_words)
                start = time_offset + phrase_words[0]['start']
                end = time_offset + phrase_words[-1]['end']

                cap_path = os.path.join(temp_dir, f"cap_{seg_idx}_{i}.png")
                generate_caption_image(phrase_text, i, cap_path)
                all_captions.append({"path": cap_path, "start": start, "end": end})

            time_offset += float(segment['duration'])

        print(f"  Generated {len(all_captions)} caption phrases")
        print(f"  Overlaying captions onto video...")

        # Build FFmpeg overlay filter chain
        inputs = ["-i", video_path]
        for cap in all_captions:
            inputs += ["-i", cap["path"]]

        filter_parts = []
        prev = "[0:v]"

        for i, cap in enumerate(all_captions):
            input_ref = f"[{i + 1}:v]"
            out_ref = f"[v{i}]" if i < len(all_captions) - 1 else "[vfinal]"
            start = cap["start"]
            end = cap["end"]
            filter_parts.append(
                f"{prev}{input_ref}overlay=0:0:enable='between(t,{start:.2f},{end:.2f})'{out_ref}"
            )
            prev = out_ref

        filter_complex = ";".join(filter_parts)

        cmd = (
            ["ffmpeg"]
            + inputs
            + [
                "-filter_complex", filter_complex,
                "-map", "[vfinal]",
                "-map", "0:a",
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "copy",
                "-y",
                output_path
            ]
        )

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Caption overlay failed: {result.stderr[-500:]}")

        print(f"  ✅ Captions burned successfully")
        return output_path

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def add_background_music(video_path: str, output_path: str, script: dict = None, music_volume: float = 0.04) -> str:
    """
    Adds background music to the video.
    Picks music based on topic mood — battle, ominous, or intense.
    Loops the track if shorter than video, trims if longer.

    Args:
        video_path:    Path to video
        output_path:   Path for output
        script:        Script dict — used to pick mood from topic/title
        music_volume:  Volume 0.0-1.0 (default 0.15 = 15%)

    Returns:
        Path to final video with music
    """

    print(f"  Adding background music...")

    # Pick music file based on topic keywords
    MUSIC_DIR = "assets/music"
    

# ****************** Hardcoded for now — dark_ominous fits Viking theme perfectly
    # In Phase 2: dynamic mood selection per segment
    music_file = os.path.join(MUSIC_DIR, "dark_ominous.mp3")
    print(f"  🎵 Using: dark_ominous.mp3")

    
    if not os.path.exists(music_file):
        print(f"  ⚠️  Music file not found: {music_file} — skipping music")
        shutil.copy(video_path, output_path)
        return output_path

    duration = get_video_duration(video_path)

    # FFmpeg command:
    # -stream_loop -1  = loop music infinitely
    # -t duration      = trim to video length
    # amix             = mix narration + music together
    # duration=first   = stop when video ends
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-stream_loop", "-1",
        "-i", music_file,
        "-filter_complex",
        f"[1:a]volume={music_volume},atrim=0:{duration}[music];[0:a][music]amix=inputs=2:duration=first[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-y",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️  Music failed — saving without music: {result.stderr[-150:]}")
        shutil.copy(video_path, output_path)
    else:
        print(f"  ✅ Background music added")

    return output_path


def assemble_reel(script: dict, audio_result: dict, video_result: dict, output_dir: str = None) -> str:
    """
    Master assembly function — combines everything into final reel.
    This is the last step of the FrameCraft pipeline.

    Args:
        script:       Script dictionary from generate_script()
        audio_result: Dictionary from generate_voice_for_script()
        video_result: Dictionary from fetch_videos_for_script()
        output_dir:   Override output folder. If None, auto-generates

    Returns:
        Path to final assembled reel ready for upload
    """

    print(f"\n🎬 ASSEMBLING FINAL REEL")
    print(f"{'='*50}")
    print(f"Topic: {script['topic']}")
    print(f"Title: {script['title']}")

    audio_paths = audio_result['audio_paths']
    video_paths = video_result['video_paths']

    if len(audio_paths) != len(video_paths):
        raise ValueError(
            f"Mismatch: {len(audio_paths)} audio files but {len(video_paths)} video clips"
        )

    if len(audio_paths) == 0:
        raise ValueError("No audio or video files to assemble")

    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_topic = script['topic'].replace(' ', '_')[:30].lower()
        output_dir = os.path.join("outputs", "reels", f"{timestamp}_{clean_topic}")

    os.makedirs(output_dir, exist_ok=True)

    temp_dir = os.path.join(output_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # STEP 1 — Merge each video clip with its audio
        print(f"\n📎 Step 1: Merging audio + video segments...")
        merged_clips = []

        for i, (video_path, audio_path) in enumerate(zip(video_paths, audio_paths), 1):
            print(f"  Segment {i}:")
            merged_path = os.path.join(temp_dir, f"merged_{i}.mp4")
            merge_audio_video(video_path, audio_path, merged_path)
            merged_clips.append(merged_path)

        # STEP 2 — Concatenate all merged clips
        print(f"\n🔗 Step 2: Concatenating all segments...")
        concat_path = os.path.join(temp_dir, "concatenated.mp4")
        concatenate_clips(merged_clips, concat_path)

        # STEP 3 — Skip caption burning
        # Captions handled by TikTok/Instagram/YouTube auto-caption
        # This gives better sync, native look, and saves processing time
        print(f"\n💬 Step 3: Skipping captions — platform auto-captions will be used")

        # STEP 4 — Add background music
        print(f"\n🎵 Step 4: Adding background music...")
        music_path = os.path.join(temp_dir, "with_music.mp4")
        add_background_music(concat_path, music_path, script=script)

        # STEP 5 — Save final reel
        print(f"\n📦 Step 5: Saving final reel...")
        clean_title = script['title'].replace(' ', '_')[:30]
        final_path = os.path.join(output_dir, f"IronNorth_{clean_title}.mp4")

        shutil.copy(music_path, final_path)

        final_size_mb = os.path.getsize(final_path) / (1024 * 1024)
        final_duration = get_video_duration(final_path)

        print(f"\n{'='*50}")
        print(f"✅ REEL ASSEMBLED SUCCESSFULLY!")
        print(f"{'='*50}")
        print(f"📁 File:     {final_path}")
        print(f"⏱️  Duration: {final_duration:.1f} seconds")
        print(f"📦 Size:     {final_size_mb:.1f} MB")
        print(f"{'='*50}")

        return final_path

    except Exception as e:
        print(f"\n❌ Assembly failed: {e}")
        raise

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 Temp files cleaned up")