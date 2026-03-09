# modules/video_fetcher.py
# FrameCraft — Video Fetcher Module
#
# This module generates cinematic video clips for each script segment
# using AI image generation + Ken Burns effect (slow zoom/pan).
# This approach gives us History Channel documentary style visuals
# that actually match the story — unlike generic stock footage.
#
# Flow:
#   Visual description → Pollinations AI SDK → generates image
#        → FFmpeg Ken Burns effect → cinematic video clip
#
# Why this approach:
#   Stock footage (Pexels) can't find specific Viking/medieval scenes
#   AI generation creates EXACTLY what the script describes
#   Ken Burns effect makes static images feel cinematic and alive
#
# Upgrade path:
#   Free now:  Pollinations AI SDK (good quality, Flux model)
#   Later:     FLUX.1 Pro via Replicate (photorealistic, ~€0.003/image)
#   Dream:     Kling AI (actual video generation, ~€30/month)
#
# Error handling:
#   - Image generation retries 3 times on failure
#   - FFmpeg errors caught with clear messages
#   - Partial files cleaned up on any failure
#
# Author: Ferdous
# Part of: FrameCraft Pipeline

import os
import time
import subprocess
from datetime import datetime
from PIL import Image
import requests
from config.settings import PIXAZO_API_KEY

# Image dimensions — 9:16 vertical ratio for reels
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920

# Ken Burns effect duration per clip — matches audio segment duration
CLIP_DURATION = 12  # seconds

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries


def build_image_prompt(visual_description: str, topic: str) -> str:
    """
    Builds an optimized image generation prompt from a visual description.
    Adding style keywords dramatically improves image quality.

    Args:
        visual_description: Raw visual description from script segment
        topic:              Overall video topic for context

    Returns:
        Optimized prompt string for Pollinations AI
    """

    # Style keywords proven to produce cinematic historical images
    # These guide the AI toward documentary/epic movie aesthetics
    style_suffix = (
        "epic cinematic lighting, dramatic atmosphere, "
        "highly detailed, dark and moody, historically accurate, "
        "oil painting style, 4k quality, dramatic shadows, "
        "no text, no watermark, no modern elements"
    )

    full_prompt = f"{visual_description}, {style_suffix}"
    return full_prompt


def generate_ai_image(visual_description: str, segment_id: int, output_dir: str, topic: str) -> str:
    """
    Generates an AI image matching the visual description
    using Pixazo AI with Flux model.
    Free trial includes 100 credits — enough for testing full pipeline.

    Args:
        visual_description: Visual description from script segment
        segment_id:         Segment number used in filename
        output_dir:         Folder to save the image
        topic:              Overall topic for context in prompt

    Returns:
        File path of saved image

    Raises:
        Exception if image generation fails after all retries
    """

    if not visual_description or not visual_description.strip():
        raise ValueError(f"Segment {segment_id}: visual description is empty")

    from config.settings import PIXAZO_API_KEY
    if not PIXAZO_API_KEY:
        raise ValueError("Pixazo API key missing — check your .env file")

    # Build optimized prompt
    prompt = build_image_prompt(visual_description, topic)

    print(f"  Generating AI image for segment {segment_id}...")
    print(f"  Prompt: {visual_description[:70]}...")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Call Pixazo Flux API
            response = requests.post(
                'https://gateway.pixazo.ai/flux-2-klein-4b/v1/generateImage',
                headers={
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Ocp-Apim-Subscription-Key': PIXAZO_API_KEY
                },
                json={
                    'prompt': prompt,
                    'steps': 25,
                    'width': IMAGE_WIDTH,
                    'height': IMAGE_HEIGHT
                },
                timeout=60
            )

            if response.status_code != 200:
                raise Exception(f"Pixazo API error: {response.status_code} — {response.text[:200]}")

            # Extract image URL from response
            image_url = response.json().get('output')
            if not image_url:
                raise Exception("No image URL in response")

            # Download the generated image
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code != 200:
                raise Exception(f"Image download failed: {img_response.status_code}")

            # Save image to disk
            os.makedirs(output_dir, exist_ok=True)
            image_path = os.path.join(output_dir, f"segment_{segment_id}.jpg")

            with open(image_path, "wb") as f:
                f.write(img_response.content)

            # Verify file saved correctly
            if not os.path.exists(image_path):
                raise Exception("Image file was not saved")

            size_kb = os.path.getsize(image_path) / 1024
            if size_kb < 10:
                raise Exception(f"Image too small ({size_kb:.1f} KB)")

            print(f"  ✅ Image generated ({size_kb:.0f} KB): {image_path}")
            return image_path

        except Exception as e:
            print(f"  ⚠️  Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"  Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)

    raise Exception(
        f"Image generation failed for segment {segment_id} "
        f"after {MAX_RETRIES} attempts"
    )


