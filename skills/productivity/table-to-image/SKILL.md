---
name: table-to-image
description: "Render data tables as dark-themed PNG images using Python/Pillow for Discord. Use when the user asks for formatted tables, comparisons, or data summaries — especially on Discord where markdown tables aren't supported and code blocks wrap badly on mobile."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [discord, tables, images, pillow, formatting]
    related_skills: []
---

# Table-to-Image (Discord)

Generate clean, dark-themed table PNGs with Python Pillow. Bypasses Discord's lack of markdown table support and avoids mobile line-wrapping.

## When to Use

- User asks for **tables** on Discord
- User says "tabell", "sammenligning", "comparison", "data", "oversikt"
- Any structured data with rows/columns where formatting matters
- **Don't use for**: simple one-line lists or single-row data (text is fine)

## How It Works

1. Define `data` as a list of lists — first row is the header
2. Pillow measures text width with `textlength()` to auto-size columns
3. Draws rows with alternating backgrounds and optional gold highlights
4. Uses **dual-font rendering**: DejaVu Sans for Latin text, Noto Emoji for emoji characters only
5. Saves to `/home/erik/tmp_table.png` and sends as `MEDIA:/home/erik/tmp_table.png`

## Font Setup (emoji support)

DejaVu Sans (system default) does NOT render emoji glyphs — they show as empty boxes.
The NotoColorEmoji font (`/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf`) gives "invalid pixel size" in Pillow.
The Noto Emoji variable font renders emojis but its Latin glyphs are invisible/too thin — users report "text is just squares."

**Solution: dual-font approach** — DejaVu Sans for Latin text, Noto Emoji for emoji characters only, split per-character run.

### Install the emoji font

```bash
mkdir -p ~/.local/share/fonts
curl -sL -o ~/.local/share/fonts/NotoEmoji-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/notoemoji/NotoEmoji%5Bwght%5D.ttf"
fc-cache -f ~/.local/share/fonts/
```

### Requirements

- Pillow with **raqm** support: `from PIL import features; features.check('raqm')` — the Hermes venv Pillow ships with raqm.
- Image mode **RGBA** (not RGB) for `embedded_color=True`.

## Template Script (with emoji support)

```python
from PIL import Image, ImageDraw, ImageFont
import re, os

# ── Data (emojis work!) ──
data = [
    ["Header 1", "Header 2", "Header 3"],
    ["Row 1 val", "42 000", "299 900 kr"],
    ["✨ Row 2 val", "15 000", "199 900 kr"],
]

# Rows to highlight (gold background + bold) — 0-indexed, 0 = header
highlight_rows = {1}

# ── Style ──
BG = (30, 31, 34)
HEADER_BG = (47, 49, 54)
ROW_ALT = (37, 39, 43)
HIGHLIGHT = (53, 46, 28)
TEXT_COLOR = (212, 215, 217)
HIGHLIGHT_TEXT = (250, 215, 75)
HEADER_TEXT = (255, 255, 255)
SEPARATOR = (64, 68, 75)

# ── Fonts ──
TEXT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
TEXT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
EMOJI_FONT = os.path.expanduser("~/.local/share/fonts/NotoEmoji-Regular.ttf")

font_text = ImageFont.truetype(TEXT_FONT, 17)
font_text_bold = ImageFont.truetype(TEXT_BOLD, 17)
font_emoji = ImageFont.truetype(EMOJI_FONT, 17, layout_engine=ImageFont.Layout.RAQM)

# ── Emoji detection ──
EMOJI_RX = re.compile(
    '[\U0001F300-\U0001FAFF'
    '\U00002702-\U000027B0'
    '\u2600-\u27BF'
    '\uFE00-\uFE0F'
    '\u200D'
    ']'
)

def split_emoji_runs(text):
    """Split text into [(is_emoji, segment), ...] tuples."""
    runs, i = [], 0
    while i < len(text):
        ch = text[i]
        if EMOJI_RX.match(ch):
            j = i + 1
            while j < len(text) and text[j] in '\uFE0F\u200D\U0001F3FB\U0001F3FC\U0001F3FD\U0001F3FE\U0001F3FF':
                j += 1
            if '\u200D' in text[i:j]:
                while j < len(text) and (EMOJI_RX.match(text[j]) or text[j] in '\uFE0F'):
                    j += 1
            runs.append((True, text[i:j]))
            i = j
        else:
            j = i + 1
            while j < len(text) and not EMOJI_RX.match(text[j]):
                j += 1
            runs.append((False, text[i:j]))
            i = j
    return runs

def table_cell_draw(draw, x, y, text, font_text_obj, font_emoji_obj, fg_color):
    """Render a cell with mixed text+emoji using separate fonts."""
    cx = x
    for is_emoji, seg in split_emoji_runs(text):
        fnt = font_emoji_obj if is_emoji else font_text_obj
        kwargs = {"fill": fg_color, "font": fnt}
        if is_emoji:
            kwargs["embedded_color"] = True
        draw.text((cx, y), seg, **kwargs)
        cx += draw.textlength(seg, font=fnt)

def measure_mixed(draw, text, font_text_obj, font_emoji_obj):
    """Width of mixed text with correct font per run."""
    return sum(draw.textlength(seg, font=font_emoji_obj if e else font_text_obj)
               for e, seg in split_emoji_runs(text))


# ── Measure columns ──
img_tmp = Image.new("RGBA", (1, 1))
draw_tmp = ImageDraw.Draw(img_tmp)

col_widths = []
for ci in range(len(data[0])):
    max_w = 0
    for ri, row in enumerate(data):
        w = measure_mixed(draw_tmp, str(row[ci]),
                         font_text_bold if ri == 0 else font_text, font_emoji)
        if w > max_w:
            max_w = w
    col_widths.append(int(max_w) + 40)

row_height = 36
header_height = 40
total_w = sum(col_widths)
total_h = header_height + len(data[1:]) * row_height

# ── Render ──
img = Image.new("RGBA", (total_w, total_h), BG)
draw = ImageDraw.Draw(img)

y = 0
for i, row in enumerate(data):
    if i == 0:
        bg, fnt, fg, rh = HEADER_BG, font_text_bold, HEADER_TEXT, header_height
    else:
        rh = row_height
        if i in highlight_rows:
            bg, fnt, fg = HIGHLIGHT, font_text_bold, HIGHLIGHT_TEXT
        else:
            bg = ROW_ALT if i % 2 == 0 else BG
            fnt, fg = font_text, TEXT_COLOR

    draw.rectangle([0, y, total_w, y + rh], fill=bg)
    draw.line([(0, y), (total_w, y)], fill=SEPARATOR, width=1)
    x = 14
    for ci, cell in enumerate(row):
        table_cell_draw(draw, x, y + (rh - 17) // 2, str(cell), fnt, font_emoji, fg)
        x += col_widths[ci]
    y += rh

draw.line([(0, y), (total_w, y)], fill=SEPARATOR, width=1)

path = "/home/erik/tmp_table.png"
img.save(path)
print(f"Saved {path} ({img.size[0]}x{img.size[1]})", flush=True)
```

