# Emoji Font Troubleshooting for Pillow Tables

## The Problem

Discord doesn't support markdown tables natively. The `table-to-image` skill
generates PNG images with Pillow, but Pillow has limited emoji support.

## What Doesn't Work

### Noto Color Emoji (CBDT/CBLC bitmap)
```
/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf
```
- Pillow `ImageFont.truetype()` gives: `invalid pixel size`
- Reason: Pillow doesn't support color bitmap font formats (CBDT/CBLC).
- **Status**: Unusable regardless of raqm support.

### Noto Emoji as sole font (variable wght font)
```
~/.local/share/fonts/NotoEmoji-Regular.ttf
```
- Download: `https://github.com/google/fonts/raw/main/ofl/notoemoji/NotoEmoji%5Bwght%5D.ttf`
- Emojis render perfectly with `embedded_color=True`.
- **But**: Latin characters (letters, numbers) are extremely thin/stylized.
  Users report: "text is just squares" / "teksten er bare firkanter."
- Even with `set_variation_by_name("Bold")`, Latin glyphs are barely visible.
- **Status**: Ok for emoji-only cells, unusable for mixed text+emoji.

## The Fix: Dual-Font Rendering

Split each cell into runs of emoji vs non-emoji characters, then render each
run with the appropriate font:

| Content | Font | Notes |
|---------|------|-------|
| Latin text, numbers, symbols | DejaVu Sans | `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` |
| Bold Latin text | DejaVu Sans Bold | `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` |
| Emoji characters | Noto Emoji (variable) | `embedded_color=True`, `layout_engine=RAQM` |

### The emoji regex

```python
import re
EMOJI_RX = re.compile(
    '[\U0001F300-\U0001FAFF'     # Misc symbols, pictographs, emoticons
    '\U00002702-\U000027B0'      # Dingbats
    '\u2600-\u27BF'              # Misc symbols, arrows, math
    '\uFE00-\uFE0F'              # Variation selectors
    '\u200D'                     # Zero-width joiner
    ']'
)
```

This covers:
- U+1F300–U+1FAFF: Main emoji block
- U+2702–U+27B0: Dingbats (✅, ❌, ✨, etc.)
- U+2600–U+27BF: Misc symbols (☀, ☁, ⚙, etc.)
- U+FE00–U+FE0F: Variation selectors (emoji presentation)
- U+200D: Zero-width joiner (for flag sequences, families)

### ZWJ sequence handling

When a ZWJ (`\u200D`) is found in a run, consume the next emoji character(s)
as part of the same sequence. This correctly renders:
- 👨‍👩‍👧‍👦 — family (multi-ZWJ)
- 🏳️‍🌈 — rainbow flag
- Skin tone sequences: 👍🏻, 👍🏿

### Column width measurement

When measuring mixed text:
```python
def measure_mixed(draw, text, ft, fe):
    return sum(draw.textlength(seg, font=fe if e else ft)
               for e, seg in split_emoji_runs(text))
```

This ensures columns auto-size to fit both text and emoji widths.

## Verification

After rendering, check that emojis are actually multicolor (not boxes):

```python
img = Image.open('/home/erik/tmp_table.png')
pixels = set()
for y in range(40, 80):          # first data row
    for x in range(10, 40):       # first cell area
        r, g, b, a = img.getpixel((x, y))
        if a > 50:
            pixels.add((r, g, b))
if len(pixels) > 20:
    print("✓ Emoji is multicolor (real glyphs)")
else:
    print("✗ Emoji likely shows as boxes")
```
