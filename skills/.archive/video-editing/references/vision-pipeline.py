#!/usr/bin/env python3
"""Vision pipeline for analyzing video frames using model API.

Usage:
    python3 vision-pipeline.py <frames_dir> <clip_name> [api_key] [base_url] [model]

Example:
    python3 vision-pipeline.py /home/user/video/frames IMG_4599

This script analyzes keyframes from a video clip using a vision-capable model.
It encodes frames as base64 and sends them to the model API for description.
"""

import base64
import json
import os
import sys
import requests
from pathlib import Path

def encode_image(image_path):
    """Encode image to base64 data URL"""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{data}"

def analyze_frame(image_path, api_key, base_url, model, prompt="Describe what you see in this video frame in detail. What product is shown? What action is happening? What is the environment/setting?"):
    """Send image to vision model for analysis"""
    data_url = encode_image(image_path)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}}
        ]}],
        "max_tokens": 500
    }
    try:
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_clip_frames(clip_name, frames_dir, api_key, base_url, model, num_frames=3):
    """Analyze multiple frames from a clip"""
    frames = sorted([f for f in os.listdir(frames_dir) if f.startswith(clip_name) and f.endswith(".jpg")])
    
    # Sample frames evenly
    if len(frames) > num_frames:
        indices = [int(i * (len(frames) - 1) / (num_frames - 1)) for i in range(num_frames)]
        frames = [frames[i] for i in indices]
    
    analyses = []
    for frame in frames:
        frame_path = os.path.join(frames_dir, frame)
        print(f"  Analyzing {frame}...", flush=True)
        analysis = analyze_frame(frame_path, api_key, base_url, model)
        if analysis is None:
            analysis = "No analysis available"
        analyses.append({"frame": frame, "analysis": analysis})
    
    return analyses

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 vision-pipeline.py <frames_dir> <clip_name> [api_key] [base_url] [model]")
        sys.exit(1)
    
    frames_dir = sys.argv[1]
    clip_name = sys.argv[2]
    api_key = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("OPENCODE_GO_API_KEY", "")
    base_url = sys.argv[4] if len(sys.argv) > 4 else "https://opencode.ai/zen/go/v1"
    model = sys.argv[5] if len(sys.argv) > 5 else "mimo-v2.5"
    
    if not api_key:
        print("Error: No API key provided. Set OPENCODE_GO_API_KEY or pass as argument.")
        sys.exit(1)
    
    print(f"=== Analyzing {clip_name} ===", flush=True)
    analyses = analyze_clip_frames(clip_name, frames_dir, api_key, base_url, model)
    
    for a in analyses:
        print(f"\n{a['frame']}:", flush=True)
        print(f"  {a['analysis'][:300]}...", flush=True)
    
    # Save results
    output_path = os.path.join(frames_dir, f"{clip_name}_analysis.json")
    with open(output_path, "w") as f:
        json.dump(analyses, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalysis saved to {output_path}")

if __name__ == "__main__":
    main()
