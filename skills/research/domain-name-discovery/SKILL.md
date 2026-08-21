---
name: domain-name-discovery
description: >-
  Brainstorm project/brand names that work across languages (especially Norwegian + English) and
  verify domain availability via DNS pre-filtering and WHOIS lookups. Covers .no, .com, .co, .io TLDs.
  Includes naming strategy for B2B/fintech (Klarna/Affirm-style), consumer SaaS, and tech brands.
  Full pipeline from name ideation with localisation constraints to availability verification to
  registrar recommendations.
tags: [domains, naming, whois, registration, brainstorming, brand]
---

# Domain Name Discovery

Use when the user wants to brainstorm names for a project, SaaS, or brand and check which domains are available for registration. Works best when the name needs to work in Norwegian and English (or other language pairs).

## Phase 1: Name Brainstorming

### Constraints to consider
- **Language pair**: Which languages must the name work in? (e.g. Norwegian + English)
- **TLD preference**: .com, .co, .io, or others the user prefers
- **Length**: Short (3-6 chars) is better for brandability
- **Meaning**: Should the name mean something in one or both languages?
- **Pronunciation**: Must be easy to pronounce for target audience

### Brainstorming categories
1. **Native words that work internationally** — short existing words in the source language that are pronounceable in English (e.g. *trygg*, *borg*, *vakt*, *vern*, *heim*, *kopi*)
2. **Language hybrids** — compound names mixing Norwegian + English (e.g. *tryggvault*, *nordvault*, *backupvern*)
3. **Nordic or fjord theme** — Nordic-sounding brand names (e.g. *nordbackup*, *norsafe*)
4. **English words** — pure English backup or storage vocabulary (e.g. *safekeep*, *backvault*, *stash*)
5. **Verbs as brands** — Norwegian past participles (e.g. *backupet* = has backed up, *lagret* = saved)

### Norwegian-specific notes
- Short Norwegian words ending in consonants are often pronounceable by English speakers
- Examples: *Trygg* (safe), *Borg* (fortress), *Vern* (protection), *Vakt* (guard), *Heim* (home), *Kopi* (copy), *Stasj* (stash), *Lagre* (save/store)
- Past participles (*backupet*, *lagret*, *kopiert*) work as memorable brands

6. **Abstract tech brand names** — short made-up words with no literal meaning but a tech/futuristic vibe (e.g. *zynk*, *nexa*, *velo*, *pixl*, *kiro*). These are often 4-5 letters, easy to pronounce internationally, and evoke brands like Stripe, Vercel, Linear. Good when the user explicitly wants "tech vibe" without semantic baggage. Combine phonemes that sound modern: x, z, v, k, p endings; soft vowels; sharp consonant clusters.

7. **Klarna/Affirm-style brand names** — for B2B, fintech, or SaaS where the name must feel established and trustworthy, not playful. Reference brands: Klarna, Affirm, Collector, Stripe, Vercel. Key traits:
   - **4-6 letters**, 2 syllables max
   - **Every letter unambiguous** — no Q, X, Z (hard to spell in Norwegian). Avoid double letters that create pronunciation doubt
   - **Hard consonant start** (K, V, T, R, B) signals authority; soft starts (S, A) signal approachability
   - **No service-descriptive words** — no "rent", "lease", "cloud", "pay", "shop" in the name. The name should be a clean slate for branding
   - **No generic suffixes** — avoid -ly, -ify, -io, -ly that scream "startup". These age poorly and blur together
   - **Vowel-consonant alternation** makes names easy to say: K-L-A-R-N-A, A-F-F-I-R-M
   - **Example generation pattern**: Pick a hard start (K/V/T/R) + 2-3 alternating consonants/vowels + clean ending. E.g. *Kresto*, *Kredo*, *Vorso*, *Terio*

## Phase 2: Domain Availability Check

When registrar websites (Namecheap, GoDaddy) and the `whois` CLI are rate-limited or blocked, use **raw TCP WHOIS** via Python's `socket` module.

### WHOIS Servers by TLD

| TLD | WHOIS Server |
|-----|-------------|
| .io | whois.nic.io |
| .com | whois.verisign-grs.com |
| .co | whois.nic.co |

### Python lookup function

```python
import socket

def check_domain(domain, server):
    """Returns 'LEDIG', 'REGISTRERT', or raw response text."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(8)
        sock.connect((server, 43))
        sock.sendall((domain + '\r\n').encode())
        data = b''
        while True:
            chunk = sock.recv(8192)
            if not chunk:
                break
            data += chunk
            if len(data) > 5000:
                break
        sock.close()
        text = data.decode('utf-8', errors='ignore')
        # Available signals
        if any(kw in text for kw in [
            'No Data Found', 'NOT FOUND', 'No match for',
            'is available', 'DOMAIN NOT FOUND', 'Domain not found'
        ]):
            return 'LEDIG'
        # Registered signals
        if any(kw in text for kw in [
            'Domain ID:', 'Registry Domain ID:', 'Creation Date:'
        ]):
            return 'REGISTRERT'
        return f'UKJENT: {text[:200]}'
    except Exception as e:
        return f'FEIL: {e}'
```

