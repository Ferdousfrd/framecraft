# FrameCraft — Build Progress Log

## Project Info

- **Builder:** Rehan (Software Engineering Student, Tampere, Finland)
- **Started:** Day 1 — Account setup
- **GitHub:** github.com/YOURUSERNAME/framecraft
- **Goal:** Automated AI content pipeline for short-form videos

## Brands

- **IronNorth** — Content brand (Viking/Finnish History, Coding, Poems)
- **FrameCraft** — The system/pipeline/future SaaS

## Social Accounts Created

- YouTube: IronNorth (under review)
- TikTok: @ironnorthhq
- Instagram: @iron_north_hq

## API Keys Configured

- ✅ Anthropic (Claude) — saved, needs credits
- ✅ Groq — active, currently using as free alternative
- ✅ ElevenLabs — saved
- ✅ Pexels — saved

## Project Structureframecraft/

├── modules/
│ └── script_generator.py ✅ COMPLETE
├── pipelines/
├── outputs/
├── config/
│ └── settings.py ✅ COMPLETE
├── docs/
│ ├── PROGRESS.md
│ └── ROADMAP.md
├── .env ✅ configured
├── .gitignore ✅ configured
└── test_script.py ✅ working

## Completed Modules

### script_generator.py ✅

- Takes a topic string as input
- Calls Groq API (llama-3.3-70b model)
- Returns structured JSON with 5 segments
- Each segment has: narration, visual description, duration
- Tested successfully with "Viking raid on Paris 845 AD"
- Will switch to Claude API when credits added

## Current Status

- ✅ Day 1 COMPLETE — accounts, GitHub, API keys
- ✅ Day 2 COMPLETE — script generator working, first commit pushed

## Next Session — Day 3

- [ ] Update script prompt with accuracy/fact-check instructions
- [ ] Build fact_checker.py module
- [ ] Build voice_generator.py module (ElevenLabs)
- [ ] Test full script → voice pipeline

## Known Issues

- YouTube channel still under review
- Anthropic API needs credits ($5 minimum)
- Only 1 TikTok account (need second Gmail for more)
- Need to create IronNorth Code + IronNorth Verses accounts

## How To Resume After Break

1. Open terminal
2. cd ~/Studies/content-creation/framecraft
3. source venv/bin/activate
4. Open VS Code: code .
5. Paste this file into new Claude chat to resume
