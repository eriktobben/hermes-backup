import json
from datetime import datetime

MONTHS_NB = ['', 'januar', 'februar', 'mars', 'april', 'mai', 'juni',
             'juli', 'august', 'september', 'oktober', 'november', 'desember']

def norwegian_date(iso_str):
    d = datetime.fromisoformat(iso_str)
    return f"{d.day}. {MONTHS_NB[d.month]} {d.year}"

def norwegian_date_short(iso_str):
    d = datetime.fromisoformat(iso_str)
    return f"{d.day}. {MONTHS_NB[d.month]} {d.year}"

def format_price(price):
    if price is None:
        return "—"
    return f"{price:,.0f}".replace(",", " ")

def card_html(ad):
    budget_icon = "✅" if ad['fits_budget'] else "⚠️"
    budget_class = "budget-ok" if ad['fits_budget'] else "budget-warn"
    budget_text = "Innenfor budsjett" if ad['fits_budget'] else "Over budsjett"
    
    price_str = format_price(ad['price'])
    
    kind_icon = "🔋" if ad['kind'] == 'elbil' else "⛽"
    kind_label = "Elbil" if ad['kind'] == 'elbil' else "Bensin"
    
    estimates_html = ""
    if ad.get('estimates') and len(ad['estimates']) > 0:
        est = ad['estimates']
        e60 = est.get('60')
        e84 = est.get('84')
        e96 = est.get('96')
        parts = []
        if e60 is not None:
            parts.append(f'<span class="est">5 år: <strong>{format_price(e60)} kr/mnd</strong></span>')
        if e84 is not None:
            parts.append(f'<span class="est">7 år: <strong>{format_price(e84)} kr/mnd</strong></span>')
        if e96 is not None:
            parts.append(f'<span class="est">8 år: <strong>{format_price(e96)} kr/mnd</strong></span>')
        if parts:
            estimates_html = '<div class="estimates">' + ' · '.join(parts) + '</div>'
    
    img_html = ""
    if ad.get('img') and ad['img'].strip():
        img_html = f'<img src="{ad["img"]}" alt="{ad["title"]}" loading="lazy" onerror="this.parentElement.style.display=\'none\'">'
    
    desc_html = f'<p class="desc">{ad["desc"]}</p>' if ad.get('desc') else ''
    
    return f'''
    <div class="card">
      <div class="card-header">
        <span class="{budget_class}">{budget_icon} {budget_text}</span>
        <span class="kind-badge">{kind_icon} {kind_label}</span>
      </div>
      <a href="{ad['link']}" target="_blank" rel="noopener" class="card-title">{ad['title']}</a>
      <div class="card-price">{price_str} kr</div>
      <div class="meta">{ad.get('meta', '')}</div>
      {estimates_html}
      {desc_html}
      {('<div class="img-wrap">' + img_html + '</div>') if img_html else ''}
    </div>'''

with open('/home/erik/.hermes/cron/finn-bilvarsel/data.json') as f:
    data = json.load(f)

ads = data['ads']
total = len(ads)
generated = data['generated_at']

# Group by date
from collections import defaultdict
by_date = defaultdict(list)
for ad in ads:
    d = ad['first_seen'][:10]
    by_date[d].append(ad)

# Separate Tesla Model 3
tesla_m3 = [ad for ad in ads if 'Tesla Model 3' in ad['title']]
other_ads = [ad for ad in ads if 'Tesla Model 3' not in ad['title']]

# Re-group non-Tesla by date
by_date_other = defaultdict(list)
for ad in other_ads:
    d = ad['first_seen'][:10]
    by_date_other[d].append(ad)

sorted_dates = sorted(by_date_other.keys(), reverse=True)

# Build date sections
date_sections = ""
for d in sorted_dates:
    day_ads = by_date_other[d]
    dt = datetime.fromisoformat(d)
    nb_date = f"{dt.day}. {MONTHS_NB[dt.month]} {dt.year}"
    count_text = f"{len(day_ads)} annonse{'r' if len(day_ads) != 1 else ''}"
    
    cards_html = "".join(card_html(ad) for ad in day_ads)
    
    date_sections += f'''
    <div class="day-section">
      <div class="day-header">
        <h2 class="day-title">{nb_date}</h2>
        <span class="day-count">{count_text}</span>
      </div>
      <div class="day-divider"></div>
      {cards_html}
    </div>'''

