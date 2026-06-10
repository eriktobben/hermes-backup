---
name: baoyu-skills
description: "Baoyu creative content skills: article illustrations, knowledge comics, and infographics. All use image_generate with type × style × palette consistency, share the same download/curl patterns, and follow the same analyze→confirm→generate→finalize workflow."
version: 1.0.0
author: Hermes Agent (adapted from 宝玉/JimLiu)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [baoyu, creative, image-generation, illustration, comic, infographic]
    category: creative
---

# Baoyu Creative Skills (Umbrella)

This umbrella skill covers three Baoyu content-creation workflows that share the same core pattern: **analyze → confirm settings → generate prompts → download images → finalize**. All use `image_generate` (prompt-only, returns URL), all need absolute-path `curl -o` downloads, all require secrets stripping, and all follow the same type × style × palette design system.

## Shared Patterns (All Baoyu Skills)

### image_generate Constraints

- `image_generate` accepts only `prompt` and `aspect_ratio` (`landscape` | `portrait` | `square`)
- Returns a **URL**, not a local file — always download with `curl -fsSL "<url>" -o /abs/path/to/output.png`
- **Use absolute paths** for `curl -o` — never relative paths. Shell CWD can drift between calls.
- No backend selection — the user-configured provider is used.
- Auto-retry once on generation failure.

### Secrets Stripping

Scan source content for API keys, tokens, or credentials before writing any output file. Never include secrets in prompts or local files.

### Prompt File Requirement

Every image must have a saved prompt file before `image_generate` is called. The prompt file is the reproducibility record.

---

## Section A: Article Illustrator (`baoyu-article-illustrator`)

**Trigger**: User asks to illustrate an article, add images to content, or uses "为文章配图".

**Three dimensions**: Type (infographic, scene, flowchart, comparison, framework, timeline) × Style (notion, warm, minimal, blueprint, watercolor, elegant) × Palette (macaron, warm, neon).

**Output**: `{output-dir}/outline.md`, `prompts/NN-{type}-{slug}.md`, `NN-{type}-{slug}.png`

**Key principles**:
- Visualize concepts, not metaphors
- Labels use actual article data (numbers, terms, quotes)
- Insert `![description](path)` after the corresponding paragraph

Full procedure: See archived skill `baoyu-article-illustrator` (unpack from `~/.hermes/skills/.archive/` if needed).

---

## Section B: Knowledge Comic (`baoyu-comic`)

**Trigger**: User asks to create a knowledge/educational comic, biography comic, or uses "知识漫画", "教育漫画".

**Options**: Art style (ligne-claire, manga, realistic, ink-brush, chalk, minimalist) × Tone (neutral, warm, dramatic, romantic, energetic, vintage, action) × Layout (standard, cinematic, dense, splash, mixed, webtoon, four-panel).

**Output**: `comic/{topic-slug}/storyboard.md`, `characters/characters.md`, `prompts/NN-{page}-[slug].md`, `NN-{page}-[slug].png`

**Key workflow**:
1. Analyze content and check for existing directory
2. Confirm style, focus, audience via clarify
3. Generate storyboard + character definitions
4. Generate prompts (with character descriptions embedded inline)
5. Generate character sheet PNG (optional, human-facing review artifact)
6. Generate pages

**Timeout note**: `clarify` timeouts should be surfaced visibly — don't collapse all options to defaults.

Full procedure: See archived skill `baoyu-comic`.

---

## Section C: Infographic Generator (`baoyu-infographic`)

**Trigger**: User asks to create an infographic, visual summary, or uses "信息图", "可视化", "高密度信息大图".

**Options**: 21 layouts × 21 styles. Default layout: `bento-grid`. Default style: `craft-handmade`.

**Output**: `infographic/{topic-slug}/analysis.md`, `structured-content.md`, `prompts/infographic.md`, `infographic.png`

**Key workflow**:
1. Analyze content → save to `analysis.md`
2. Generate structured content → `structured-content.md`
3. Recommend 3-5 layout×style combinations (check keyword shortcuts first)
4. Confirm via clarify
5. Generate prompt → `prompts/infographic.md`
6. Generate image

Full procedure: See archived skill `baoyu-infographic`.

---

## Quick Reference: Aspect Ratio Mapping

| Desired ratio | `image_generate` format |
|---------------|------------------------|
| 16:9, 4:3 | `landscape` |
| 9:16, 3:4 | `portrait` |
| 1:1 | `square` |
| Custom (e.g. 3:4) | Nearest named ratio |

## Pitfalls

1. **Absolute paths for curl downloads** — never use relative paths; CWD changes between calls are a silent footgun.
2. **Prompt files before image generation** — reproducibility depends on it.
3. **Data integrity** — never summarize or paraphrase source statistics.
4. **No backend selection** — `image_generate` uses whatever model the user configured.
5. **Secret stripping** — always scan for API keys, tokens, credentials before writing output.
