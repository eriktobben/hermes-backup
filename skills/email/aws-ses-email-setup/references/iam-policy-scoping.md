# Domain-scoped IAM policy for SES sending

Goal: one access key that can only send mail *as* one domain, nothing
else in the account.

## Policy shape (validated against a live account)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SendOnlyFromDomain",
      "Effect": "Allow",
      "Action": ["ses:SendEmail", "ses:SendRawEmail", "ses:SendTemplatedEmail"],
      "Resource": [
        "arn:aws:ses:<region>:<account>:identity/<domain>",
        "arn:aws:ses:<region>:<account>:identity/*@<domain>"
      ],
      "Condition": {"StringLike": {"ses:FromAddress": ["*@<domain>"]}}
    },
    {
      "Sid": "ReadSendStats",
      "Effect": "Allow",
      "Action": ["ses:GetSendQuota", "ses:GetSendStatistics"],
      "Resource": "*"
    }
  ]
}
```

Why both resources:

- The domain ARN covers calls that pass `SourceArn`/`ReturnPathArn`.
- `identity/*@<domain>` covers plain `SendEmail`/`SendRawEmail`, where SES
  resolves the resource from the **From address** instead of the verified
  domain. Domain ARN alone → `AccessDenied` on `identity/user@<domain>`.
- The `ses:FromAddress` condition is the second layer: even if Resource
  were widened later, only `*@<domain>` From values pass. `StringLike`
  accepts `*`/`?` wildcards and is case-sensitive.
- `*@<domain>` does **not** match subdomains (`x@sub.<domain>` ends in
  `.`, not `@`) — each subdomain needs its own verified identity and its
  own ARN. Intended.
- `ses:GetSendQuota`/`ses:GetSendStatistics` on `*` are read-only health
  checks; harmless and worth keeping for monitoring.

## Create

```bash
aws iam create-policy --policy-name SES-<name> --policy-document file:///policy.json
aws iam create-user --user-name <name>-ses-api      # no --description flag; use --tags
aws iam attach-user-policy --user-name <name>-ses-api --policy-arn <policy-arn>
aws iam create-access-key --user-name <name>-ses-api
```

Updating an existing policy later:
`aws iam create-policy-version --policy-arn <arn> --policy-document
file:///policy.json --set-as-default` — run it as an admin credential, not
as the scoped key you just made.

## Validate before DNS exists

IAM is authorized *before* SES's own identity verification, so a policy
can be proven correct while the domain is still `Pending`, with zero mail
delivered:

```bash
(
export AWS_ACCESS_KEY_ID=<key>
export AWS_SECRET_ACCESS_KEY=<secret>
export AWS_DEFAULT_REGION=<region>
MSG='Subject={Data=policy-test},Body={Text={Data=hi}}'

# 1) allowed From on the (still unverified) domain
aws ses send-email --from postmaster@<domain> --to someone@example.invalid --message "$MSG"
#  -> MessageRejected: Email address is not verified   => policy PASSED

# 2) From outside the domain
aws ses send-email --from no-reply@evil.example --to someone@example.invalid --message "$MSG"
#  -> AccessDenied on identity/no-reply@evil.example    => correctly denied

# 3) read-only call
aws ses get-send-quota --query Max24HourSend --output text
#  -> 50000.0                                           => stats statement OK
)
```

Read the outcomes strictly:

- `MessageRejected ... not verified` = authorization succeeded; the only
  missing piece is DNS. Do not touch the policy.
- `AccessDenied` = policy bug. The error names the evaluated resource —
  compare it against your `Resource` patterns to see which is missing.
- A subshell (or an explicit `unset AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY`) matters: exported credentials persist across
  terminal calls in a session and silently re-scope later admin commands.

Negative probes are free: an unverified foreign From is rejected by IAM
before anything else, so the deny path never sends mail either.

## Wiring the application

Laravel (SES driver over the AWS SDK):

```dotenv
MAIL_MAILER=ses
AWS_ACCESS_KEY_ID=<key id>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_DEFAULT_REGION=<region>
```

- `config/mail.php` → `mailers` needs `'ses' => ['transport' => 'ses']`
  on Laravel 10 and older; 11+ ships it.
- `mail.from.address` **must** be inside `*@<domain>` — the condition
  denies every send otherwise, and Laravel surfaces it as an SDK error,
  not a permissions message.
- The SDK reads the region from `AWS_DEFAULT_REGION`; SES endpoints are
  region-specific, so it must match where the identity was created.

SMTP alternative (same key, derived password): see
`references/smtp-credentials.md` — username = access key id, host
`email-smtp.<region>.amazonaws.com`, port 587 STARTTLS.

## Scaling to more domains

Add another identity plus its pair of `Resource` ARNs to the same
statement only when one key is genuinely meant to speak for several
domains; otherwise use one policy + one key per app so a leak is
containable.
