#!/bin/bash
# Hero Video Creation Template
# Creates a polished slow-motion hero video from 120fps iPhone footage
#
# Usage: 
#   1. Set CLIPS_DIR and OUTPUT_DIR variables
#   2. Edit the clip selections and text overlays
#   3. Run: bash create-hero.sh

set -e

# === CONFIGURATION ===
CLIPS_DIR="/path/to/clips"
FRAMES_DIR="/path/to/frames"
OUTPUT_DIR="/path/to/output"
TEMP_DIR="/path/to/temp"

# Slow-motion factor (120fps → 24fps = 5x slowdown)
SLOW_FACTOR=5
OUTPUT_FPS=24

# === CLIP SELECTION ===
# Format: "INPUT_FILE START_TIME DURATION OUTPUT_NAME TEXT"
# Adjust these based on your footage analysis

declare -a CLIPS=(
    # Opening shot (empty product)
    "$CLIPS_DIR/IMG_XXXX.MOV 0 2 01_opening 'Brand Name'"
    
    # Action shot (product in use)
    "$CLIPS_DIR/IMG_YYYY.MOV 3 3 02_action 'Key Feature'"
    
    # Detail shot (close-up)
    "$CLIPS_DIR/IMG_ZZZZ.MOV 2 2 03_detail 'Benefit Text'"
    
    # CTA shot (final)
    "$CLIPS_DIR/IMG_WWWW.MOV 5 2 04_cta 'website.no'"
)

# === FUNCTIONS ===

trim_and_slow() {
    local input="$1" start="$2" duration="$3" output="$4" factor="$5" fps="$6"
    
    ffmpeg -y -ss "$start" -t "$duration" -i "$input" \
        -vf "setpts=${factor}*PTS,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
        -r "$fps" -c:v libx264 -preset medium -crf 18 -an \
        "$output" 2>/dev/null
}

add_text() {
    local input="$1" text="$2" output="$3"
    local fontsize=$4:-48
    local y_pos=$5:-100
    
    ffmpeg -y -i "$input" \
        -vf "drawtext=text='${text}':fontsize=${fontsize}:fontcolor=white:x=(w-text_w)/2:y=h-${y_pos}:enable='between(t,2,8)':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" \
        -c:v libx264 -preset medium -crf 18 "$output" 2>/dev/null
}

# === MAIN ===

mkdir -p "$TEMP_DIR" "$OUTPUT_DIR"

echo "=== Step 1: Trim and apply slow-motion ==="
for clip in "${CLIPS[@]}"; do
    read -r input start duration name text <<< "$clip"
    echo "Processing $name..."
    trim_and_slow "$input" "$start" "$duration" "$TEMP_DIR/${name}_raw.MOV" "$SLOW_FACTOR" "$OUTPUT_FPS"
done

echo "=== Step 2: Add text overlays ==="
for clip in "${CLIPS[@]}"; do
    read -r input start duration name text <<< "$clip"
    echo "Adding text to $name..."
    add_text "$TEMP_DIR/${name}_raw.MOV" "$text" "$TEMP_DIR/${name}_text.MOV"
done

echo "=== Step 3: Concatenate ==="
> "$TEMP_DIR/concat.txt"
for clip in "${CLIPS[@]}"; do
    read -r input start duration name text <<< "$clip"
    echo "file '${name}_text.MOV'" >> "$TEMP_DIR/concat.txt"
done

ffmpeg -y -f concat -safe 0 -i "$TEMP_DIR/concat.txt" \
    -c:v libx264 -preset medium -crf 18 \
    "$TEMP_DIR/combined.MOV" 2>/dev/null

echo "=== Step 4: Add fades ==="
DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$TEMP_DIR/combined.MOV")
FADE_OUT=$(python3 -c "print(f'{float($DUR)-2:.1f}')")

ffmpeg -y -i "$TEMP_DIR/combined.MOV" \
    -vf "fade=t=in:st=0:d=1.5,fade=t=out:st=$FADE_OUT:d=2" \
    -c:v libx264 -preset medium -crf 18 \
    "$OUTPUT_DIR/hero_video.MOV" 2>/dev/null

echo "=== Done! ==="
ls -lh "$OUTPUT_DIR/hero_video.MOV"
FINAL_DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUTPUT_DIR/hero_video.MOV")
echo "Final duration: ${FINAL_DUR}s"
