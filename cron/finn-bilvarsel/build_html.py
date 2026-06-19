import json, os

with open('/home/erik/.hermes/cron/finn-bilvarsel/data.json') as f:
    data = json.load(f)

# Embed the whole data as JS
data_json = json.dumps(data, ensure_ascii=False)

# Norwegian month names
months = ['januar', 'februar', 'mars', 'april', 'mai', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'desember']

def norwegian_date(iso_str):
    """Convert ISO date to Norwegian format: '19. juni 2026'"""
    parts = iso_str[:10].split('-')
    day = int(parts[2])
    month = int(parts[1])
    year = parts[0]
    return f"{day}. {months[month-1]} {year}"

def format_price(price):
    """Format price with spaces: 169 000 kr"""
    if price is None:
        return "—"
    s = f"{int(price):,}".replace(',', ' ')
    return f"{s} kr"

generated_at = data['generated_at']
total = data['total_ads']

html = f'''<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FINN Bilvarsel – {norwegian_date(generated_at)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  background: #0d1117;
  color: #e6edf3;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.5;
  padding: 20px;
}}
.container {{ max-width: 800px; margin: 0 auto; }}
h1 {{
  font-size: 1.6em;
  margin-bottom: 6px;
  color: #f0f6fc;
}}
.subtitle {{
  color: #8b949e;
  font-size: 0.9em;
  margin-bottom: 24px;
}}
.tesla-section {{
  background: #0a1929;
  border: 1px solid #1a4a7a;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}}
.tesla-section h2 {{
  color: #58a6ff;
  font-size: 1.2em;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.day-section {{
  margin-bottom: 32px;
}}
.day-header {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-bottom: 8px;
  margin-bottom: 16px;
  border-bottom: 2px solid #30363d;
}}
.day-header h3 {{
  font-size: 1.1em;
  color: #f0f6fc;
}}
.day-header .count {{
  color: #8b949e;
  font-size: 0.85em;
}}
.card {{
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
  transition: border-color 0.15s;
}}
.card:hover {{
  border-color: #58a6ff;
}}
.card-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 8px;
}}
.card-title {{
  font-size: 1.05em;
  font-weight: 600;
  color: #58a6ff;
  text-decoration: none;
  word-break: break-word;
}}
.card-title:hover {{
  text-decoration: underline;
}}
.budget-badge {{
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75em;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}}
.budget-ok {{
  background: #0a2e1a;
  color: #3fb950;
  border: 1px solid #238636;
}}
.budget-warn {{
  background: #2e1a0a;
  color: #d29922;
  border: 1px solid #9e6a03;
}}
.meta-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-bottom: 8px;
  font-size: 0.88em;
  color: #8b949e;
}}
.meta-row .tag {{
  color: #e6edf3;
}}
.price {{
  font-size: 1.15em;
  font-weight: 700;
  color: #f0f6fc;
  margin-bottom: 6px;
}}
.estimates {{
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 0.82em;
}}
.est-item {{
  background: #0d1117;
  border: 1px solid #21262d;
  border-radius: 6px;
  padding: 4px 10px;
  text-align: center;
}}
.est-item .label {{
  color: #8b949e;
  font-size: 0.85em;
}}
.est-item .value {{
  color: #f0f6fc;
  font-weight: 600;
}}
.desc {{
  color: #c9d1d9;
  font-size: 0.9em;
  margin-bottom: 10px;
  line-height: 1.4;
}}
.img-wrap {{
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: #0d1117;
}}
.img-wrap img {{
  width: 100%;
  height: auto;
  display: block;
}}
.img-wrap img[src=""], .img-wrap img:not([src]) {{
  display: none;
}}
.price-missing {{
  color: #8b949e;
  font-style: italic;
}}
@media (max-width: 600px) {{
  body {{ padding: 12px; }}
  h1 {{ font-size: 1.3em; }}
  .estimates {{ flex-wrap: wrap; gap: 6px; }}
}}
</style>
</head>
<body>
<div class="container" id="app"></div>
<script>
const DATA = {data_json};

function norwegianDate(iso) {{
  const months = ['januar', 'februar', 'mars', 'april', 'mai', 'juni', 'juli', 'august', 'september', 'oktober', 'november', 'desember'];
  const parts = iso.slice(0,10).split('-');
  return parseInt(parts[2]) + '. ' + months[parseInt(parts[1])-1] + ' ' + parts[0];
}}

function formatPrice(p) {{
  if (p === null || p === undefined) return '—';
  return p.toString().replace(/\B(?=(\d{{3}})+(?!\d))/g, ' ') + ' kr';
}}

function render() {{
  const ads = DATA.ads;
  const generated = DATA.generated_at;
  
  // Group by date
  const byDate = {{}};
  ads.forEach(a => {{
    const d = a.first_seen.slice(0,10);
    if (!byDate[d]) byDate[d] = [];
    byDate[d].push(a);
  }});
  
  const sortedDates = Object.keys(byDate).sort((a,b) => b.localeCompare(a));
  
  // Separate Tesla Model 3
  const tesla3 = ads.filter(a => a.title.includes('Tesla Model 3'));
  
  let html = '';
  
  // Header
  html += `<h1>🚗 FINN Bilvarsel – ${{norwegianDate(generated)}}</h1>`;
  html += `<p class="subtitle">Generert ${{new Date(generated).toLocaleString('nb-NO', {{timeZone: 'UTC', dateStyle: 'long', timeStyle: 'short'}})}} · ${{ads.length}} annonser fordelt på ${{sortedDates.length}} dager</p>`;
  
  // Tesla Model 3 section
  if (tesla3.length > 0) {{
    html += `<div class="tesla-section"><h2>⚡ Tesla Model 3 (${{tesla3.length}})</h2>`;
    html += renderCards(tesla3);
    html += `</div>`;
  }}
  
  // Day sections
  sortedDates.forEach(date => {{
    const dayAds = byDate[date];
    html += `<div class="day-section">`;
    html += `<div class="day-header"><h3>${{norwegianDate(date)}}</h3><span class="count">${{dayAds.length}} annonse${{dayAds.length !== 1 ? 'r' : ''}}</span></div>`;
    html += renderCards(dayAds);
    html += `</div>`;
  }});
  
  document.getElementById('app').innerHTML = html;
}}

function renderCards(ads) {{
  let html = '';
  ads.forEach(a => {{
    const budgetClass = a.fits_budget ? 'budget-ok' : 'budget-warn';
    const budgetLabel = a.fits_budget ? '✅ Budsjett' : '⚠️ Over budsjett';
    
    const priceStr = formatPrice(a.price);
    const hasEstimates = a.estimates && a.estimates['60'] !== undefined;
    
    let estHtml = '';
    if (hasEstimates && a.estimates['60'] > 0) {{
      estHtml = `<div class="estimates">
        <div class="est-item"><div class="label">5 år</div><div class="value">${{formatPrice(a.estimates['60'])}}/mnd</div></div>
        <div class="est-item"><div class="label">7 år</div><div class="value">${{formatPrice(a.estimates['84'])}}/mnd</div></div>
        <div class="est-item"><div class="label">8 år</div><div class="value">${{formatPrice(a.estimates['96'])}}/mnd</div></div>
      </div>`;
    }}
    
    const kindLabel = a.kind === 'elbil' ? '⚡ Elbil' : '⛽ Bensin';
    
    html += `<div class="card">
      <div class="card-header">
        <a href="${{a.link}}" class="card-title" target="_blank" rel="noopener">${{a.title}}</a>
        <span class="budget-badge ${{budgetClass}}">${{budgetLabel}}</span>
      </div>
      <div class="meta-row">
        <span>${{kindLabel}}</span>
        <span class="tag">${{a.meta}}</span>
      </div>
      <div class="price">${{priceStr}}</div>
      ${{estHtml}}
      ${{a.desc ? `<div class="desc">${{a.desc}}</div>` : ''}}
      ${{a.img ? `<div class="img-wrap"><img src="${{a.img}}" alt="${{a.title}}" loading="lazy"></div>` : ''}}
    </div>`;
  }});
  return html;
}}

render();
</script>
</body>
</html>'''

with open('/home/erik/.hermes/cron/finn-bilvarsel/index.html', 'w') as f:
    f.write(html)

print(f"Written index.html ({len(html)} bytes)")
