# Shopify/WooCommerce Price Extraction Patterns

Common HTML/JS patterns for extracting prices from e-commerce product pages.
Use when building price-drop watchdog scripts for stores like begood.no, komplett.no, etc.

## Server-rendered HTML patterns

### Hidden form inputs (most reliable)
```html
<input type="hidden" name="price" value="998,-" />
<input type="hidden" name="original_price" value="998,-" />
```
Regex: `name=["\']original_price["\']\s+value=["\']([^"\']+)`

### Price span (visible element)
```html
<span class="products_price">998,-</span>
```
Regex: `class="products_price">([^<]+)<`

### Meta tags
```html
<meta property="product:price:amount" content="998.00" />
<meta property="product:price:currency" content="NOK" />
```
Regex: `product:price:amount.*?content="([^"]+)"`

## JavaScript variables (server-rendered in script tags)

```javascript
var product_price = "998";
var baseprice = "798.4";  // ex-VAT price
```
Regex: `var\s+product_price\s*=\s*"(\d+)"`

## Sale indicators

### Strikethrough / compare-at price
```html
<span class="price-old"><s>1.299,-</s></span>
<span class="price-new">998,-</span>
```
Check: `re.search(r'class="price-old"', html)` → boolean

### Sale badge
```html
<span class="badge sale">-20%</span>
```

### JSON-LD structured data (if present)
```json
{
  "@type": "Product",
  "offers": {
    "price": "998.00",
    "priceCurrency": "NOK"
  }
}
```

## Norwegian price formats

| Input format | Float value |
|---|---|
| `998,-` | 998.0 |
| `1.299,-` | 1299.0 |
| `49,90` | 49.90 |
| `1.299,50` | 1299.50 |

Parsing: strip `.` (thousands), replace `,` → `.` (decimal), strip trailing `.-`

```python
raw = price_str.replace(".", "").replace(",", ".").rstrip(".-")
value = float(raw)
```

## Gotchas

- **Prices in JS variables are more reliable** than visible spans (some stores update
  JS variables dynamically but the span lags behind)
- **`original_price` hidden input** is the best sale indicator — when it equals the
  current price, the product is NOT on sale
- **Server-rendered JS** (`<script>var product_price = "..."`) is visible to `curl`;
  client-rendered content (React/Vue hydration) is NOT — use `browser_navigate`
  for inspection, but the cron script can often rely on server-rendered data
- **Some stores use `baseprice` for ex-VAT** — don't confuse with original/sale price
- **Escaped quotes in HTML** (`\"original_price\"`) vary by store — test with `cat -v`
  on the curl output before writing regex