### Rate limiting
- Always add `time.sleep(1.5)` between lookups to avoid being rate-limited
- Batch checks into groups of 10-15 per script run

### Verification using DNS (quick pre-check)
Before doing WHOIS lookups, DNS can eliminate obviously-taken domains:

```
dig +short "$domain" NS   # Nameservers exist - registered
dig +short "$domain" A    # A record exists - possibly registered
dig +short "$domain" MX   # MX records - definitely in use
```

If a domain has NS or MX records, it is almost certainly registered and you can skip the WHOIS call.

### Batch DNS pre-filter script
For quickly checking many candidate domains before doing full WHOIS:

```bash
for domain in kresto.no kredo.no vorso.no terio.no; do
  dns=$(dig "$domain" +short 2>/dev/null)
  http=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://$domain" 2>/dev/null || echo "err")
  if [ -z "$dns" ] && [ "$http" = "000" -o "$http" = "err" ]; then
    echo "🟢 $domain (LEDIG - ingen DNS, ingen HTTP)"
  elif [ -z "$dns" ]; then
    echo "🟡 $domain (DNS ledig, HTTP $http - sjekk nærmere)"
  else
    echo "🔴 $domain (OPPTATT - DNS peker: $dns)"
  fi
done
```

**Interpretation**: 🟢 = likely available (no DNS + no HTTP response). 🟡 = probably available but verify with WHOIS. 🔴 = definitely taken. DNS-only check is not 100% reliable — domains can be registered but unpointed — so always recommend the user verify on the registrar (norid.no for .no) before committing.

### Alternative (when WHOIS is unreachable)
Use the browser to check a registrar directly (Namecheap works). Navigate to:
`https://www.namecheap.com/domains/registration/results/?domain=<name>`

If the domain appears as "Premium" with a high price, it is taken but could be purchased.
If results show "Add to cart" at standard price, it is available.

## Phase 3: Compile and Present Results

### Recommended format
Categorize by TLD (.com, .io, .co) and mark each as:
- LEDIG - confirmed available
- REGISTRERT - taken
- PREMIUM - taken but available on aftermarket

Highlight top 5 recommendations with:
1. Why the name works (language, meaning, brandability)
2. The TLD that is available
3. How it positions the product

### Common pitfalls — naming
- **Avoid service-descriptive names** — "Rently", "Leasly", "CloudX" etc. feel generic and age poorly. Users often say they want this, then reject it when they see it. Lead with abstract/brandable names first, offer descriptive as fallback only
- **Avoid -ly suffixes** — overused in startup naming (Shopify, Spotify, etc.), signals "just another SaaS". Users frequently reject these
- **Avoid Q, X, Z in Nordic markets** — hard to spell and pronounce in Norwegian. "Quippo" sounds good but fails the "is it easy to spell on the phone?" test
- **Avoid double letters that create ambiguity** — "Bocco", "Fazzo" look good but people ask "er det to c'er? én z?"
- **Test the "Klarna standard"** — if you can't spell it after hearing it once, it's too complex. K-L-A-R-N-A: every letter is immediately clear
- **Check .no domain FIRST** for Norwegian businesses — many short .com names are taken but .no may be free. Don't fall in love with a .com if the business is Norway-only
- **User preferences vary widely** — some want literal/descriptive, others want abstract. Ask early, don't assume

### Common pitfalls — domain verification
- WHOIS servers enforce strict rate limits across IP ranges; single-thread plus sleep is essential
- .io WHOIS (whois.nic.io) rejects queries that do not end with '\r\n' - binary socket ensures this
- Short dictionary-word .io domains are almost always premium or registered
- .com availability is rare for short words; compound names have better odds
- .co WHOIS server (whois.nic.co) is unreliable from some networks
- Some registry WHOIS servers only show NOT FOUND versus registered state; pattern-match carefully
- .no (NORID) requires `domain: <name>.no` format, not bare domain — `nc whois.norid.no 43` works when `whois` CLI is missing
- **Norid API details**: See `references/norid-api.md` for RDAP, DAS, WHOIS endpoints, rate limits, and limitations (including that expiry dates are NOT exposed via any public API)
- Batch WHOIS lookups via subagents can return inconsistent results due to rate limiting or format issues. Always re-verify a subset individually before presenting final results to the user
