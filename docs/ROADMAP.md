# FrameCraft — Full Roadmap

## Vision
FrameCraft is an automated AI content pipeline that crafts 
short-form videos across multiple niches and languages.
Deployed live through the IronNorth brand.

## Revenue Streams (in order of timeline)
1. Affiliate links (month 1 — no follower requirement)
2. YouTube ad revenue (month 3-6)
3. TikTok creator fund (month 2-4)
4. Sponsorships (month 4-8)
5. Content creation service for clients (month 6+)
6. FrameCraft SaaS subscriptions (year 1+)

## Content Brands
| Brand | Niche | Languages | Platforms |
|---|---|---|---|
| IronNorth | Viking/Finnish History | EN + Finnish | YT + TT + IG |
| IronNorth Code | Python/Coding | EN + Bengali | YT + TT + IG |

## Tech Stack
| Purpose | Tool | Cost |
|---|---|---|
| Script generation | Groq (free) → Claude API | €0 → €8/mo |
| Voice generation | ElevenLabs | €5/mo |
| Stock footage | Pexels API | Free |
| Video assembly | FFmpeg | Free |
| Cloud rendering | Google Colab | Free |
| Translation | DeepL API | Free tier |
| Total | | ~€13/mo |

## Pipeline Architecture
```
Topic Input
    ↓
script_generator.py    → generates 5-segment script
    ↓
fact_checker.py        → verifies historical accuracy
    ↓
translator.py          → translates to Bengali/Finnish
    ↓
voice_generator.py     → ElevenLabs creates audio per segment
    ↓
video_fetcher.py       → Pexels fetches stock footage per segment
    ↓
assembler.py           → FFmpeg combines video + audio + captions
    ↓
Output: publish-ready vertical video (1080x1920)
```

## Quality Layers
1. Accuracy prompt — instructs AI to use verified facts only
2. Fact checker module — second AI reviews generated script
3. Voice sync — audio duration drives video length
4. Caption sync — word-level timestamps from ElevenLabs
5. Final review prompt — AI checks overall quality before output

## IP Protection Strategy
- Pipeline code stays on private server (never given to clients)
- Clients get content output only (videos, not the system)
- SaaS users get a UI interface (never see underlying code)
- Core prompts are trade secrets — never exposed

## Build Phases

### Phase 1 — Core Pipeline (Weeks 1-3)
- [x] script_generator.py
- [ ] fact_checker.py
- [ ] voice_generator.py
- [ ] video_fetcher.py
- [ ] assembler.py
- [ ] translator.py

### Phase 2 — Multi-language + Polish (Weeks 4-5)
- [ ] Bengali translation layer
- [ ] Bengali voice on ElevenLabs
- [ ] Intro/outro branding
- [ ] Background music layer
- [ ] Caption styling

### Phase 3 — Launch (Week 6)
- [ ] Generate first 30 videos
- [ ] Schedule posting on all platforms
- [ ] Write SEO descriptions + hashtags
- [ ] Launch all accounts same week

### Phase 4 — Scale (Month 2-3)
- [ ] Add IronNorth Code pipeline (Manim)
- [ ] Add IronNorth Verses pipeline
- [ ] Add more social accounts
- [ ] First affiliate links live

### Phase 5 — Monetize (Month 4-6)
- [ ] YouTube Partner Program application
- [ ] First sponsor outreach
- [ ] Content service for first client
- [ ] FrameCraft SaaS planning

## Money Timeline
| Month | Milestone | Estimated Income |
|---|---|---|
| 1 | Launched, growing | €0 |
| 2 | 500-2000 followers | €20-80 |
| 3 | First monetized channels | €50-200 |
| 4-5 | First sponsors | €150-500 |
| 6 | Multiple streams | €300-800 |
| 9-12 | Full passive mode | €800-2500 |

## Competitive Edge
- Viking/Finnish history — underserved niche in English
- Bengali market — almost zero quality competition
- Developer built — better quality than no-code alternatives
- Fact checking layer — accuracy beats lazy AI farms
- Multi-language from day 1 — doubles content output
- Local angle — Hämeenlinna festival, Finnish community

## Portfolio Value
This project demonstrates:
- API integration (Groq, ElevenLabs, Pexels, Claude)
- Automated pipeline architecture
- Video processing (FFmpeg)
- Cloud computing (Google Colab)
- Multi-language system design
- Real deployed product with actual users and revenue