#!/usr/bin/env bash
# Generate ambient BGM for HyperFrames videos using ffmpeg.
# Usage: ./scripts/gen-bgm.sh <output_path> [duration]
# Example: ./scripts/gen-bgm.sh assets/bgm.wav 38

set -e

OUTPUT="${1:-assets/bgm.wav}"
DURATION="${2:-38}"

echo "Generating ${DURATION}s ambient BGM → ${OUTPUT}"

ffmpeg -y \
  -f lavfi -i "anoisesrc=d=${DURATION}:c=pink:a=0.02" \
  -f lavfi -i "sine=frequency=261.63:duration=${DURATION}" \
  -f lavfi -i "sine=frequency=329.63:duration=${DURATION}" \
  -f lavfi -i "sine=frequency=392.00:duration=${DURATION}" \
  -filter_complex "[1]volume=0.04[ch1];[2]volume=0.035[ch2];[3]volume=0.035[ch3];[0]volume=0.015[noise];[noise][ch1][ch2][ch3]amix=inputs=4:duration=first:dropout_transition=0,afade=t=in:d=2,afade=t=out:d=3" \
  -ac 2 "${OUTPUT}"

echo "Done: $(du -h "${OUTPUT}" | cut -f1)"
