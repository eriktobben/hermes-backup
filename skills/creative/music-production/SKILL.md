---
name: music-production
description: "AI-assisted music production: songwriting craft, Suno prompt engineering, open-source music generation with HeartMuLa, and audio analysis/visualization with songsee. Covers lyrics, prompting, local music generation, and spectrogram analysis of results."
tags: [music, songwriting, suno, heartmula, songsee, audio, generation, analysis]
platforms: [linux, macos, windows]
related_skills: []
---

# AI Music Production Pipeline

Four phases of the AI music workflow, unified in one skill. Use the section that matches
the user's question — or combine them for a full pipeline: write lyrics → generate music
→ analyze the result.

## When to use

- User wants to write song lyrics, a parody, or a Suno AI prompt
- User wants to generate music with open-source models (HeartMuLa)
- User wants to analyze or visualize an audio file (spectrograms, MFCC, chroma)
- User wants to combine any of the above into a complete music production workflow

---

## § Songwriting & AI Prompt Engineering

Everything below is a GUIDELINE, not a rule. Art breaks rules on purpose.
Use what serves the song. Ignore what doesn't.

### Song Structure

Common skeletons — mix, modify, or throw out as needed:

```
ABABCB  Verse/Chorus/Verse/Chorus/Bridge/Chorus    (most pop/rock)
AABA    Verse/Verse/Bridge/Verse (refrain-based)    (jazz standards, ballads)
ABAB    Verse/Chorus alternating                    (simple, direct)
AAA     Verse/Verse/Verse (strophic, no chorus)     (folk, storytelling)
```

Building blocks: Intro, Verse, Pre-Chorus, Chorus, Bridge, Outro.

### Rhyme & Meter

**Rhyme types** (tight → loose): Perfect (lean/mean), Family (crate/braid),
Assonance (had/glass), Consonance (scene/when), Near/slant.

**Meter:** Say it out loud. Match stressed syllables between parallel lines.
Breaking meter on purpose can create emphasis.

### Emotional Arc & Dynamics

Map energy on a 1-10 scale: Intro 2-3 → Verse 5-6 → Pre-Chorus 7 → Chorus 8-9.
The most powerful trick: contrast. Whisper-before-scream. Sparse-before-dense.

### Writing Lyrics

- Show, don't tell: "Your hoodie's still on the hook by the door" beats "I was sad"
- The hook: the line people remember. Usually the title. Place where it lands hardest.
- Avoid clichés, Yoda-speak forced rhymes, flat dynamics.

### Parody Adaptation

Map original's structure first: syllables per line, rhyme scheme, stressed syllables.
Match stressed syllables to same beats. On long held notes, match the vowel sound.
Monosyllabic swaps keep rhythm intact. Keep some original lines for recognizability.

### Suno AI Prompt Engineering

**Style formula:** Genre + Mood + Era + Instruments + Vocal Style + Production + Dynamics.
Describe the journey: "Begins as a haunting whisper over sparse piano. Builds through
the chorus with full orchestra. Outro strips back to a fragile whisper."

**Metatags** (in [brackets]): [Verse] [Chorus] [Bridge] [Outro] [Whispered] [Belted]
[Soulful] [Explosive] [Emotional Climax] [Female Vocals] [Male Vocals]

**Tips:**
- V4.5+ supports 1,000 chars in Style field
- No artist names or trademarks — describe the sound
- Always use Custom Mode for serious work
- 5-8 tags per section max
- Phonetic respelling for AI singers: "through" → "thru", "Nous" → "Noose"
- Spell out numbers: "24/7" → "twenty four seven"

### Workflow

1. Write concept/hook first
2. If adapting, map the original structure
3. Generate raw material
4. Draft lyrics into structure
5. Read/sing aloud
6. Build Suno style description
7. Add metatags
8. Generate 3-5 variations

---

## § Open-Source Music Generation (HeartMuLa)

