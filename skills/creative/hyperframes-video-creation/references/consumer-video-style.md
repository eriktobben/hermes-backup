# Consumer Product Video Style Patterns

## What Tobben rejected (v1-v2)
- Grid layouts with small text cards → "feels like a corporate presentation"
- Elements that animate in once and freeze → "there's no movement"
- Feature lists as text → too informational, not emotional
- Small product thumbnails in cards → not impactful enough
- Fade-in transitions → too slow, too gentle

## What worked (v3)
- **Giant text** filling the screen (120px font-weight:900)
- **Ken Burns** on full-bleed background images (continuous slow zoom, never stops)
- **Fast slam-in** animations (0.3-0.5s, back.out(2) easing)
- **One word per hit** ("Fyll", "Tenn", "Nyt") instead of full sentences
- **Products popping in** one by one with bounce, not all at once in a grid
- **Big number reveal** for price ("KR 299" at 140px)
- **Emotional language**: "Skap stemning ✨" not "Plantebasert kvalitet"

## Composition structure that works
```
S1 (0-3s):   HOOK — Giant title + Ken Burns product bg
S2 (3-6s):   VIBE — Emotional text + Ken Burns product bg  
S3 (6-10s):  FEATURES — 3 rapid-fire text cards, staggered
S4 (10-16s): PRODUCTS — Grid that pops in one-by-one, bobs
S5 (16-21s): HOW — 3 big words slamming in ("Fyll → Tenn → Nyt")
S6 (21-26s): VALUE — Big price reveal + shipping perks
S7 (26-31s): CTA — Button that pulses
S8 (31-36s): OUTRO — Product beauty shot + logo + URL
```

## Animation recipe
1. Ken Burns on EVERY background image (scale 1.0 → 1.15, ease:"none")
2. Text entrance: opacity:0 + scale:0.5 → opacity:1 + scale:1, 0.4s, back.out(3)
3. After entrance: continuous float (y:-12, sine.inOut, yoyo) or pulse (scale:1.05)
4. Product cards: stagger by 0.5s, each with back.out(2) bounce

## Norwegian e-commerce language patterns
- "Skap stemning" (Create atmosphere)
- "Perfekt gave" (Perfect gift)  
- "Gratis frakt over X kr" (Free shipping over X kr)
- "Rask levering fra Norge" (Fast delivery from Norway)
- "Fra kr X" (From kr X) — price anchoring
- Feature → benefit: "Plantebasert" → "Renere flamme, bedre inneklima"
