# WHOIS Servers by TLD

| TLD | WHOIS Server | Protocol |
|-----|-------------|----------|
| .no | whois.norid.no | Port 43 (raw TCP) |
| .io | whois.nic.io | Port 43 (raw TCP) |
| .com | whois.verisign-grs.com | Port 43 (raw TCP) |
| .net | whois.verisign-grs.com | Port 43 (raw TCP) |
| .co | whois.nic.co | Port 43 (raw TCP) |
| .org | whois.pir.org | Port 43 (raw TCP) |
| .info | whois.afilias.net | Port 43 (raw TCP) |
| .xyz | whois.nic.xyz | Port 43 (raw TCP) |
| .app | whois.nic.google | Port 43 (raw TCP) |
| .dev | whois.nic.google | Port 43 (raw TCP) |

## .no (NORID) specific

Query format — must send `domain: <name>.no` (not just the domain):
```bash
echo "domain: test.no" | nc whois.norid.no 43
```

### Available signals (NORID)
- `No match for` — domain is available

### Registered signals (NORID)
- `Handle:` or `Holder:` — domain is registered
- `created:` — domain has a creation date

### Pitfalls
- NORID does NOT accept bare domain queries (e.g. `test.no\r\n`). Must use `domain: test.no` format.
- `whois` CLI may not be installed; use `nc whois.norid.no 43` directly.
- Batch WHOIS lookups can return inconsistent results due to rate limiting. If results look wrong, re-verify individually before presenting to the user.

# Response Pattern Reference

## Available ("LEDIG") signals — any of these in the response text
- `No Data Found`
- `NOT FOUND`
- `No match for`
- `is available for purchase`
- `DOMAIN NOT FOUND`
- `Domain not found`
- `No entries found`
- `Status: free`

## Registered signals — any of these confirms registration
- `Domain ID:`
- `Registry Domain ID:`
- `Creation Date:`
- `Updated Date:`
- `Registry Expiry Date:`
- `Registrar:`
- `Registrar IANA ID:`
- `Handle:` (NORID)
- `Holder:` (NORID)

# Registrar Website URLs (alternative to WHOIS)

| Registrar | URL Pattern |
|-----------|-------------|
| Namecheap | `https://www.namecheap.com/domains/registration/results/?domain=<domain>` |
| Porkbun | `https://porkbun.com/check/<domain>` |
| Godaddy | `https://www.godaddy.com/domainsearch/find?checkAvail=1&domainToCheck=<domain>` |

Note: Most registrars use Cloudflare anti-bot protection and will block automated curl/browser_snapshot. Namecheap works best for manual browser checks.