HeartMuLa generates full songs from lyrics + tags using open-source models (Apache-2.0).
Comparable to Suno for local/offline generation.

### Hardware Requirements

- Minimum: 8GB VRAM (with `--lazy_load true`)
- Recommended: 16GB+ VRAM
- No GPU: CPU possible but extremely slow; recommend Colab or the online demo

### Installation

```bash
git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib
uv venv --python 3.10 .venv
. .venv/bin/activate
uv pip install -e .
uv pip install --upgrade datasets transformers
```

### Source Patches (required for transformers 5.x)

**Patch 1** — In `src/heartlib/heartmula/modeling_heartmula.py`, `setup_caches` method,
add after the `reset_caches` try/except block:

```python
from torchtune.models.llama3_1._position_embeddings import Llama3ScaledRoPE
for module in self.modules():
    if isinstance(module, Llama3ScaledRoPE) and not module.is_cache_built:
        module.rope_init()
        module.to(device)
```

**Patch 2** — In `src/heartlib/pipelines/music_generation.py`, add
`ignore_mismatched_sizes=True` to all `HeartCodec.from_pretrained()` calls.

### Model Checkpoints

```bash
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' 'HeartMuLa/HeartCodec-oss-20260123'
```

### Usage

```bash
cd heartlib && . .venv/bin/activate
python ./examples/run_music_generation.py \
  --model_path=./ckpt --version="3B" \
  --lyrics="./assets/lyrics.txt" --tags="./assets/tags.txt" \
  --save_path="./assets/output.mp3" --lazy_load true
```

**Tags format:** comma-separated, no spaces: `piano,happy,wedding,synthesizer,romantic`
**Lyrics format:** use bracketed structural tags: `[Intro]`, `[Verse]`, `[Chorus]`, `[Bridge]`, `[Outro]`

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max_audio_length_ms` | 240000 | Max length in ms (240s = 4 min) |
| `--topk` | 50 | Top-k sampling |
| `--temperature` | 1.0 | Sampling temperature |
| `--cfg_scale` | 1.5 | Classifier-free guidance scale |
| `--lazy_load` | false | Load/unload models on demand |

### Pitfalls

- Do NOT use bf16 for HeartCodec — use fp32 (degrades quality)
- Tags may be partially ignored; lyrics tend to dominate
- Triton not available on macOS
- RTF ≈ 1.0 (4-min song takes ~4 min to generate)

### Links

- Repo: https://github.com/HeartMuLa/heartlib
- Models: https://huggingface.co/HeartMuLa
- Paper: https://arxiv.org/abs/2601.10547

---

## § Audio Analysis & Visualization (songsee)

Generate spectrograms and multi-panel audio feature visualizations from audio files
using the `songsee` CLI (Go).

### Prerequisites

```bash
go install github.com/steipete/songsee/cmd/songsee@latest
```

### Quick Start

```bash
# Basic spectrogram
songsee track.mp3

# Multi-panel visualization grid
songsee track.mp3 --viz spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux

# Time slice
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg

# From stdin
cat track.mp3 | songsee - --format png -o out.png
```

### Visualization Types

| Type | Description |
|------|-------------|
| `spectrogram` | Standard frequency spectrogram |
| `mel` | Mel-scaled spectrogram |
| `chroma` | Pitch class distribution |
| `hpss` | Harmonic/percussive separation |
| `selfsim` | Self-similarity matrix |
| `loudness` | Loudness over time |
| `tempogram` | Tempo estimation |
| `mfcc` | Mel-frequency cepstral coefficients |
| `flux` | Spectral flux (onset detection) |

### Common Flags

`--style` (classic/magma/inferno/viridis/gray), `--width`/`--height`,
`--window`/`--hop`, `--min-freq`/`--max-freq`, `--format` (jpg/png)

### Notes

- WAV and MP3 decoded natively; other formats need ffmpeg
- Output images can be inspected with vision_analyze for automated analysis
- Useful for comparing audio outputs, debugging synthesis, or documenting pipelines
