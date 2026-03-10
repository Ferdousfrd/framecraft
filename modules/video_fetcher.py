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
    Applies smooth Ken Burns effect using scale+crop approach.
    This method is much smoother than zoompan — no jitter or shaking.
    
    Different segments get different movements for visual variety:
        1: Slow zoom in from center
        2: Pan left to right
        3: Slow zoom out
        4: Pan right to left  
        5: Slow zoom in from center

    Args:
        image_path:  Path to source image
        output_path: Path for output video clip
        duration:    Clip length in seconds
        segment_id:  Used to pick movement direction

    Returns:
        Path to generated video clip
    """

    if not os.path.exists(image_path):
        raise Exception(f"Image not found: {image_path}")

    fps = 30  # 25fps is smoother for Ken Burns than 30fps
    total_frames = duration * fps

    # Scale+crop approach — much smoother than zoompan
    # We scale image slightly larger than output, then crop a moving window
    # This eliminates the frame-by-frame recalculation jitter of zoompan
    #
    # How it works:
    #   1. Scale image to 120% of output size
    #   2. Crop a window that slowly moves across the larger image
    #   3. Result = smooth pan/zoom with zero jitter

    w = IMAGE_WIDTH
    h = IMAGE_HEIGHT
    # Scale to 120% for zoom room
    sw = int(w * 1.2)
    sh = int(h * 1.2)
    # Extra pixels available for movement
    ex = sw - w  # extra width = 216px
    ey = sh - h  # extra height = 384px

    # Simple reliable movements using scale+crop
    # No complex expressions — just linear interpolation
    movements = {
        # Zoom in: start at 120%, end at 100%
        1: f"scale=8000:-1,zoompan=z='min(zoom+0.0005,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={w}x{h}:fps={fps}",
        # Pan left to right
        2: f"scale=8000:-1,zoompan=z='1.2':x='iw/2-(iw/zoom/2)+on*0.3':y='ih/2-(ih/zoom/2)':d={total_frames}:s={w}x{h}:fps={fps}",
        # Zoom out
        3: f"scale=8000:-1,zoompan=z='max(1.2-on*0.0005,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={w}x{h}:fps={fps}",
        # Pan right to left
        4: f"scale=8000:-1,zoompan=z='1.2':x='iw/2-(iw/zoom/2)-on*0.3':y='ih/2-(ih/zoom/2)':d={total_frames}:s={w}x{h}:fps={fps}",
        # Slow zoom in
        5: f"scale=8000:-1,zoompan=z='min(zoom+0.0003,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={w}x{h}:fps={fps}",
    }

    movement = movements.get(segment_id % 5 or 5, movements[1])

    print(f"  Applying Ken Burns effect to segment {segment_id}...")

    cmd = [
        "ffmpeg",
        "-loop", "1",
        "-i", image_path,
        "-vf", movement,
        "-c:v", "libx264",
        "-preset", "slow",     # slow preset = better quality, smoother
        "-crf", "18",          # quality level — 18 = high quality
        "-t", str(duration),
        "-r", str(fps),
        "-pix_fmt", "yuv420p",
        "-y",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

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
            print(f"  ⚠️  Segment {seg_id} API failed: {e}")
            print(f"  Using placeholder for segment {seg_id}...")

            # Fallback — generate placeholder instead of crashing
            # Pipeline continues, placeholder gets replaced when API recovers
            try:
                from PIL import Image, ImageDraw
                placeholder_dir = os.path.join(images_dir)
                os.makedirs(placeholder_dir, exist_ok=True)
                img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), color=(20, 20, 35))
                draw = ImageDraw.Draw(img)
                draw.text((IMAGE_WIDTH//2, IMAGE_HEIGHT//2), f"SEGMENT {seg_id}", fill=(200,160,60), anchor="mm")
                placeholder_img = os.path.join(placeholder_dir, f"segment_{seg_id}.jpg")
                img.save(placeholder_img)

                # Apply Ken Burns to placeholder
                clip_path = os.path.join(clips_dir, f"segment_{seg_id}.mp4")
                os.makedirs(clips_dir, exist_ok=True)
                apply_ken_burns_effect(
                    image_path=placeholder_img,
                    output_path=clip_path,
                    duration=script['segments'][seg_id-1]['duration'],
                    segment_id=seg_id
                )
                video_paths.append(clip_path)
                print(f"  ✅ Placeholder used for segment {seg_id}")

            except Exception as fallback_error:
                failed_segments.append(seg_id)
                print(f"  ❌ Placeholder also failed: {fallback_error}")

    # Only crash if placeholder also failed
    if failed_segments:
        import shutil
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)
        raise Exception(
            f"Video generation failed completely for segments: {failed_segments}"
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