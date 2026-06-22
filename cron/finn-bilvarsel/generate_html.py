#!/usr/bin/env python3
"""Generate FINN bilvarsel HTML from data.json"""

import json
from datetime import datetime, timezone, timedelta
from collections import OrderedDict

MONTHS = {
    1: "januar", 2: "februar", 3: "mars", 4: "april",
    5: "mai", 6: "juni", 7: "juli", 8: "august",
    9: "september", 10: "oktober", 11: "november", 12: "desember"
}

def format_norwegian_date(iso_date):
    if not iso_date:
        return "Ukjent dato"
    try:
        dt = datetime.fromisoformat(iso_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        oslo_offset = timedelta(hours=2)
        dt_local = dt + oslo_offset
        day = dt_local.day
        month = dt_local.month
        year = dt_local.year
        return f"{day}. {MONTHS[month]} {year}"
    except (ValueError, KeyError):
        return iso_date[:10] if len(iso_date) >= 10 else iso_date

def get_date_key(iso_date):
    if not iso_date:
        return "0000-00-00"
    try:
        dt = datetime.fromisoformat(iso_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        oslo_offset = timedelta(hours=2)
        dt_local = dt + oslo_offset
        return dt_local.strftime("%Y-%m-%d")
    except ValueError:
        return iso_date[:10]

def format_price(price):
    if price is None:
        return "?"
    try:
        return f"{int(price):,}".replace(",", " ")
    except (ValueError, TypeError):
        return "?"

def monthly_cost(cost):
    if cost is None or cost == 0:
        return "\u2013"
    return format_price(cost)

def is_tesla_model3(title):
    t = title.lower()
    return "tesla" in t and "model 3" in t

with open("data.json", "r") as f:
    data = json.load(f)

ads = data["ads"]
generated_at = data["generated_at"]
total_ads = data["total_ads"]

tesla_m3_ads = [a for a in ads if is_tesla_model3(a["title"])]
other_ads = [a for a in ads if not is_tesla_model3(a["title"])]

date_groups = OrderedDict()
for a in other_ads:
    dk = get_date_key(a["first_seen"])
    if dk not in date_groups:
        date_groups[dk] = []
    date_groups[dk].append(a)

sorted_dates = sorted(date_groups.keys(), reverse=True)

formatted_gen_time = format_norwegian_date(generated_at)

html_parts = []
html_parts.append("""<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FINN Bilvarsel</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background: #0d1117;
  color: #e6edf3;
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
  line-height: 1.5;
}
h1 {
  font-size: 1.6rem;
  margin-bottom: 4px;
  color: #f0f6fc;
}
.stats {
  color: #8b949e;
  font-size: 0.9rem;
  margin-bottom: 20px;
}
.stats span { display: inline-block; margin-right: 12px; }
.tesla-section {
  background: #0d1b2a;
  border: 1px solid #1f3a5f;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}
.tesla-section h2 {
  color: #58a6ff;
  font-size: 1.2rem;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #1f3a5f;
}
.day-section {
  margin-bottom: 28px;
}
.day-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #30363d;
}
.day-header h2 {
  font-size: 1.1rem;
  color: #f0f6fc;
  white-space: nowrap;
}
.day-header .count {
  color: #8b949e;
  font-size: 0.85rem;
  white-space: nowrap;
}
.day-header .line {
  flex: 1;
  height: 1px;
  background: #21262d;
}
.ad-card {
  background: #161b22;
  border: 1px solid #21262d;
  border-radius: 10px;
  margin-bottom: 20px;
  overflow: hidden;
}
.ad-card:hover {
  border-color: #30363d;
}
.ad-card .img-wrap {
  width: 100%;
  background: #0d1117;
  line-height: 0;
}
.ad-card .img-wrap img {
  width: 100%;
  height: auto;
  display: block;
}
.ad-card .img-wrap .no-img {
  padding: 40px 20px;
  text-align: center;
  color: #484f58;
  font-size: 0.85rem;
  line-height: 1.5;
}
.card-body {
  padding: 14px 16px;
}
.card-title {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
}
.card-title a {
  color: #58a6ff;
  font-size: 1rem;
  font-weight: 600;
  text-decoration: none;
  flex: 1;
}
.card-title a:hover { text-decoration: underline; }
.badge {
  display: inline-block;
  font-size: 0.7rem;
  padding: 2px 7px;
  border-radius: 4px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  margin-top: 2px;
}
.badge-budget {
  background: #1a3a2a;
  color: #3fb950;
}
.badge-nobudget {
  background: #3d1f1f;
  color: #f85149;
}
.card-meta {
  color: #8b949e;
  font-size: 0.82rem;
  margin-bottom: 6px;
}
.card-desc {
  color: #c9d1d9;
  font-size: 0.85rem;
  margin-bottom: 8px;
}
.card-price-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px 16px;
  margin-bottom: 8px;
}
.price-main {
  font-size: 1.1rem;
  font-weight: 700;
  color: #f0f6fc;
}
.price-kind {
  font-size: 0.8rem;
  color: #8b949e;
  background: #21262d;
  padding: 2px 8px;
  border-radius: 4px;
}
.estimates {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 0.8rem;
  color: #8b949e;
}
.estimates strong {
  color: #e6edf3;
}
@media (max-width: 600px) {
  body { padding: 12px; }
  h1 { font-size: 1.3rem; }
  .card-title a { font-size: 0.9rem; }
  .price-main { font-size: 1rem; }
}
</style>
</head>
<body>
""")

now = datetime.now(timezone.utc)
oslo_offset = timedelta(hours=2)
now_oslo = now + oslo_offset
date_str = f"{now_oslo.day}. {MONTHS[now_oslo.month]} {now_oslo.year}"
html_parts.append(f'<h1>\U0001f697 FINN Bilvarsel \u2013 {date_str}</h1>')
html_parts.append(f'<div class="stats"><span>Sist oppdatert: {formatted_gen_time}</span><span>{total_ads} annonser</span></div>')

if tesla_m3_ads:
    html_parts.append('<div class="tesla-section">')
    html_parts.append(f'<h2>\u26a1 Tesla Model 3 ({len(tesla_m3_ads)})</h2>')
    for a in tesla_m3_ads:
        budget = a.get("fits_budget", False)
        badge = '<span class="badge badge-budget">\u2705 Budsjett</span>' if budget else '<span class="badge badge-nobudget">\u26a0\ufe0f Over budsjett</span>'
        img_html = ""
        if a.get("img"):
            img_html = f'<img src="{a["img"]}" alt="{a["title"]}" loading="lazy">'
        else:
            img_html = '<div class="no-img">\U0001f4f7 Ikke tilgjengelig</div>'
        kind_emoji = "\U0001f50b" if a.get("kind") == "elbil" else "\u26fd"
        price = format_price(a.get("price"))
        estimates = a.get("estimates", {})
        e60 = monthly_cost(estimates.get("60"))
        e84 = monthly_cost(estimates.get("84"))
        e96 = monthly_cost(estimates.get("96"))
        html_parts.append(f'''
<div class="ad-card">
  <div class="img-wrap">{img_html}</div>
  <div class="card-body">
    <div class="card-title">
      <a href="{a["link"]}" target="_blank" rel="noopener">{a["title"]}</a>
      {badge}
    </div>
    <div class="card-meta">{a.get("meta", "")}</div>
    <div class="card-desc">{a.get("desc", "")}</div>
    <div class="card-price-row">
      <span class="price-main">{price} kr</span>
      <span class="price-kind">{kind_emoji} {a.get("kind", "")}</span>
    </div>
    <div class="estimates">
      Mnd. kostnad: <strong>{e60} kr</strong> / 5 \u00e5r &middot; <strong>{e84} kr</strong> / 7 \u00e5r &middot; <strong>{e96} kr</strong> / 8 \u00e5r
      <span style="color:#8b949e;font-size:0.75rem;">(50k egenkapital, 7% rente)</span>
    </div>
  </div>
</div>''')
    html_parts.append('</div>')

for dk in sorted_dates:
    ads_in_day = date_groups[dk]
    first_ad = ads_in_day[0]
    date_header = format_norwegian_date(first_ad["first_seen"])
    count = len(ads_in_day)
    html_parts.append(f'<div class="day-section">')
    html_parts.append(f'''
<div class="day-header">
  <h2>{date_header}</h2>
  <span class="count">{count} annonse{"r" if count > 1 else ""}</span>
  <div class="line"></div>
</div>''')
    for a in ads_in_day:
        budget = a.get("fits_budget", False)
        badge = '<span class="badge badge-budget">\u2705 Budsjett</span>' if budget else '<span class="badge badge-nobudget">\u26a0\ufe0f Over budsjett</span>'
        img_html = ""
        if a.get("img"):
            img_html = f'<img src="{a["img"]}" alt="{a["title"]}" loading="lazy">'
        else:
            img_html = '<div class="no-img">\U0001f4f7 Ikke tilgjengelig</div>'
        kind_emoji = "\U0001f50b" if a.get("kind") == "elbil" else "\u26fd"
        price = format_price(a.get("price"))
        estimates = a.get("estimates", {})
        e60 = monthly_cost(estimates.get("60"))
        e84 = monthly_cost(estimates.get("84"))
        e96 = monthly_cost(estimates.get("96"))
        html_parts.append(f'''
<div class="ad-card">
  <div class="img-wrap">{img_html}</div>
  <div class="card-body">
    <div class="card-title">
      <a href="{a["link"]}" target="_blank" rel="noopener">{a["title"]}</a>
      {badge}
    </div>
    <div class="card-meta">{a.get("meta", "")}</div>
    <div class="card-desc">{a.get("desc", "")}</div>
    <div class="card-price-row">
      <span class="price-main">{price} kr</span>
      <span class="price-kind">{kind_emoji} {a.get("kind", "")}</span>
    </div>
    <div class="estimates">
      Mnd. kostnad: <strong>{e60} kr</strong> / 5 \u00e5r &middot; <strong>{e84} kr</strong> / 7 \u00e5r &middot; <strong>{e96} kr</strong> / 8 \u00e5r
      <span style="color:#8b949e;font-size:0.75rem;">(50k egenkapital, 7% rente)</span>
    </div>
  </div>
</div>''')
    html_parts.append('</div>')

html_parts.append("""</body>
</html>""")

output = "\n".join(html_parts)

with open("index.html", "w") as f:
    f.write(output)

print(f"Generated index.html with {total_ads} ads")
print(f"Tesla Model 3: {len(tesla_m3_ads)}")
for dk in sorted_dates:
    ads_in_day = date_groups[dk]
    first_ad = ads_in_day[0]
    date_header = format_norwegian_date(first_ad["first_seen"])
    print(f"  {date_header}: {len(ads_in_day)} ads")