# Tesla Model 3 section
tesla_section = ""
if tesla_m3:
    cards_tesla = "".join(card_html(ad) for ad in tesla_m3)
    tesla_section = f'''
    <div class="day-section tesla-section">
      <div class="day-header tesla-header">
        <h2 class="day-title">⚡ Tesla Model 3</h2>
        <span class="day-count">{len(tesla_m3)} annonse{'r' if len(tesla_m3) != 1 else ''}</span>
      </div>
      <div class="day-divider tesla-divider"></div>
      {cards_tesla}
    </div>'''

today_dt = datetime.fromisoformat(generated)
today_str = f"{today_dt.day}. {MONTHS_NB[today_dt.month]} {today_dt.year}"
time_str = today_dt.strftime("%H:%M")

html = f'''<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FINN Bilvarsel – {today_str}</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  background: #0d1117;
  color: #e6edf3;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  line-height: 1.6;
  padding: 16px;
}}
.container {{
  max-width: 720px;
  margin: 0 auto;
}}
.header {{
  text-align: center;
  padding: 24px 0 20px;
  border-bottom: 1px solid #21262d;
  margin-bottom: 28px;
}}
.header h1 {{
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 6px;
}}
.header .subtitle {{
  color: #8b949e;
  font-size: 0.9rem;
}}
.header .subtitle span {{
  color: #58a6ff;
}}
.day-section {{
  margin-bottom: 32px;
}}
.day-header {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8px;
}}
.day-title {{
  font-size: 1.15rem;
  font-weight: 600;
  color: #f0f6fc;
}}
.day-count {{
  font-size: 0.85rem;
  color: #8b949e;
  background: #161b22;
  padding: 2px 10px;
  border-radius: 12px;
}}
.day-divider {{
  height: 3px;
  background: linear-gradient(90deg, #30363d, #21262d);
  border-radius: 2px;
  margin-bottom: 18px;
}}
.tesla-section .tesla-header .day-title {{
  color: #58a6ff;
}}
.tesla-divider {{
  background: linear-gradient(90deg, #1f6feb, #0d1117);
}}
.card {{
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}}
.card-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.8rem;
}}
.budget-ok {{ color: #3fb950; }}
.budget-warn {{ color: #d29922; }}
.kind-badge {{
  background: #0d1117;
  padding: 2px 10px;
  border-radius: 10px;
  border: 1px solid #30363d;
  font-size: 0.78rem;
}}
.card-title {{
  display: block;
  font-size: 1.1rem;
  font-weight: 600;
  color: #58a6ff;
  text-decoration: none;
  margin-bottom: 6px;
  line-height: 1.3;
}}
.card-title:hover {{ text-decoration: underline; }}
.card-price {{
  font-size: 1.25rem;
  font-weight: 700;
  color: #f0f6fc;
  margin-bottom: 4px;
}}
.meta {{
  font-size: 0.82rem;
  color: #8b949e;
  margin-bottom: 8px;
}}
.estimates {{
  font-size: 0.82rem;
  color: #8b949e;
  margin-bottom: 8px;
  line-height: 1.5;
}}
.estimates .est {{
  display: inline-block;
}}
.estimates strong {{
  color: #e6edf3;
}}
.desc {{
  font-size: 0.82rem;
  color: #8b949e;
  margin-bottom: 10px;
  font-style: italic;
}}
.img-wrap {{
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  margin-top: 8px;
}}
.img-wrap img {{
  width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
}}
@media (max-width: 480px) {{
  body {{ padding: 10px; }}
  .header h1 {{ font-size: 1.3rem; }}
  .card {{ padding: 12px; }}
  .card-title {{ font-size: 1rem; }}
}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🚗 FINN Bilvarsel – {today_str}</h1>
    <div class="subtitle">Generert {time_str} · <span>{total} annonser</span></div>
  </div>
  {tesla_section}
  {date_sections}
</div>
</body>
</html>'''

with open('/home/erik/.hermes/cron/finn-bilvarsel/index.html', 'w') as f:
    f.write(html)

print(f"HTML generated: {total} ads, {len(tesla_m3)} Tesla Model 3, {len(sorted_dates)} dag(er)")
