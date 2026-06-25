#!/usr/bin/env python3
"""
AI Model Daily Briefing — retry wrapper with backoff.

If the briefing fails (e.g. provider downtime), retries after 5 min,
then 10 min. Reports the final error if all attempts fail.
Silent (exit 0 with no output) only when there's nothing to say.
"""

import subprocess
import sys
import time

HERMES = "/home/erik/.local/bin/hermes"

PROMPT = """Your task: Produce a daily AI model news briefing in Norwegian, publish it as a here.now page, and deliver the link.

SKILL: The 'here-now' skill is loaded. It provides the publish.sh script.

WORKDIR: Use /home/erik/Projects/ai-daily-briefing/ as working directory. The .herenow/state.json file is there with the slug and API key for permanent publishing.

SLUG: The slug is "whimsy-vow-vjzk" — use --slug whimsy-vow-vjzk when publishing to update the existing page at https://whimsy-vow-vjzk.here.now/ instead of creating a new one.

FRESHNESS RULES (critical):
- Only include news from the LAST 24-48 HOURS. Discard anything older than 2 days.
- This page is UPDATED DAILY with fresh content. Do NOT re-report news that was covered in previous briefings — every day should have fresh news only.
- If nothing new has happened since last time, say "Ingen store nyheter siste døgn" instead of recycling old news.
- When in doubt about whether something is new, err on the side of excluding it.

STEP 1 — Research
Search the web for the LATEST news about AI models — with a strong focus on Chinese AI models.

1. Search for Chinese AI model news — DeepSeek (all versions), Qwen (Alibaba), Kimi (Moonshot AI), Baidu ERNIE, Zhipu GLM/ChatGLM, ByteDance (Doubao/Seed), Baichuan, Yi (01.AI), SenseTime SenseNova, StepFun (MiniMax), Alibaba's Tongyi, Huawei's Pangu, Tencent's Hunyuan, and any new/emerging Chinese models. Include open-source releases, benchmark results, new architectures, API pricing changes, and regulatory news.

2. Search for general AI model news — OpenAI (GPT, o-series), Anthropic (Claude), Google (Gemini, Gemma), Meta (Llama), Mistral, xAI (Grok), and other notable models.

3. Check for new papers on arXiv relevant to model architecture, training efficiency, or benchmarks.

Focus on news from the last 24-48 hours ONLY. If nothing major happened in a category, skip it rather than padding.

STEP 2 — Create HTML
Create /home/erik/Projects/ai-daily-briefing/index.html:
- Dark theme, mobile-friendly, self-contained (no external CSS/JS)
- Norwegian date at top ("25. juni 2026")
- Sections with emoji headers
- Sources cited as hyperlinks
- ~5-10 items unless exceptional news

STEP 3 — Publish
PUBLISH=~/.hermes/skills/productivity/here-now/scripts/publish.sh
bash "$PUBLISH" /home/erik/Projects/ai-daily-briefing/ --slug whimsy-vow-vjzk --client hermes --title "AI Model Briefing - $(date +%d.%m.%Y)"

STEP 4 — Deliver
Output ONLY the link + a 1-line teaser (no full content):
🧠 **AI Model Briefing — <dato>**
<url>
> <kort teaser>
"""


def run_briefing() -> tuple[int, str]:
    """Run the briefing and return (exit_code, combined_output)."""
    try:
        proc = subprocess.run(
            [
                HERMES,
                "chat", "-q", PROMPT,
                "-s", "here-now",
                "-t", "web,search,terminal",
                "-Q",
                "--yolo",
            ],
            capture_output=True,
            text=True,
            timeout=600,  # 10 min max per attempt
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        combined = out
        if err:
            combined += "\n" + err
        return proc.returncode, combined
    except subprocess.TimeoutExpired:
        return 1, "ERROR: Briefing timed out after 10 minutes"
    except FileNotFoundError:
        return 1, f"ERROR: hermes not found at {HERMES}"
    except Exception as e:
        return 1, f"ERROR: {e}"


attempts = [
    (0, "Første forsøk"),
    (300, "Backoff 5 min → andre forsøk"),     # 5 min
    (600, "Backoff 10 min → tredje forsøk"),   # 10 min
]

for delay, label in attempts:
    if delay > 0:
        print(f"[{label}]", flush=True)
        time.sleep(delay)

    exit_code, output = run_briefing()

    if exit_code == 0:
        # Success — relay the output and exit cleanly
        if output:
            print(output)
        sys.exit(0)
    else:
        # Failure — log and continue to next attempt
        print(f"❌ {label} feilet (exit code {exit_code})", flush=True)
        # Show the actual error (truncated to avoid noise)
        error_lines = output.strip().split("\n")
        short_error = "\n".join(error_lines[-10:])  # last 10 lines
        print(f"   Siste feil: {short_error[:500]}", flush=True)

# All attempts failed
print()
print("=" * 50)
print("❌❌❌ AI Model Daily Briefing — ALLE FORSØK FEILET")
print("=" * 50)
print()
print("Kjøreplan:")
for delay, label in attempts:
    status = "❌" if delay > 0 else "✅" if delay == 0 else "❌"
    print(f"  {status} {label}")
print()
print("Siste feilmelding:")
print(output[:2000] if output else "(ingen output)")
sys.exit(1)
