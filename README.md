# FrameCraft 🎬⚔️

> An automated AI content pipeline that crafts publish-ready short-form videos
> across multiple niches and languages — deployed live through the IronNorth brand.

![Status](https://img.shields.io/badge/status-active%20development-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-private-red)

---

## 🚀 What Is FrameCraft?

FrameCraft is a fully automated content pipeline built in Python. You give it a topic —
it returns a publish-ready vertical video with narration, captions, stock footage
and background music. No human editing required.

**Live proof of concept:** The IronNorth brand across YouTube, TikTok and Instagram
is 100% powered by FrameCraft.

---

## ⚡ How It Works

```
Topic Input  →  Script  →  Fact Check  →  Voice  →  Footage  →  Assemble  →  Video
```

1. **Script Generator** — Claude AI writes a dramatic 5-segment narration script
2. **Fact Checker** — Second AI pass verifies historical accuracy
3. **Translator** — DeepL translates script to target language
4. **Voice Generator** — ElevenLabs converts narration to natural speech
5. **Video Fetcher** — Pexels API sources cinematic stock footage per segment
6. **Assembler** — FFmpeg combines everything with synced captions

---

## 🎯 Content Brands Powered By FrameCraft

| Brand               | Niche                    | Languages         | Platforms                    |
| ------------------- | ------------------------ | ----------------- | ---------------------------- |
| ⚔️ IronNorth        | Viking & Finnish History | English + Finnish | YouTube · TikTok · Instagram |
| 🐍 IronNorth Code   | Python Programming       | English + Bengali | YouTube · TikTok · Instagram |
| 📜 IronNorth Verses | Poems & Motivational     | English + Bengali | TikTok · Instagram           |

---

## 🛠️ Tech Stack

| Purpose           | Tool                                  |
| ----------------- | ------------------------------------- |
| Script Generation | Groq API (llama-3.3-70b) → Claude API |
| Voice Generation  | ElevenLabs API                        |
| Stock Footage     | Pexels API                            |
| Video Assembly    | FFmpeg + MoviePy                      |
| Translation       | DeepL API                             |
| Cloud Rendering   | Google Colab                          |
| Language          | Python 3.12                           |

---

## 📁 Project Structure

```
framecraft/
├── modules/
│   ├── script_generator.py   # AI script generation
│   ├── fact_checker.py       # AI accuracy verification
│   ├── voice_generator.py    # ElevenLabs voice synthesis
│   ├── video_fetcher.py      # Pexels stock footage
│   ├── translator.py         # DeepL translation
│   └── assembler.py          # FFmpeg video assembly
├── pipelines/
│   ├── history_pipeline.py   # Full history video pipeline
│   ├── coding_pipeline.py    # Full coding video pipeline
│   └── poem_pipeline.py      # Full poem video pipeline
├── config/
│   └── settings.py           # Global settings + API config
├── outputs/                  # Generated videos (gitignored)
├── docs/
│   ├── PROGRESS.md           # Build progress log
│   └── ROADMAP.md            # Full project roadmap
├── .env                      # API keys (gitignored)
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- FFmpeg installed
- API keys for: Groq/Claude, ElevenLabs, Pexels, DeepL

### Installation

```bash
# Clone the repo
git clone https://github.com/Ferdousfrd/framecraft.git
cd framecraft

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your API keys to .env
```

### Generate Your First Script

```bash
python3 test_script.py
```

---

## 📊 Pipeline Status

| Module              | Status         | Description                           |
| ------------------- | -------------- | ------------------------------------- |
| script_generator.py | ✅ Complete    | Generates 5-segment narration scripts |
| fact_checker.py     | 🔨 In progress | Verifies historical accuracy          |
| voice_generator.py  | ⬜ Planned     | ElevenLabs voice synthesis            |
| video_fetcher.py    | ⬜ Planned     | Pexels stock footage sourcing         |
| translator.py       | ⬜ Planned     | DeepL multi-language support          |
| assembler.py        | ⬜ Planned     | FFmpeg video assembly                 |

---

## 🔒 IP Protection

FrameCraft is proprietary software. The pipeline, prompts, and architecture
are trade secrets. Clients and subscribers receive generated content output only —
never access to the underlying system.

---

## 💰 Business Model

- **Passive content income** — ad revenue + affiliate links across IronNorth channels
- **Content service** — generating videos for clients using FrameCraft
- **SaaS subscriptions** — clients access FrameCraft through a web interface

---

## 👨‍💻 Author

**Ferdous** — Software Engineering Student, Tampere, Finland  
Building FrameCraft as a real business and portfolio project simultaneously.

> _"Every line of code is either building the product or building the portfolio."_

---

## 📈 Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full build and business roadmap.
