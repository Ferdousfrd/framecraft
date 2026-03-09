# FrameCraft — Build Progress Log

## Project Info
- **Builder:** Ferdous (Software Engineering Student, Tampere, Finland)
- **Started:** Day 1 — Account setup
- **GitHub:** github.com/Ferdousfrd/framecraft
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
- ✅ Groq — active, used for script generation
- ✅ ElevenLabs — active, Harry voice working
- ✅ Pexels — saved (not used, replaced by AI generation)
- ✅ Pixazo — active, Flux model working, 100 free credits
- ✅ Together AI — saved (backup option)
- ✅ Gemini — saved (backup option)

## Project Structure
```
framecraft/
├── modules/
│   ├── script_generator.py  ✅ COMPLETE
│   ├── fact_checker.py      ✅ COMPLETE
│   ├── voice_generator.py   ✅ COMPLETE
│   └── video_fetcher.py     ✅ COMPLETE
├── pipelines/
├── outputs/
├── config/
│   └── settings.py          ✅ COMPLETE
├── docs/
│   ├── PROGRESS.md
│   └── ROADMAP.md
├── .env                     ✅ configured
├── .gitignore               ✅ configured
└── test_script.py           ✅ working
```

## Completed Modules

### script_generator.py ✅
- Takes topic string as input
- Calls Groq API (llama-3.3-70b model)
- Returns structured JSON with 5 segments
- Each segment: narration, visual description, duration
- Accuracy prompt — only verified historical facts
- Tested successfully with multiple Viking topics
- Will switch to Claude API when credits added

### fact_checker.py ✅
- Reviews generated script for historical accuracy
- Returns accuracy score out of 10
- Flags inaccurate or uncertain claims with corrections
- Feedback loop — issues fed back into next generation attempt
- Auto retry up to 3 times with fixes
- Saves best attempt to outputs/review/ if all attempts fail
- Approval threshold: 7/10 or above

### voice_generator.py ✅
- Converts script narration to MP3 audio files
- Uses ElevenLabs API with Harry (Fierce Warrior) voice
- One MP3 per segment for perfect sync
- Timestamped output folders — no overwriting
- Retry logic with 3 attempts and 2 second delay
- Input validation before API calls
- Partial failure cleanup
- Auto cleanup function for after video assembly

### video_fetcher.py ✅
- Generates AI images via Pixazo Flux API
- Applies Ken Burns effect via FFmpeg (5 movements for variety)
- One cinematic video clip per segment
- Timestamped output folders
- Retry logic with 3 attempts
- Partial failure cleanup
- Placeholder fallback for testing without API credits

## Upgrade Path for Visuals
```
Now (free trial):   Pixazo Flux      → artistic, cinematic style
Month 2 (~€8/mo):  Pixazo Nano Banana → photorealistic images
Month 3 (~€8/mo):  Pixazo Kling/Veo   → actual video generation
                                         Troy/300 movie style!
```

## Current Status
- ✅ Day 1 COMPLETE — accounts, GitHub, API keys
- ✅ Day 2 COMPLETE — script generator working, first commit pushed
- ✅ Day 3 COMPLETE — fact checker + voice generator working
- ✅ Day 4 COMPLETE — video fetcher with AI images + Ken Burns effect

## Next Session — Day 5
- [ ] Build assembler.py — combines audio + video + captions into final reel
- [ ] Test full pipeline end to end
- [ ] Watch first complete IronNorth reel!

## Known Issues
- YouTube channel still under review
- Anthropic API needs credits ($5 minimum)
- Script sometimes generates modern keywords for historical visuals
      → Fix: update script_generator prompt to ban modern elements
- Pixazo occasional 500 errors — retry system handles this fine

## How To Resume After Break
1. Open terminal
2. cd ~/Studies/content-creation/framecraft
3. source venv/bin/activate
4. Open VS Code: code .
5. Paste this file into new Claude chat to resume