def apply_ken_burns_effect(image_path: str, output_path: str, duration: int = CLIP_DURATION, segment_id: int = 1) -> str:
    """
    Applies Ken Burns effect to a static image using FFmpeg.
    Ken Burns = slow zoom in or pan across — makes images feel cinematic.
    Used in documentaries to bring still images to life.

    Different segments get different movements for visual variety:
        Odd segments:  Slow zoom in  (dramatic, intense)
        Even segments: Pan left/right (sweeping, cinematic)

    Args:
        image_path:  Path to source image
        output_path: Path for output video clip
        duration:    Clip length in seconds
        segment_id:  Used to pick movement direction

    Returns:
        Path to generated video clip

    Raises:
        Exception if FFmpeg fails
    """

    if not os.path.exists(image_path):
        raise Exception(f"Image not found: {image_path}")

    fps = 30
    total_frames = duration * fps

    # Five different Ken Burns movements for visual variety
    # zoompan filter parameters:
    #   z = zoom level expression (1.0 = no zoom, 1.5 = 50% zoomed in)
    #   x = horizontal position expression
    #   y = vertical position expression
    #   d = total frames
    #   s = output size
    movements = {
        1: f"zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={IMAGE_WIDTH}x{IMAGE_HEIGHT}:fps={fps}",
        2: f"zoompan=z='1.3':x='on/{total_frames}*iw*0.1':y='ih/2-(ih/zoom/2)':d={total_frames}:s={IMAGE_WIDTH}x{IMAGE_HEIGHT}:fps={fps}",
        3: f"zoompan=z='max(1.5-on/{total_frames}*0.5,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={IMAGE_WIDTH}x{IMAGE_HEIGHT}:fps={fps}",
        4: f"zoompan=z='1.3':x='iw*0.1+(1-on/{total_frames})*iw*0.1':y='ih/2-(ih/zoom/2)':d={total_frames}:s={IMAGE_WIDTH}x{IMAGE_HEIGHT}:fps={fps}",
        5: f"zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={IMAGE_WIDTH}x{IMAGE_HEIGHT}:fps={fps}",
    }

    # Pick movement — cycles through 1-5 for variety
    movement = movements.get(segment_id % 5 or 5, movements[1])

    print(f"  Applying Ken Burns effect to segment {segment_id}...")

    # FFmpeg command:
    # -loop 1          = loop static image as video input
    # -i image_path    = input file
    # -vf movement     = apply Ken Burns zoom/pan filter
    # -c:v libx264     = H.264 encoding — universal compatibility
    # -t duration      = output clip length in seconds
    # -pix_fmt yuv420p = pixel format compatible with all players/platforms
    # -y               = overwrite output if exists without asking
    ffmpeg_command = [
        "ffmpeg",
        "-loop", "1",
        "-i", image_path,
        "-vf", movement,
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-y",
        output_path
    ]

    # Run FFmpeg silently — only show output if it fails
    result = subprocess.run(
        ffmpeg_command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"FFmpeg failed: {result.stderr[-500:]}")

    if not os.path.exists(output_path):
        raise Exception("FFmpeg did not create output file")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  ✅ Video clip ready ({size_mb:.1f} MB): {output_path}")
    return output_path


