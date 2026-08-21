# Norid API Reference (.no Domains)

## Services Overview

| Service | Endpoint | Purpose | Access |
|---------|----------|---------|--------|
| **RDAP** | `rdap.norid.no` | REST API for domain data (JSON) | Public |
| **DAS** | `finger.norid.no:79` | Domain Availability Service | Public |
| **WHOIS** | `finger.norid.no:79` | Legacy lookup (being phased out) | Public |
| **EPP** | `epp.norid.no:700` | Domain registration/management | Registrar only |

## RDAP (Recommended for .no Lookups)

### Basic Usage
```bash
# Check if domain exists (returns 200 or 404)
curl -I https://rdap.norid.no/domain/example.no

# Get full domain data (JSON)
curl https://rdap.norid.no/domain/example.no

# Check name server
curl https://rdap.norid.no/nameserver_handle/X11H-NORID
```

### Key Limitations
- **No expiry dates**: RDAP returns `registration` and `last changed` events, but NOT `expiration` events. You cannot determine when a domain will expire.
- **No drop list**: Norid does not publish a list of domains about to become available.
- **No bulk listing**: Cannot enumerate all domains or search by expiry date.

### Rate Limiting (Anonymous)
- 300 GET + 3,000 HEAD requests per 24 hours (sliding window) per IP
- 10 requests per minute (GET or HEAD) per IP
- Exceeding returns `429 Too Many Requests`

### Authenticated Access (Registrars Only)
- Higher rate limits
- Access to search functions (but only returns domains where you are the sponsoring registrar)
- Extended data (subscriber info, contact details)
- Authentication: HTTP Basic Auth with username@regid format

### RDAP Search Functions (Registrar Only)
```
https://rdap.norid.no/domains?name=nord*.no
https://rdap.norid.no/domains?registrant=NT1O
https://rdap.norid.no/domains?identity=985821585
https://rdap.norid.no/domains?nsIp=128.39.8.40
```
⚠️ These only return domains where the authenticating registrar is the sponsoring registrar.

## DAS (Domain Availability Service)

### Usage
```bash
# Via finger protocol
echo 'example.no' | nc finger.norid.no 79

# Or with whois client
whois -p 79 -h finger.norid.no example.no
```

### Response Types
- `example.no is available` → Domain can be registered
- `example.no is delegated` → Domain is registered
- `example.no is not available` → Permanently blocked (reserved, premium, etc.)

### Test Environment
- Host: `finger.test.norid.no`, Port: 79

## Common Pitfalls

1. **WHOIS CLI may not be installed**: Use `nc` (netcat) or Python socket as fallback
2. **DAS requires port 79**: Some networks block non-standard ports; use `nc -w 5` for timeout
3. **IDN domains**: Use UTF-8 syntax: `whois -p 79 -h finger.test.norid.no -- -c utf-8 øøæån.no`
4. **Rate limits are strict**: Add `sleep 1-2` between batch lookups
5. **RDAP 404 is ambiguous**: A 404 could mean "available" OR "permanently blocked" — do a GET to distinguish:
   - "Domain is not available for registration" → permanently blocked
   - "Domain is currently not available for registration" → temporarily blocked (e.g., recently expired)

## Monitoring Expiring Domains

**There is no official Norid API for tracking expiring domains.** Workarounds:

1. **Manual monitoring**: Check specific domains of interest periodically via RDAP/DAS
2. **Third-party services**: Some domain monitoring services track .no drops (research current options)
3. **Contact Norid**: Email info@norid.no to ask about bulk/expiry data access
4. **Registrar partnership**: Some registrars offer backorder services for expiring domains

## Official Documentation
- Technical portal: https://teknisk.norid.no
- RDAP docs: https://teknisk.norid.no/en/integrere-mot-norid/rdap-tjenesten/
- DAS docs: https://teknisk.norid.no/en/integrere-mot-norid/das/
- Domain lookup: https://www.norid.no/no/domeneoppslag/finn-ledig-domenenavn/

---
*Last updated: 2026-08-21*
