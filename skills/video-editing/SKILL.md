---
name: video-editing
description: "Edit existing video footage into polished outputs - hero videos, product demos, social media clips. Covers the full pre-production and production workflow including accessing clips from cloud storage, downloading and organizing, extracting frames for analysis, analyzing content programmatically, planning the edit, and executing with ffmpeg. Use when the user wants to edit, cut, trim, combine, or transform existing video clips (not create videos from HTML/scratch)."
tags: [video, editing, ffmpeg, production, workflow]
---

# Video Editing

Edit existing video footage into polished outputs. This skill covers the workflow from accessing raw clips to delivering the final edit.

## When to use

Use this skill when the user wants to:
- Edit existing video clips (trim, cut, combine, transform)
- Create a "hero video" or product demo from raw footage
- Assemble social media clips from multiple source videos
- Process video files downloaded from cloud storage

**Do NOT use when:**
- Creating videos from HTML/CSS/JS → use `hyperframes-video-creation`
- Resolving media assets (BGM, SFX, images) → use `media-use`
- Converting video to ASCII → use `ascii-video`

## Pre-production workflow

### 1. Access clips from cloud storage

**Dropbox shared folders:**
```bash
# Folder links serve as zip when dl=1 — access individual files via their specific URLs
# Individual file download (dl=1 triggers direct download)
curl -sL -o output.MOV "https://www.dropbox.com/scl/fo/<folder-id>/<file-hash>/<filename.MOV>?rlkey=<key>&dl=1"

# To see what's in a folder, access the web page (dl=0)
curl -sL "https://www.dropbox.com/scl/fo/<folder-id>/<hash>?dl=0"
```

**Google Drive shared folders:**
```bash
pip install gdown
gdown --folder <share-url>
```

### 2. Analyze video metadata

Get detailed information about each clip:
```bash
# Full JSON metadata
ffprobe -v quiet -print_format json -show_format -show_streams input.MOV

# Quick key properties
ffprobe -v quiet -show_entries stream=width,height,codec_name,r_frame_rate,duration -of csv=p=0 input.MOV
```

Key properties to note:
- Resolution (4K? 1080p? vertical?)
- Frame rate (24fps? 30fps? 120fps slow-mo?)
- Duration (short clips vs long takes)
- Codec (HEVC? H.264? ProRes?)

### 3. Extract frames for visual analysis

Extract evenly-spaced keyframes to understand clip content:
```bash
FRAMES=4
DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 input.MOV)
for i in $(seq 0 $((FRAMES-1))); do
  TIMESTAMP=$(python3 -c "print(f'{float($DURATION)*$i/$FRAMES:.2f}')")
  ffmpeg -y -ss "$TIMESTAMP" -i input.MOV -vframes 1 -q:v 2 "frames/frame_${i}.jpg"
done
```

### 4. Analyze frame content

**Color profile analysis** (understand lighting/mood):
```python
from PIL import Image
img = Image.open('frame.jpg')
img_small = img.resize((100, 100))
pixels = list(img_small.getdata())
avg_r = sum(p[0] for p in pixels) / len(pixels)
avg_g = sum(p[1] for p in pixels) / len(pixels)
avg_b = sum(p[2] for p in pixels) / len(pixels)
brightness = (avg_r + avg_g + avg_b) / 3
print(f'avg_rgb=({avg_r:.0f},{avg_g:.0f},{avg_b:.0f}), brightness={brightness:.0f}')
```

**Visual content analysis via model API:**

When the model supports vision (e.g., mimo-v2.5, GPT-4o, Claude), you can analyze local frames by calling the model API directly with base64-encoded images:

```python
import base64, requests, os

def analyze_frame(image_path, api_key, base_url, model, prompt="Describe this video frame"):
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}}
        ]}],
        "max_tokens": 500
    }
    response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=60)
    return response.json()["choices"][0]["message"]["content"]

# Usage
api_key = os.environ.get("OPENCODE_GO_API_KEY")  # or other vision model key
analysis = analyze_frame("frames/frame_0.jpg", api_key, "https://opencode.ai/zen/go/v1", "mimo-v2.5")
```

**Visual content analysis options (in preference order):**
1. **Model API with base64** — most reliable for analyzing local files (see above)
2. **Ask user to describe** — only when API analysis is unavailable or user prefers
3. **Color profile analysis** — fallback for understanding lighting/mood only

### Pitfall: Don't ask user to describe video content

Users expect the agent to figure out what's in the video clips using vision capabilities. Asking "what's in this clip?" forces manual work the user doesn't want to do. Always try programmatic analysis first:
1. Extract frames
2. Analyze via model API (base64 images)
3. Only ask user if analysis fails or is ambiguous

The user's role is to approve/reject the edit plan, not to describe raw footage.

## Planning the edit

Before executing, clarify with the user:
1. **Which clips** are relevant (filenames + timestamps)
2. **Target length** (30s? 60s? 2min?)
3. **Music/voiceover** requirements
4. **Text/titles/logo/CTA**
5. **Target platform** (social media, YouTube, website)
6. **Aspect ratio** (9:16 portrait for reels, 16:9 landscape for YouTube)

## Complete workflow: Vision analysis → Edit

