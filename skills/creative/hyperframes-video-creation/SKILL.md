---
name: hyperframes-video-creation
description: >
  Create MP4 videos from HTML using HyperFrames (heygen-com/hyperframes).
  Prerequisites: Node.js 22+, FFmpeg, npx. Uses `npx hyperframes` CLI.
  Can create product promos, explainers, PR-to-video, captioned clips, motion graphics, slideshows, etc.
  Built for the Norwegian product catalog / e-commerce context Tobben works in.
---

# HyperFrames Video Creation

Create MP4 videos from HTML using HyperFrames. Covers the full pipeline: asset capture, composition authoring, GSAP animation, validation, BGM, and rendering.

## Prerequisites
- Node.js 22+ ✅ (installed)
- FFmpeg ✅
- npx ✅

## Quick start

```bash
npx hyperframes init my-video
cd my-video
npx hyperframes preview       # browser preview with live reload
npx hyperframes lint           # check for errors
npx hyperframes validate       # runtime validation in headless Chrome
npx hyperframes inspect        # check layout across timeline
npx hyperframes render --quality high --output renders/video.mp4
```

## Workflow skills (install on demand)

```bash
npx hyperframes skills update <workflow-name>
```

Workflows: `product-launch-video`, `website-to-video`, `faceless-explainer`, `pr-to-video`, `embedded-captions`, `talking-head-recut`, `motion-graphics`, `music-to-video`, `slideshow`, `general-video`, `remotion-to-hyperframes`

## Auth / Sign-in (check before starting)

```bash
npx hyperframes auth status
```
Relay output verbatim to the user. If not signed in, HeyGen TTS/BGM are unavailable; local engines are used instead. Continue offline on user consent.

---

## Tobben's video style guide

Based on the Serena Home Lysperler product video (references/product-launch-case-study.md), Tobben expects:

### Format
- **Social media reels: 9:16 portrait** (1080×1920) — always default to vertical for Instagram/TikTok/Reels
- **Landscape** (1920×1080) only for YouTube or embed use
- **Length: 30–50s** sweet spot for product promos

### Pacing
- **Fast entrance animations**: 0.3–0.5s duration — NOT 0.8–1.0s which feels sluggish
- Use `back.out()` easing for energetic, bouncy feels (`back.out(2)` or `back.out(2.5)`)
- Stagger element entrances by 0.5–0.6s gaps to keep visual tempo up
- Total video should feel quick and punchy, not lingering

### Continuous motion (CRITICAL — Tobben's #1 complaint)
Elements MUST keep moving after they animate in. A frozen screen after entrance looks like a still image — Tobben called this out explicitly: "it looks like a still image" and "there's no movement, you just added a small animation after it animates in."

**Ken Burns is the primary technique for images** — a continuous slow zoom/pan that NEVER stops:
```javascript
// Ken Burns: slow zoom on a background image for the entire scene duration
tl.fromTo("#bgImg", { scale: 1.0 }, { scale: 1.15, duration: 3, ease: "none", transformOrigin: "center center" }, 0);
```
Apply Ken Burns to EVERY full-bleed background image. The zoom should start before the scene and continue through its entire duration. `ease: "none"` for constant speed.

**For text/cards, use finite-repeat GSAP tweens** with helper functions:

```javascript
function floatUp(el, startAt, sceneDuration, delayAfter=0) {
  const visibleEnd = startAt + sceneDuration;
  const tweenStart = startAt + delayAfter;
  const remaining = visibleEnd - tweenStart;
  const repeats = Math.floor(remaining / 2) - 1;  // 2s cycle
  if (repeats > 0) {
    tl.to(el, { y: -12, duration: 1, ease: "sine.inOut", repeat: repeats, yoyo: true }, tweenStart);
  }
}
function pulse(el, startAt, sceneDuration, delayAfter=0) {
  const visibleEnd = startAt + sceneDuration;
  const tweenStart = startAt + delayAfter;
  const remaining = visibleEnd - tweenStart;
  const repeats = Math.floor(remaining / 1.5) - 1;  // 1.5s cycle
  if (repeats > 0) {
    tl.to(el, { scale: 1.04, duration: 0.75, ease: "sine.inOut", repeat: repeats, yoyo: true, transformOrigin: "center center" }, tweenStart);
  }
}
function sway(el, startAt, sceneDuration, delayAfter=0) {
  const visibleEnd = startAt + sceneDuration;
  const tweenStart = startAt + delayAfter;
  const remaining = visibleEnd - tweenStart;
  const repeats = Math.floor(remaining / 2.5) - 1;  // 2.5s cycle
  if (repeats > 0) {
    tl.to(el, { rotation: 2, duration: 1.25, ease: "sine.inOut", repeat: repeats, yoyo: true, transformOrigin: "center center" }, tweenStart);
  }
}
```

