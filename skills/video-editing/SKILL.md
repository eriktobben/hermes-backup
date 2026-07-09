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

**Visual content analysis:**
- Extract frames and view in browser (serve via `python3 -m http.server`)
- Ask user to describe what's in each clip
- Use vision-capable models for analysis (pass images as conversation attachments)

### Pitfall: Vision capability is conversation-attached

Model vision support works for images sent as conversation attachments, not for analyzing files on disk. To analyze local files:
- Extract frames and analyze programmatically (color profiles, edge detection)
- Serve them via HTTP and view in browser
- Ask the user to describe the content

Do NOT assume vision models can "see" local files — they need the image in the conversation context.

## Planning the edit

Before executing, clarify with the user:
1. **Which clips** are relevant (filenames + timestamps)
2. **Target length** (30s? 60s? 2min?)
3. **Music/voiceover** requirements
4. **Text/titles/logo/CTA**
5. **Target platform** (social media, YouTube, website)
6. **Aspect ratio** (9:16 portrait for reels, 16:9 landscape for YouTube)

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
# Slow to 50% (half speed)
ffmpeg -i input.MOV -filter:v "setpts=0.5*PTS" -filter:a "atempo=2.0" output.MOV

# Speed up 2x
ffmpeg -i input.MOV -filter:v "setpts=0.5*PTS" -filter:a "atempo=2.0" output.MOV
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

### 🚫 120fps slow-mo needs special handling
iPhone 120fps clips play at normal speed in most players. To get slow-mo:
```bash
ffmpeg -i input.MOV -vf "setpts=0.25*PTS" -r 30 output_slowmo.MOV
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

## Files created during editing
- `clips/` — downloaded source footage
- `frames/` — extracted keyframes for analysis
- `output/` — final edited videos
- `temp/` — intermediate files during editing