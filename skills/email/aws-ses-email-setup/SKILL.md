---
name: aws-ses-email-setup
description: "AWS SES email setup: domain verify, DKIM, SMTP creds."
version: 1.0.0
author: hermes-agent
license: MIT
metadata:
  hermes:
    tags: [AWS, SES, Email, SMTP, DKIM, DNS]
---

# AWS SES Email Setup

Procedures for setting up email sending through Amazon SES — domain
verification, DKIM, SMTP credential generation, IAM user creation,
and DNS record management.

## References

- `references/dns-records.md` (exact DNS record formats for verification + DKIM)
- `references/smtp-credentials.md` (password generation algorithm + pitfalls)

## Prerequisites

1. AWS CLI configured (`aws sts get-caller-identity` to verify)
2. IAM user with SES permissions (`ses:SendEmail`, `ses:SendRawEmail`)
3. DNS access for the domain being verified

## Procedure

### 1. Verify the domain

```bash
aws ses verify-domain-identity --domain app.example.com --region eu-north-1
```

Returns a `VerificationToken` — this goes in a TXT DNS record.

### 2. Enable DKIM

```bash
aws ses verify-domain-dkim --domain app.example.com --region eu-north-1
```

Returns 3 DKIM tokens — each becomes a CNAME DNS record.

### 3. Add DNS records

See `references/dns-records.md` for the exact record format. The user
must add these before verification completes.

### 4. Check verification status

```bash
aws ses get-identity-verification-attributes --identities app.example.com --region eu-north-1
```

Status goes from `Pending` → `Success` once DNS propagates.

### 5. Generate SMTP credentials

See `references/smtp-credentials.md` for the algorithm. The SMTP
username is the IAM access key ID; the password is generated from
the secret key.

### 6. Configure the sending application

Provide the user with:
- SMTP host, port, username, password
- From address
- Encryption method (STARTTLS on port 587 recommended — port 465 is often blocked)

## Pitfalls

- **Port 465 often blocked.** Many servers block outbound port 465
  (implicit TLS). Use port 587 with STARTTLS instead. Test with
  `nc -zv -w 3 email-smtp.<region>.amazonaws.com 587` before assuming
  port 465 works.

- **SES is region-specific.** Always pass `--region` to AWS CLI
  commands. Credentials generated in one region don't work in another.

- **New IAM users need propagation time.** SMTP credentials for
  freshly created IAM users may fail immediately. Wait 30-60 seconds
  and retry.

- **Sandbox mode.** New SES accounts start in sandbox — can only send
  to verified addresses. Request production access via the AWS console
  to send to any address.

- **IAM user needs explicit SES permissions.** `AdministratorAccess`
  works but is overkill. For production, create a dedicated IAM user
  with only `ses:SendEmail` and `ses:SendRawEmail`.

- **Himalaya v2 config format.** If configuring himalaya, use the v2
  flat `smtp.*` keys, not the old `message.send.backend.*` format.
  See himalaya skill for details.