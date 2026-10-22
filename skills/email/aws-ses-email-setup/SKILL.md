---
name: aws-ses-email-setup
description: "AWS SES email setup: domain verify, DKIM, SMTP creds, domain-scoped IAM API key for SDK/Laravel."
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
- `references/iam-policy-scoping.md` (domain-scoped IAM policy JSON, pre-DNS
  policy validation probes, Laravel/SMTP wiring)

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

### 7. Scope an API key for the application

SDK apps (Laravel and friends) want an IAM access key rather than SMTP:

```bash
aws iam create-policy --policy-name SES-<name> --policy-document file:///policy.json
aws iam create-user --user-name <name>-ses-api      # no --description flag exists; use --tags
aws iam attach-user-policy --user-name <name>-ses-api --policy-arn <policy-arn>
aws iam create-access-key --user-name <name>-ses-api
```

Use the policy shape in `references/iam-policy-scoping.md`: the send
actions on the domain ARN **and** `identity/*@<domain>`, gated by a
`ses:FromAddress` condition of `*@<domain>`, plus
`ses:GetSendQuota`/`ses:GetSendStatistics` on `*`. Hand over the key id,
secret, region, and the exact From address the app is allowed to use —
anything outside the domain is rejected by the condition.

**Validate the key before DNS is in place.** IAM is authorized ahead of
SES's identity check, so a send from an allowed From on a still-unverified
domain returns `MessageRejected: ... not verified` (policy passed), while
a From outside the domain returns `AccessDenied` (policy failed). Run the
probes in a subshell (see the credential-leak pitfall below) — nothing is
delivered either way.

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
  to send to any address. Read `aws ses get-send-quota --region <r>`
  first: sandbox shows ~200 sends/24h at 1/sec, production 50000/24h at
  14/sec — promise recipients accordingly.

- **IAM user needs explicit SES permissions, scoped to one domain.**
  `AdministratorAccess` works but is overkill; create a dedicated IAM
  user whose send statement covers only `ses:SendEmail` /
  `ses:SendRawEmail` on that identity. SES resolves `SendEmail`'s IAM
  resource to the **From address** (`identity/user@domain.tld`) whenever
  the call carries no `SourceArn` — not to the verified domain — so a
  policy whose Resource is only the domain ARN denies every plain send.
  Always add `identity/*@<domain>` beside the domain ARN, and gate with
  `ses:FromAddress`. Full JSON in `references/iam-policy-scoping.md`.

- **Never widen a policy in answer to `MessageRejected: ... not
  verified`.** That error means IAM already passed and only DNS is
  missing; `AccessDenied` is the policy-failure signal. Treating the two
  as the same bug quietly loosens a correctly scoped key.

- **Himalaya v2 config format.** If configuring himalaya, use the v2
  flat `smtp.*` keys, not the old `message.send.backend.*` format.
  See himalaya skill for details.

- **Exported AWS credentials persist across terminal calls in a
  session.** Running a scoped key's `export AWS_ACCESS_KEY_ID=...`
  silently turns every later `aws iam` / `aws ses` command into that
  restricted user, producing confusing `AccessDenied` on admin calls.
  Wrap credential use in a subshell `( ... )`, or `unset
  AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN` before the
  next command.

- **JMESPath treats dots as path separators.** With identity names like
  `app.example.com`, `--query 'VerificationAttributes.app.example.com'`
  returns `null`; quote the key (`--query
  'VerificationAttributes."app.example.com"'`) or drop `--query` and read
  the raw JSON.