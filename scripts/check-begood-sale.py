#!/usr/bin/env python3
"""
Check if the Diskré Speedometer product on begood.no is on sale.
Outputs a message only if the product is on sale (compare-at price differs from current price).
"""
import re
import urllib.request

URL = "https://www.begood.no/products/diskr-speedometer-tesla-model-3y"

def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

def extract_prices(html):
    """Return (current_price, original_price) as floats, or None if not found."""
    # Current price from JS variable
    m_price = re.search(r'var\s+product_price\s*=\s*"(\d+)"', html)
    # Original price from hidden input
    m_orig = re.search(r'name=["\']original_price["\']\s+value=["\']([^"\']+)', html)
    # Also check for .price-old element (strikethrough on sale)
    has_price_old = bool(re.search(r'class="price-old"', html))
    # Check for sale badge / compare price in structured data
    m_compare = re.search(r'"price"\s*:\s*"?(\d+[\.,]?\d*)"?', html)

    current = float(m_price.group(1)) if m_price else None
    if m_orig:
        # Value is "998,-" format — strip everything except digits and decimal
        raw = m_orig.group(1).replace(".", "").replace(",", ".").rstrip(".-")
        original = float(raw) if raw else None
    else:
        original = None
    return current, original, has_price_old

def main():
    html = fetch()
    current, original, has_price_old = extract_prices(html)

    if current is None:
        print("Kunne ikke hente pris fra siden. Sjekk manuelt:")
        print(URL)
        return

    # If original exists and is higher than current, it's on sale
    if original and original > current:
        pct = round((1 - current / original) * 100)
        print(f"🎉 TILBUD på Diskré Speedometer Tesla Model 3 & Y!")
        print(f"Nå: {current:.0f},- (ordinærpris: {original:.0f},-)")
        print(f"Spart: {original - current:.0f},- ({pct}% rabatt)")
        print(f"\n🔗 {URL}")
    elif has_price_old:
        print(f"🎉 TILBUD på Diskré Speedometer Tesla Model 3 & Y!")
        print(f"Pris: {current:.0f},-")
        print(f"\n🔗 {URL}")
    else:
        # Not on sale — no output (silent)
        pass

if __name__ == "__main__":
    main()