Then send with: `MEDIA:/home/erik/tmp_table.png`

## Key Parts to Customize Per Use

| What | Where |
|------|-------|
| Data rows | `data = [...]` — first row is header |
| Highlighted rows | `highlight_rows = {1, 5}` — set of 1-indexed row numbers after header |
| Column content | Each cell is a string |
| Emoji handling | Unicode emojis (🧠, ✅, 🐛, etc.) work via dual-font rendering. No extra config needed. |

## Common Pitfalls

- **Pillow not installed**: `pip install Pillow` (it's usually there on this system)
- **Missing Noto Emoji font**: Run the curl + fc-cache from the Font Setup section above. If curl fails, download manually from [Google Fonts Noto Emoji](https://github.com/google/fonts/tree/main/ofl/notoemoji)
- **DejaVu Sans does NOT support emojis**: If you use DejaVu Sans (`/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`), all emoji characters will render as empty boxes. Always use the dual-font approach when data contains emojis.
- **Noto Emoji ALONE produces unreadable Latin text** (most critical pitfall): Using Noto Emoji as the sole font will make emojis look great but Latin characters (letters, numbers) will be very thin and users will report "text is just squares" or "teksten er bare firkanter." Always use DejaVu Sans for text + Noto Emoji for emoji characters only.
- **NotoColorEmoji.ttf fails**: The color bitmap version (`/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf`) gives "invalid pixel size" in Pillow. Use the variable-weight NotoEmoji (non-color) instead.
- **Embedded_color requires RGBA mode**: Image mode must be `"RGBA"`, not `"RGB"`, for `embedded_color=True` to work. Background color needs an alpha channel: `(30, 31, 34, 255)`.
- **RAQM required**: Pillow must have raqm enabled. Check with `from PIL import features; features.check('raqm')`. The Hermes venv Pillow ships with raqm.
- **Variable font weight**: Noto Emoji is a variable font with wght axis. Set weight explicitly: `font.set_variation_by_name("Regular")` or `font.set_variation_by_name("Bold")`. Default weight may be too light.
- **Text overflow**: `textlength()` auto-sizes columns, but long single words can still overflow. Keep cell text under ~30 chars
- **Multiple tables**: Only saves one file at `/home/erik/tmp_table.png` — overwrites on each run. Fine for one-at-a-time use
- **Emoji width**: Emojis are wider than Latin chars. The `textlength()` accounts for this, but very emoji-heavy cells may look cramped. Test if unsure
- **ZWJ sequences**: Flags and multi-emoji sequences (family, skin tones) use ZWJ (\u200D) and variation selectors (\uFE0F). The `split_emoji_runs()` helper handles these correctly.
- **Don't use the single-font shortcut**: Even though Noto Emoji can render both text and emoji, its Latin glyphs are extremely thin/stylized and appear as invisible boxes on dark backgrounds. Always use DejaVu Sans for Latin text.

## Verification Checklist

- [ ] Image file saved successfully (check output path)
- [ ] Image is attached as `MEDIA:/home/erik/tmp_table.png` in the message
- [ ] All data rows present and correctly ordered
- [ ] Highlighted rows are visually distinct
- [ ] Headers are bold
- [ ] Emojis render as actual emoji glyphs (not empty boxes) — check with color-distinctness test: `len(set(pixels in text area)) > 20` confirms multicolor emoji rendering
- [ ] Latin text is crisp and readable (white/light gray on dark background)
