# AWS SES DNS Records

## Domain Verification (TXT)

```
_amazonses.<domain>  TXT  <VerificationToken>
```

The token comes from:
```bash
aws ses verify-domain-identity --domain <domain> --region <region>
```

## DKIM (CNAME × 3)

```
<token1>._domainkey.<domain>  CNAME  <token1>.dkim.amazonses.com
<token2>._domainkey.<domain>  CNAME  <token2>.dkim.amazonses.com
<token3>._domainkey.<domain>  CNAME  <token3>.dkim.amazonses.com
```

The tokens come from:
```bash
aws ses verify-domain-dkim --domain <domain> --region <region>
```

## MAIL FROM (optional, improves deliverability)

```
<mail-from-subdomain>.<domain>  MX  10 feedback-smtp.<region>.amazonses.com
<mail-from-subdomain>.<domain>  TXT  "v=spf1 include:amazonses.com ~all"
```

Configure with:
```bash
aws ses set-identity-mail-from-domain \
  --identity <domain> \
  --mail-from-domain <mail-from-subdomain>.<domain> \
  --region <region>
```

## Verification Status Check

```bash
aws ses get-identity-verification-attributes --identities <domain> --region <region>
```

States: `Pending` → `Success` (DNS propagated) or `Failed` (wrong record).

## Notes

- DKIM is optional but strongly recommended — prevents spoofing and
  improves inbox placement.
- A subdomain identity (`app.example.com`) needs its own TXT/CNAMEs
  *under that subdomain*; apex records verify only the apex. Verifying
  the apex does not cover mail sent as `@app.example.com` either.
- Hand records over in both forms: the FQDN SES resolves
  (`_amazonses.app.example.com`) and the registrar-panel host, which is
  the FQDN minus the zone apex (`_amazonses.app`) for panels that append
  the origin themselves — mismatches here are the usual cause of a
  stuck `Pending`.
- Confirm locally before polling SES: `dig +short TXT
  _amazonses.<domain>` and `dig +short CNAME <token>._domainkey.<domain>`
  against the authoritative NS.
- DNS propagation can take minutes to hours. Check status periodically.
- SES sandbox: new accounts can only send to verified addresses.
  Request production access in the AWS console.
