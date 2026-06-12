#!/usr/bin/env python3
"""
Collect FINN car ads matching filters (elbil + bensin med registerkjede).
Maintains a rolling 10-day window in state. Outputs JSON for agent consumption.
"""
import json
import math
import re
from datetime import datetime, timezone, timedelta
from html import unescape
from pathlib import Path

import requests

STATE_PATH = Path('/home/erik/.hermes/cron/state/finn_bilvarsel_data.json')
HEADERS = {"User-Agent": "Mozilla/5.0 (Hermes car alert)"}

# User preferences
EGENKAPITAL = 50_000
RENTE_AARLIG = 0.07
TERMS = [60, 84, 96]  # months
MAX_MND = 2500
PRICE_TO = 260000

SEARCHES = [
    {
        "name": "Biler (automat, nyeste først)",
        "url": f"https://www.finn.no/mobility/search/car?gearbox=2&sales_form=1&price_to={PRICE_TO}&sort=PUBLISHED_DESC",
    },
]

BENSIN_KEYWORDS = [
    "registerkjede",
    "reg.kjede",
    "registerreim byttet",
    "ny registerreim",
    "regreim byttet",
    "vannpumpe byttet",
]
EXCLUDE_WORDS = ["leasing", "leiekampanje", "firmaleasing", "0% rente"]


def annuity_monthly(principal: float, months: int, annual_rate: float) -> int:
    if principal <= 0:
        return 0
    r = annual_rate / 12
    if r <= 0:
        return math.ceil(principal / months)
    return math.ceil(principal * (r / (1 - (1 + r) ** (-months))))


def parse_search(url: str):
    t = requests.get(url, headers=HEADERS, timeout=30).text
    blocks = re.findall(r'<article class="relative isolate sf-search-ad.*?</article>', t, flags=re.S)
    out = []
    for b in blocks:
        def g(p):
            m = re.search(p, b, flags=re.S)
            return unescape(m.group(1).strip()) if m else ""

        link = g(r'href="(https://www\.finn\.no/mobility/item/\d+)"')
        if not link:
            continue
        title = g(r'<h2[^>]*>(.*?)</h2>')
        desc = g(r'<div class="text-caption mb-4 s-text-subtle truncate block max-w-full ">(.*?)</div>')
        meta = g(r'<span class="text-caption font-bold inline-block mb-8">(.*?)</span>')
        img = g(r'<img[^>]+src="(https://images\.finncdn\.no/dynamic/480w/item/[^"]+)"')
        ad_id = link.rsplit('/', 1)[-1]
        text_blob = (title + " " + desc).lower()
        if any(w in text_blob for w in EXCLUDE_WORDS):
            continue
        out.append({"id": ad_id, "link": link, "title": title, "desc": desc, "meta": meta, "img": img})

    seen = set()
    uniq = []
    for x in out:
        if x["id"] in seen:
            continue
        seen.add(x["id"])
        uniq.append(x)
    return uniq


def enrich_price(link: str):
    t = requests.get(link, headers=HEADERS, timeout=30).text
    for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, flags=re.S):
        try:
            obj = json.loads(s)
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("@type") == "Product":
            offers = obj.get("offers") or {}
            price = offers.get("price")
            if isinstance(price, (int, float)):
                return int(price)
    m = re.search(r'"price"\s*:\s*(\d{4,8})', t)
    if m:
        return int(m.group(1))
    return None


def load_state():
    if not STATE_PATH.exists():
        return {"ads": {}}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"ads": {}}


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def classify_fuel(item):
    meta = (item.get("meta", "") or "").lower()
    if " ∙ el ∙" in f" {meta} ":
        return "elbil"
    if "hybrid" in meta:
        return "hybrid"
    if "bensin" in meta:
        return "bensin"
    return "annet"


def qualifies_bensin(item):
    blob = (item.get("title", "") + " " + item.get("desc", "")).lower()
    return any(k in blob for k in BENSIN_KEYWORDS)


def main():
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    state = load_state()
    ads = state.get("ads", {})

    # Scrape current FINN results
    all_found = []
    for s in SEARCHES:
        items = parse_search(s["url"])
        for it in items:
            fuel_kind = classify_fuel(it)
            if fuel_kind == "elbil":
                it["kind"] = "elbil"
                all_found.append(it)
                continue
            if fuel_kind == "bensin" and qualifies_bensin(it):
                it["kind"] = "bensin"
                all_found.append(it)
                continue

    # Merge current results into state
    found_ids = set()
    for it in all_found:
        aid = it["id"]
        found_ids.add(aid)
        if aid in ads:
            ads[aid]["last_seen"] = now_iso
            ads[aid]["title"] = it["title"]
            ads[aid]["meta"] = it["meta"]
            ads[aid]["desc"] = it["desc"]
            ads[aid]["img"] = it["img"]
            ads[aid]["link"] = it["link"]
        else:
            price = enrich_price(it["link"])
            ads[aid] = {
                "id": aid,
                "title": it["title"],
                "link": it["link"],
                "desc": it["desc"],
                "meta": it["meta"],
                "img": it["img"],
                "kind": it["kind"],
                "price": price,
                "first_seen": now_iso,
                "last_seen": now_iso,
            }

    # Purge ads first seen more than 10 days ago
    cutoff = now - timedelta(days=10)
    to_remove = []
    for aid, ad in ads.items():
        first = ad.get("first_seen", "")
        try:
            ft = datetime.fromisoformat(first)
            if ft < cutoff:
                to_remove.append(aid)
        except (ValueError, TypeError):
            to_remove.append(aid)
    for aid in to_remove:
        del ads[aid]

    state["ads"] = ads
    save_state(state)

    # Sort newest first
    sorted_ads = sorted(ads.values(), key=lambda x: x.get("first_seen", ""), reverse=True)

    # Enrich with loan estimates
    for ad in sorted_ads:
        price = ad.get("price")
        if price and isinstance(price, (int, float)):
            principal = max(0, int(price) - EGENKAPITAL)
            estimates = {}
            for m in TERMS:
                estimates[str(m)] = annuity_monthly(principal, m, RENTE_AARLIG)
            fits = any(v <= MAX_MND for v in estimates.values())
            ad["estimates"] = estimates
            ad["fits_budget"] = fits
        else:
            ad["estimates"] = {}
            ad["fits_budget"] = False

    # Detect new ads since last run (for agent to mention)
    prev_seen_ids = set(state.get("prev_seen_ids", []))
    current_ids = {ad["id"] for ad in sorted_ads}
    new_ids = current_ids - prev_seen_ids
    state["prev_seen_ids"] = sorted(current_ids)
    save_state(state)

    print(json.dumps({
        "generated_at": now_iso,
        "total_ads": len(sorted_ads),
        "ads": sorted_ads,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
