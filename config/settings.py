# config/settings.py
# Loads all API keys and settings for FrameCraft

import os
from dotenv import load_dotenv

# Load keys from our .env file
load_dotenv()

# API Keys fetching by name with os.getenv() method
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PIXAZO_API_KEY = os.getenv("PIXAZO_API_KEY")

# Video Settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # vertical format for reels
VIDEO_DURATION = 60  # seconds

# Content Settings
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ["en", "bn", "fi"]
