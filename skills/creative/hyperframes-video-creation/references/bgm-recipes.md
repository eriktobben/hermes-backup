# BGM Recipes for HyperFrames

All recipes use ffmpeg synthesis. Adjust `d=DURATION` to match your video length.

## Recipe 1: Warm Ambient Pad (C Major)
Best for: Product launches, home/lifestyle brands, cozy content.
```bash
ffmpeg -y \
  -f lavfi -i "anoisesrc=d=DURATION:c=pink:a=0.08" \
  -f lavfi -i "sine=frequency=261.63:duration=DURATION" \
  -f lavfi -i "sine=frequency=329.63:duration=DURATION" \
  -f lavfi -i "sine=frequency=392.00:duration=DURATION" \
  -f lavfi -i "sine=frequency=196.00:duration=DURATION" \
  -filter_complex " \
    [1]volume=0.15[c]; [2]volume=0.12[e]; [3]volume=0.12[g]; \
    [4]volume=0.10[sub]; [0]volume=0.06[ns]; \
    [ns][c][e][g][sub]amix=inputs=5:duration=first:dropout_transition=0, \
    aecho=0.8:0.5:60:0.25, highpass=f=60, volume=3.0, \
    afade=t=in:d=1.5, afade=t=out:st=STARTFADE:d=4 \
  " -ac 2 assets/bgm.mp3
```
C4+E4+G4 (C major), sub-bass on G3, pink noise texture, echo for depth.

## Recipe 2: Ethereal / Dreamy (Am7)
Best for: Beauty, wellness, wellness brands.
```bash
ffmpeg -y \
  -f lavfi -i "anoisesrc=d=DURATION:c=pink:a=0.05" \
  -f lavfi -i "sine=frequency=220.00:duration=DURATION" \
  -f lavfi -i "sine=frequency=261.63:duration=DURATION" \
  -f lavfi -i "sine=frequency=329.63:duration=DURATION" \
  -f lavfi -i "sine=frequency=392.00:duration=DURATION" \
  -filter_complex " \
    [1]volume=0.12[a]; [2]volume=0.10[c]; [3]volume=0.10[e]; \
    [4]volume=0.08[g]; [0]volume=0.04[ns]; \
    [ns][a][c][e][g]amix=inputs=5:duration=first:dropout_transition=0, \
    aecho=0.8:0.6:80:0.3, highpass=f=80, volume=3.5, \
    afade=t=in:d=2, afade=t=out:st=STARTFADE:d=4 \
  " -ac 2 assets/bgm.mp3
```
A3+C4+E4+G4 (Am7), more reverb, softer.

## Recipe 3: Upbeat / Energetic
Best for: Tech launches, fitness, youth brands.
```bash
ffmpeg -y \
  -f lavfi -i "anoisesrc=d=DURATION:c=pink:a=0.04" \
  -f lavfi -i "sine=frequency=329.63:duration=DURATION" \
  -f lavfi -i "sine=frequency=440.00:duration=DURATION" \
  -f lavfi -i "sine=frequency=523.25:duration=DURATION" \
  -f lavfi -i "sine=frequency=164.81:duration=DURATION" \
  -filter_complex " \
    [1]volume=0.10[e]; [2]volume=0.08[a]; [3]volume=0.08[c5]; \
    [4]volume=0.06[sub]; [0]volume=0.03[ns]; \
    [ns][e][a][c5][sub]amix=inputs=5:duration=first:dropout_transition=0, \
    aecho=0.7:0.4:40:0.2, highpass=f=100, volume=4.0, \
    afade=t=in:d=1, afade=t=out:st=STARTFADE:d=3 \
  " -ac 2 assets/bgm.mp3
```
Higher register, brighter, more energy.

## Common pitfalls
- **Raw sines at 0.01-0.04 amplitude produce ~17kbps audio that is inaudible.** Always add `volume=3.0` or higher amplification.
- **WAV output sometimes renders at very low bitrate.** Use MP3 output (`assets/bgm.mp3`) for more reliable encoding.
- **Always verify after render**: `ffprobe renders/video.mp4 | grep Audio` — expect 128+ kbps.
- **Set `data-volume="0.5"`** on the audio element for adequate playback volume.