Apply at least ONE continuous motion to every scene's main element. Combine float + pulse on hero images.

### BGM / Audio
**Always include background music** — a silent video feels incomplete.
- Generate with ffmpeg (see `references/bgm-recipes.md` for working recipes)
- Embed as: `<audio id="bgm" class="clip" data-start="0" data-duration="TOTAL" data-track-index="1" data-volume="0.5" src="assets/bgm.mp3" loop>`
- The audio element MUST have an `id` attribute or it renders silent (HyperFrames requires `id` on audio elements)
- **CRITICAL: Volume must be boosted** — raw sine waves at 0.01-0.04 amplitude produce ~17kbps audio that is inaudible. Always add `volume=3.0` (or higher) amplification in the ffmpeg filter chain, and output as MP3 (not WAV) for better rendering.
- Fade in/out with `afade=t=in:d=1.5,afade=t=out:st=34:d=4` in ffmpeg
- Verify audio after render: `ffprobe renders/video.mp4 | grep Audio` — should show 128+ kbps

### Visuals
- **Use product images throughout** — minimum 6-7 images in a 36s reel
- Don't just show text — pair every claim with a product shot
- Full-bleed hero images with dark overlays create mood
- Logo needs a light background when it's a dark/black logo. Place on warm or cream bg.

### Consumer product vs corporate presentation (CRITICAL style lesson)
Tobben explicitly rejected a corporate-style video: "I feel the whole video is a bit corporate presentation, and not sale of a consumer product." The fix:

| Corporate (AVOID) | Consumer Reel (DO THIS) |
|---|---|
| Small text in grid/card layouts | **Giant bold text** filling the screen |
| Gentle fade-in, then freeze | **Ken Burns continuous zoom** on all images |
| Structured feature lists | **Emotional single-words** that slam in |
| Clean whitespace layouts | **Full-bleed images** with text overlays |
| "Plantebasert kvalitet" | "🌱 Plantebasert" — big, visual, fast |
| 0.8–1.0s entrance animations | **0.3–0.5s snap-in** with back.out easing |
| Elements stop moving after entrance | **Everything floats/sways/pulses** continuously |
| Grid of 4 product cards in rows | Products that **pop in one by one** with bounce |

**Tone**: Aspirational, warm, cozy — like a home decor brand's Instagram. Not a PowerPoint deck.
**Language**: Short, punchy, emotional. Norwegian. Feature → benefit translation.

### Sales language
Tobben's videos are for Norwegian e-commerce. Use:
- Prices prominently ("Fra kr 299")
- Shipping perks ("Gratis frakt over 800 kr")
- Gift appeal ("Perfekt gave")
- Strong CTA with URL
- Feature-to-benefit translation (not just "plantebasert" but "renere flamme, bedre inneklima")

---

## Single-file composition (direct approach)

For simpler videos or when the product-launch workflow is overkill, build everything in `index.html`:

### Composition structure (portrait example)
```html
<div id="root" data-composition-id="main" data-start="0" data-duration="36" data-width="1080" data-height="1920">
  <!-- BGM -->
  <audio id="bgm" class="clip" data-start="0" data-duration="36" data-track-index="1" data-volume="0.3" src="assets/bgm.wav" loop></audio>

  <div id="s1" class="clip bg-warm" data-start="0" data-duration="3" data-track-index="0">
    <!-- Scene content -->
  </div>
</div>
```

### GSAP timeline pattern
```javascript
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });

// FAST entrances (0.3-0.5s, back.out easing)
tl.fromTo("#element", { opacity:0, scale:0.7 }, { opacity:1, scale:1, duration:0.4, ease:"back.out(2.5)" }, 0.2);

// CONTINUOUS motion after entrance
floatUp("#element", 0, 3, 1.0);

window.__timelines["main"] = tl;
```

### Key concepts
- Each `<div>` with `class="clip"` and `data-track-index` is a track layer
- Timing via `data-start` (seconds) and `data-duration` (seconds)
- Full-bleed backgrounds ride on a `class="clip"` layer, never on `#root`
- The video base ground comes from `frame.md`'s `canvas` color
- Deterministic: same HTML + assets = same MP4 every time
- Format: landscape 1920×1080, portrait 1080×1920, square 1080×1080