When the user provides clips and wants you to figure out the content:

1. **Download clips** selectively from cloud storage
2. **Extract frames** (4-5 per clip, evenly spaced)
3. **Analyze frames** via model API (see `references/vision-pipeline.py`)
4. **Plan the edit** based on analysis results
5. **Execute** with ffmpeg (trim, slow-mo, text, fades)
6. **Deliver** final video

See `references/vision-pipeline.py` for the complete analysis script.

## Production: ffmpeg commands

### Trim / extract a segment
```bash
ffmpeg -i input.MOV -ss 00:00:12 -to 00:00:20 -c copy output.MOV
```

### Combine multiple clips
```bash
printf "file '%s'\n" clip1.MOV clip2.MOV clip3.MOV > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy output.MOV
```

### Change speed (slow-mo / time-lapse)
```bash
# SLOW-MOTION: 120fps → 24fps (5x slower)
# CRITICAL: Use -t on INPUT only, not output. The setpts filter expands duration.
ffmpeg -ss 0 -t 3 -i input.MOV -vf "setpts=5*PTS" -r 24 -c:v libx264 output_slow.MOV
# 3 seconds input → 15 seconds output

# 120fps → 30fps (4x slower)
ffmpeg -ss 0 -t 3 -i input.MOV -vf "setpts=4*PTS" -r 30 -c:v libx264 output_slow.MOV

# Time-lapse (speed up 4x)
ffmpeg -i input.MOV -vf "setpts=0.25*PTS" -c:v libx264 output_timelapse.MOV
```

### Add text overlay
```bash
ffmpeg -i input.MOV -vf "drawtext=text='Your Text':fontsize=48:fontcolor=white:x=100:y=100" output.MOV
```

### Crop / reframe
```bash
# 16:9 to 9:16 (portrait)
ffmpeg -i input.MOV -vf "crop=ih*9/16:ih,scale=1080:1920" output.MOV
```

### Add fade transitions
```bash
# Fade in 1s, fade out 1s
ffmpeg -i input.MOV -vf "fade=t=in:st=0:d=1,fade=t=out:st=9:d=1" -af "afade=t=in:d=1,afade=t=out:st=9:d=1" output.MOV
```

### Add background music
```bash
ffmpeg -i video.MOV -i music.mp3 -filter_complex "[1:a]volume=0.3[bgm];[0:a][bgm]amix=inputs=2:duration=first" output.MOV
```

## Post-production

### Color correction
```bash
# Warm tone
ffmpeg -i input.MOV -vf "colorbalance=rs=0.1:gs=0.05:bs=-0.1" output.MOV
```

### Stabilization
```bash
# Two-pass stabilization
ffmpeg -i input.MOV -vf vidstabdetect=shakiness=5:accuracy=15 -f null -
ffmpeg -i input.MOV -vf vidstabtransform=smoothing=30:optzoom=1 output.MOV
```

### Export settings
```bash
# High quality for social media (H.264, CRF 18)
ffmpeg -i input.MOV -c:v libx264 -crf 18 -preset slow -c:a aac -b:a 192k output.mp4

# Smaller file size (CRF 23)
ffmpeg -i input.MOV -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k output.mp4
```

## Pitfalls

### 🚫 Large files from cloud storage
Dropbox shared folders can be GBs. Download selectively — ask which clips are relevant before downloading everything.

### 🚫 120fps slow-mo: -t must be on INPUT
When using `setpts=N*PTS` for slow-motion, the `-t` flag MUST be on the INPUT, not the output. The filter expands timestamps, so limiting output duration cuts the result short:
```bash
# WRONG — output will be 3 seconds, not 15
ffmpeg -i input.MOV -t 3 -vf "setpts=5*PTS" output.MOV

# CORRECT — 3 seconds input expands to 15 seconds output
ffmpeg -ss 0 -t 3 -i input.MOV -vf "setpts=5*PTS" output.MOV
```

### 🚫 HEVC codec compatibility
Some editors don't handle HEVC well. Convert to H.264 if needed:
```bash
ffmpeg -i input.MOV -c:v libx264 -crf 18 output.MOV
```

### 🚫 Audio sync issues
When combining clips with different audio sample rates, normalize first:
```bash
ffmpeg -i input.MOV -ar 48000 -ac 2 output.MOV
```

## Hero Video Structure

A typical product hero video follows this structure:
1. **Opening** (3-5s): Establishing shot of the product/brand
2. **Action** (5-10s): Product in use / demonstration
3. **Detail** (3-5s): Close-up showing features/benefits
4. **CTA** (3-5s): Call to action with brand/URL

For slow-motion hero videos from 120fps iPhone footage:
- 2-3 seconds raw footage → 10-15 seconds slow-motion
- Target total: 30-45 seconds
- Add text overlays at key moments
- Fade in/out for polish

## Files created during editing
- `clips/` — downloaded source footage
- `frames/` — extracted keyframes for analysis
- `output/` — final edited videos
- `temp/` — intermediate files during editing

## Reference files
- `references/vision-pipeline.py` — reusable script for analyzing frames via model API
- `references/hero-video-template.sh` — template for creating hero videos from 120fps footage