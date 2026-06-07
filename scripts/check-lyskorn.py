#!/home/erik/.hermes/hermes-agent/venv/bin/python3
"""Check if lyskorn.no is available for registration. Quiet if taken, notify if free."""

import sys
import whois

DOMAIN = 'lyskorn.no'

try:
    w = whois.whois(DOMAIN)
    # If we get here, domain is registered
    if w.get('domain_name'):
        # Domain is registered - stay silent
        sys.exit(0)
    else:
        # No domain_name in result - likely available
        print(f"🎉 *{DOMAIN}* er LEDIG og kan bestilles!\n"
              f"Sjekk https://www.norid.no/no/domeneoppslag/ eller bruk et domenesalg-sted.")
        sys.exit(0)
except whois.parser.WhoisDomainNotFoundError:
    print(f"🎉 *{DOMAIN}* er LEDIG og kan bestilles!\n"
          f"Sjekk https://www.norid.no/no/domeneoppslag/ eller bruk et domenesalg-sted.")
    sys.exit(0)
except Exception as e:
    # On error, print a warning so we know the check failed
    print(f"⚠️ Kunne ikke sjekke {DOMAIN}: {type(e).__name__}: {e}")
    sys.exit(1)
