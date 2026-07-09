# Product Launch Case Study: Serena Home Lysperler v2

Created 2026-07-09 for user Tobben. Three iterations of a product launch reel for Serena Home's "Lysperler" (light pearls).

## Video specs (final version)
- **Format:** 1080×1920 portrait (9:16 Instagram Reel)
- **Duration:** 36 seconds
- **FPS:** 30 (1080 frames)
- **BGM:** Yes — C-major ambient pad (generated with ffmpeg)
- **File size:** 7.9 MB (with audio)
- **Render time:** 1m 50s (low-memory, 1 worker)

## Scene structure (v2 final)

| Time | Scene | Animations | Continuous motion |
|---|---|---|---|
| 0–3s | Hook: Logo "SERENA HOME" + "Lysperler" title + "Plantebasert lys" badge on warm bg | Logo back.out, title scale bounce, badge fade | Logo floats, title pulses |
| 3–7s | Hero: Full-bleed product image with dark gradient overlay, tagline | Scale-in image 1.15→1.05, text slide-up | Slow continuous zoom 1.05→1.1 |
| 7–11s | What: Product image rotated in + "plantebasert voks" text | Image scale+rotation back.out, text fade-up | Image sways + pulses |
| 11–16s | Features: 3 feature cards (plant-based, reusable, creative) | Title fade, cards slide in from left with stagger | Each card floats independently |
| 16–22s | Products: 4 product cards in 2 rows with prices | Rows back.out, prices scale pop | Rows float, cards pulse |
| 22–27s | How it works: 3 horizontal step cards | Title fade, steps slide in from left stagger | Each step floats |
| 27–31s | Value: "Fra kr 299 · Gratis frakt" on rose bg | Scale bounce back.out | Card pulses gently |
| 31–36s | CTA: "serenahome.no" on dark bg with glow | Slide-up | CTA floats |

## Animation timing preferences (Tobben's feedback)
- Entrances: 0.3–0.5s (NOT 0.6–1.0s which feels sluggish)
- Easing: `back.out(2)` / `back.out(2.5)` for energetic feel
- Continuous motion is REQUIRED after entrance — elements must float/pulse/sway
- Stagger gap: 0.5–0.6s between elements

## BGM details
- Generated with ffmpeg sine wave + pink noise
- C major chord: C4(261.63) + E4(329.63) + G4(392.00)
- Volume: 0.03–0.04 per note, 0.3 overall track volume in HTML
- Fade in: 2s, fade out: 3s
- 38s WAV → embedded as `<audio id="bgm" class="clip" data-start="0" data-duration="36" data-track-index="1" data-volume="0.3" src="assets/bgm.wav" loop>`

## Key technical decisions
1. **Single-file composition** instead of full product-launch-video workflow — faster iteration for a ~36s reel
2. **Finite repeats** for continuous motion — `Math.floor(remaining / cycle) - 1` to satisfy deterministic renderer
3. **Data attributes** on scenes to suppress layout warnings: `data-layout-allow-occlusion`, `data-layout-allow-overlap`
4. **Logo on warm background** (FAF8F5) — the dark logo.png is invisible on dark backgrounds
5. **GSAP overwrite: "auto"** on overlapping image tweens

## Product images used (from capture)
- `lysperler-fra-serena-home.webp` — hero/hero image
- `lysperler-hvit-hilton.webp` — White Hilton scented (kr 349)
- `lysperler-hvit-sandalwood.webp` — White Sandalwood scented (kr 349)
- `lysperler-hvit-villblomst.webp` — White Wildflower scented (kr 349)
- `lysperler-lyng-gr-uten-duft.webp` — Heather Grey unscented (kr 299)

## CLI workflow
```bash
# Init
npx hyperframes init lysperle-launch

# Capture site
npx hyperframes capture "https://serenahome.no/olegutt" -o ./capture

# Copy assets
cp capture/assets/lysperler-*.webp assets/
cp capture/assets/logo-dark.png assets/

# Generate BGM
ffmpeg -y -f lavfi -i "anoisesrc=d=38:c=pink:a=0.02" -f lavfi -i "sine=frequency=261.63:duration=38" -f lavfi -i "sine=frequency=329.63:duration=38" -f lavfi -i "sine=frequency=392.00:duration=38" -filter_complex "[1]volume=0.04[ch1];[2]volume=0.035[ch2];[3]volume=0.035[ch3];[0]volume=0.015[noise];[noise][ch1][ch2][ch3]amix=inputs=4:duration=first:dropout_transition=0,afade=t=in:d=2,afade=t=out:d=3" -ac 2 assets/bgm.wav

# Check
npx hyperframes lint && npx hyperframes validate && npx hyperframes inspect

# Render
npx hyperframes render --quality high --output renders/reel-v2.mp4
```

## Render stats
- 1080 frames, 42% static-frame dedup (more motion = less dedup)
- Low-memory mode pinned to 1 worker (7.7 GB RAM threshold)
- Software rendering (no WebGL available on server)
- 58% frames reused from previous renders (cache)
- 7 product images loaded, 77 Inter font faces fetched
