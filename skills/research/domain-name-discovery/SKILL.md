---
name: domain-name-discovery
description: >
  Brainstorm SaaS or project names that work across languages (especially Norwegian + English) and
  verify domain availability across .com, .co, and .io TLDs via raw TCP WHOIS lookups. Covers the
  full pipeline from name ideation with localisation constraints to availability verification to
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

### Common pitfalls
- WHOIS servers enforce strict rate limits across IP ranges; single-thread plus sleep is essential
- .io WHOIS (whois.nic.io) rejects queries that do not end with '\r\n' - binary socket ensures this
- Short dictionary-word .io domains are almost always premium or registered
- .com availability is rare for short words; compound names have better odds
- .co WHOIS server (whois.nic.co) is unreliable from some networks
- Some registry WHOIS servers only show NOT FOUND versus registered state; pattern-match carefully
