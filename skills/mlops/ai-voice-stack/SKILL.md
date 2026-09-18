---
name: ai-voice-stack
description: "Evaluate AI voice stack: STT, LLM, TTS, telephony vendors."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ai, voice, telephony, norwegian, saas, vendor-comparison]
---

# AI Voice Stack

Use this skill when building or evaluating an AI voice agent product (AI receptionist, phone bot, voice assistant). Covers the full vendor stack: orchestration, STT, LLM, TTS, telephony, and SMS — with Norwegian language support as a key evaluation axis.

## When to use
- Building a new AI voice product
- Evaluating providers for cost, latency, or Norwegian support
- Comparing orchestration platforms (Vapi, Retell, Bland, Synthflow)
- Estimating per-minute costs for a voice agent
- Deciding between BYOK (bring your own keys) vs bundled provider pricing

## Provider Stack Architecture

```
Phone Call → Telephony (Twilio/Telnyx) → Orchestration (Retell/Vapi)
                                              ↓
                                        STT (Deepgram/Whisper)
                                              ↓
                                        LLM (GPT-4o-mini/Gemini Flash)
                                              ↓
                                        TTS (Cartesia/ElevenLabs/OpenAI)
                                              ↓
                                        Telephony (return audio)
```

## Key Decision: Bundled vs BYOK

**Bundled (all in Retell):** ~$0.20-0.31/min. Simpler, one account, faster to market.
**BYOK (own keys):** ~$0.12-0.15/min. 40-50% cheaper, more config.

**Recommendation:** Start bundled, switch to BYOK at 10+ customers when margins matter.

## Norwegian Language Support Matrix

| Component | Best for Norwegian | Notes |
|-----------|-------------------|-------|
| STT | Deepgram Nova-3 | Dedicated Norwegian page, lowest latency |
| LLM | GPT-4o-mini | Best Norwegian comprehension at low cost |
| TTS | Cartesia Sonic | Lowest latency (~90ms), Norwegian supported |
| TTS (quality) | ElevenLabs Flash v2.5 | Highest quality Norwegian voice (~4.5/5 native) |
| Telephony | Twilio | Universal integration, Norwegian numbers |
| SMS | 46elks | Cheapest Nordic SMS (~€0.02/msg) |

## Cost Modeling

See `references/cost-models.md` for detailed per-minute and per-customer cost breakdowns at different volumes.

## Orchestration Platform Comparison

| Platform | Price/min | Norwegian | White-label | Ease |
|----------|-----------|-----------|-------------|------|
| Retell.ai | $0.07-0.31 | ✅ Native | ❌ 3rd party | Easy |
| Vapi | $0.15-0.33 | ✅ BYOK | ❌ 3rd party | Hard |
| Bland.ai | $0.11-0.15 | ✅ BYOK | ❌ | Easy |
| Synthflow | $0.15-0.37 | ✅ BYOK | ✅ Native ($2K/mo) | Easy |

**For Norwegian SaaS:** Retell.ai is the fastest path to market. Synthflow if building a white-label/reseller business.

## Pitfalls
- **PlayHT is being wound down** (Meta acquisition) — do not use for new projects
- **Telavox/Phonero are not API-first** — not suitable for programmatic voice AI
- **Google STT is overpriced for Norwegian** — Deepgram is better and cheaper
- **Norwegian telephony costs more than US** — budget $0.03-0.07/min for Twilio Norway
- **Retell.ai free tier caps at 20 concurrent calls** — fine for MVP, plan for scaling
- **TTS latency matters more than quality** for real-time voice — Cartesia wins on latency, ElevenLabs on quality