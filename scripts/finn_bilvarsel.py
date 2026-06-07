#!/usr/bin/env python3
import json
import math
import re
from html import unescape
from pathlib import Path

import requests

STATE_PATH = Path('/home/erik/.hermes/cron/state/finn_bilvarsel_seen.json')
STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Hermes car alert)"}

# User prefs
EGENKAPITAL = 50_000
RENTE_AARLIG = 0.07
TERMS = [60, 84, 96]  # 5, 7, 8 years
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
        return {"seen": []}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"seen": []}


def save_state(seen_ids):
    STATE_PATH.write_text(json.dumps({"seen": sorted(seen_ids)}, ensure_ascii=False, indent=2))


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


def fmt_kr(v):
    return f"{int(v):,}".replace(',', ' ') + " kr"


def main():
    st = load_state()
    seen = set(st.get("seen", []))

    all_items = []
    for s in SEARCHES:
        items = parse_search(s["url"])
        for it in items:
            fuel_kind = classify_fuel(it)
            if fuel_kind == "elbil":
                it["kind"] = "elbil"
                all_items.append(it)
                continue
            if fuel_kind == "bensin" and qualifies_bensin(it):
                it["kind"] = "bensin"
                all_items.append(it)
                continue

    if not seen:
        save_state({x["id"] for x in all_items})
        print(f"Bilvarsel aktivert. Første synk lagret {len(all_items)} annonser (ingen varsling på første kjøring).")
        return

    new_items = [x for x in all_items if x["id"] not in seen]
    seen.update([x["id"] for x in all_items])
    save_state(seen)

    if not new_items:
        return  # silent when nothing new

    lines = [f"🚗 FINN-varsel: {len(new_items)} nye annonser som matcher filtrene dine"]

    for it in new_items[:12]:
        price = enrich_price(it["link"])
        if not price:
            continue
        principal = max(0, price - EGENKAPITAL)
        estimates = {m: annuity_monthly(principal, m, RENTE_AARLIG) for m in TERMS}
        fits = any(v <= MAX_MND for v in estimates.values())
        fit_mark = "✅" if fits else "⚠️"

        lines.append("")
        lines.append(f"{fit_mark} {it['title']} ({it['kind']})")
        lines.append(f"Pris: {fmt_kr(price)}")
        lines.append(
            f"Estimat lån (50 000 egenkapital, 7% rente): 5 år {fmt_kr(estimates[60])}/mnd · 7 år {fmt_kr(estimates[84])}/mnd · 8 år {fmt_kr(estimates[96])}/mnd"
        )
        lines.append(f"Meta: {it['meta']}")
        if it.get("desc"):
            lines.append(f"Info: {it['desc']}")
        lines.append(it["link"])
        if it.get("img"):
            lines.append(f"![annonsebilde]({it['img']})")

    if len(new_items) > 12:
        lines.append("")
        lines.append(f"... og {len(new_items)-12} flere nye treff.")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