def fetch_videos_for_script(script: dict, output_dir: str = None) -> dict:
    """
    Generates cinematic video clips for all segments in a script.
    Each clip = AI generated image + Ken Burns effect animation.

    Args:
        script:     Script dictionary from generate_script()
        output_dir: Override output folder. If None, auto-generates
                    timestamped folder

    Returns:
        Dictionary with:
            video_paths: list of video clip paths in segment order
            output_dir:  base output folder
            clips_dir:   folder containing video clips
            images_dir:  folder containing generated images
            topic:       topic string for reference

    Raises:
        Exception if any segment fails completely
    """

    if not script.get('segments'):
        raise ValueError("Script has no segments")

    # Build timestamped output folder
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_topic = script['topic'].replace(' ', '_')[:30].lower()
        base_dir = os.path.join("outputs", "video", f"{timestamp}_{clean_topic}")
    else:
        base_dir = output_dir

    # Separate subfolders for images and clips — keeps things organised
    images_dir = os.path.join(base_dir, "images")
    clips_dir = os.path.join(base_dir, "clips")

    print(f"\n🎬 Generating video clips for: {script['title']}")
    print(f"📁 Output folder: {base_dir}")
    print(f"{'-'*50}")

    video_paths = []
    failed_segments = []

    for segment in script['segments']:
        seg_id = segment['id']
        try:
            # Step 1 — Generate AI image matching visual description
            image_path = generate_ai_image(
                visual_description=segment['visual'],
                segment_id=seg_id,
                output_dir=images_dir,
                topic=script['topic']
            )

            # Step 2 — Animate image with Ken Burns effect
            clip_path = os.path.join(clips_dir, f"segment_{seg_id}.mp4")
            os.makedirs(clips_dir, exist_ok=True)

            apply_ken_burns_effect(
                image_path=image_path,
                output_path=clip_path,
                duration=segment['duration'],
                segment_id=seg_id
            )

            video_paths.append(clip_path)

        except Exception as e:
            failed_segments.append(seg_id)
            print(f"  ❌ Segment {seg_id} failed permanently: {e}")

    # If any segments failed — clean up and raise error
    # Partial sets are useless for assembly
    if failed_segments:
        print(f"\n⚠️  Cleaning up partial files...")
        import shutil
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)
        raise Exception(
            f"Video generation failed for segments: {failed_segments}. "
            f"Partial files cleaned up. Please retry."
        )

    print(f"\n✅ All {len(video_paths)} video clips generated!")
    print(f"📁 Saved to: {base_dir}")

    return {
        "video_paths": video_paths,
        "output_dir": base_dir,
        "clips_dir": clips_dir,
        "images_dir": images_dir,
        "topic": script['topic']
    }


def cleanup_video(output_dir: str) -> None:
    """
    Deletes all video segment files after final reel is assembled.
    Keeps outputs folder clean — only final reels are kept long term.

    Args:
        output_dir: The video folder to delete
    """
    if not os.path.exists(output_dir):
        print(f"⚠️  Folder not found, skipping cleanup: {output_dir}")
        return
    try:
        import shutil
        shutil.rmtree(output_dir)
        print(f"🧹 Video segments cleaned up: {output_dir}")
    except Exception as e:
        print(f"⚠️  Could not clean up video folder: {e}")


def print_video_summary(result: dict) -> None:
    """
    Prints a summary of all generated video clips.

    Args:
        result: Dictionary returned by fetch_videos_for_script()
    """
    video_paths = result['video_paths']

    print(f"\n{'='*50}")
    print(f"VIDEO GENERATION SUMMARY")
    print(f"Topic: {result['topic']}")
    print(f"{'='*50}")

    total_size = 0
    for i, path in enumerate(video_paths, 1):
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            total_size += size_mb
            print(f"Segment {i}: {os.path.basename(path)} ({size_mb:.1f} MB)")
        else:
            print(f"Segment {i}: ❌ NOT FOUND — {path}")

    print(f"{'-'*50}")
    print(f"Total size: {total_size:.1f} MB")
    print(f"🎬 Clips:  {result['clips_dir']}")
    print(f"🖼️  Images: {result['images_dir']}")
    print(f"{'='*50}\n")