---

## Pitfalls

### 🚫 GSAP infinite repeat breaks deterministic capture
```javascript
// BROKEN — prevents frame-accurate seeking
tl.to(".glow", { scale: 1.1, repeat: -1 }, 0);

// FIXED — finite repeat calculated for the scene
tl.to(".glow", { scale: 1.1, duration: 4, repeat: Math.floor(8/4)-1 }, 0);
```
Always use finite repeats. Calculate with `Math.floor(sceneDuration / cycleDuration) - 1`.

### 🚫 Audio element without id = silent
HyperFrames requires `<audio>` elements to have a unique `id` attribute or they are not discovered and produce no sound. Always add `id="bgm"` or similar.

### 🚫 Glow/overflow elements trigger layout warnings
Decorative elements partially outside their clip trigger `container_overflow`. They're intentional — add `data-layout-allow-overflow` to the parent when needed, or ignore these warnings.

### 🚫 Google Fonts add latency
HyperFrames resolves them during render (77+ font faces fetched), but they cause a lint warning. Prefer local `@font-face` when possible, or just acknowledge the warning.

### 🚫 Track density warning
6+ timed elements on the same track triggers a warning. Not blocking — disable with `--strict` or split into sub-compositions.

### 🚫 Scene occlusion in static analysis
The `inspect` tool flags text that overlaps between scenes as `text_occluded`. The clip system handles this at runtime via `data-start`/`data-duration`. Add `data-layout-allow-occlusion` to affected scenes or ignore if the clip timing is correct.

### 🚫 Logo visibility
If the logo PNG is dark/black, it must sit on a light or warm background. Never place a dark logo on a dark background. Either use a light background for the logo scene, or invert the logo.

---

## Render commands
```bash
cd <project>
npx hyperframes lint              # 0 errors required before render
npx hyperframes validate          # runtime check in headless Chrome
npx hyperframes inspect           # layout check across timeline
npx hyperframes render --quality high --output renders/video.mp4
```

Quality options: `draft` (fast preview), `standard` (balanced), `high` (final delivery).
With `--strict`, render aborts on lint errors.

---

## Reference: BGM generation with ffmpeg (use these volumes!)
```bash
# CRITICAL: volume amplification (volume=3.0) is required — raw sines at 0.01-0.04 amplitude produce silent audio
ffmpeg -y \
  -f lavfi -i "anoisesrc=d=38:c=pink:a=0.08" \
  -f lavfi -i "sine=frequency=261.63:duration=38" \
  -f lavfi -i "sine=frequency=329.63:duration=38" \
  -f lavfi -i "sine=frequency=392.00:duration=38" \
  -f lavfi -i "sine=frequency=196.00:duration=38" \
  -filter_complex " \
    [1]volume=0.15[c]; \
    [2]volume=0.12[e]; \
    [3]volume=0.12[g]; \
    [4]volume=0.10[sub]; \
    [0]volume=0.06[ns]; \
    [ns][c][e][g][sub]amix=inputs=5:duration=first:dropout_transition=0, \
    aecho=0.8:0.5:60:0.25, \
    highpass=f=60, \
    volume=3.0, \
    afade=t=in:d=1.5, \
    afade=t=out:st=34:d=4 \
  " \
  -ac 2 assets/bgm.mp3
```
This creates a C-major chord pad + sub-bass + pink noise for warmth. Outputs MP3 at 128kbps.
After render, verify: `ffprobe renders/video.mp4 | grep Audio` — expect 128+ kbps, not 17kbps.

## Reference: Serena Home brand palette
```
Dark text:  #181D25
Warm bg:   #F7F1E8, #F5EFE6, #FAF8F5
Blue acc:  #2F6ED5
Rose acc:  #F55266
Text:      #333D4C, #4E5562
White:     #FFFFFF
Background moods: warm/cream tones, not cold white
```

## Documentation
- Docs: https://hyperframes.heygen.com/introduction
- Quickstart: https://hyperframes.heygen.com/quickstart
- Showcase: https://hyperframes.heygen.com/showcase
- Playground: https://www.hyperframes.dev/

## Sharing rendered videos
After rendering, share via here.now (permanent, authenticated):
```bash
PUBLISH="/home/erik/.hermes/skills/productivity/here-now/scripts/publish.sh"
bash "$PUBLISH" renders/video.mp4 --title "Video Title" --client hermes
```
Outputs a permanent URL like `https://slug.here.now/` that the user can download from.
