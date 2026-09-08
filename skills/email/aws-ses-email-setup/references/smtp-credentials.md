# AWS SES SMTP Credentials

## How SMTP Credentials Work

SES SMTP credentials are NOT the IAM user's access key + secret key
directly. The SMTP password is derived from the IAM secret key using
a specific signing algorithm.

### SMTP Username

The IAM access key ID (e.g. `AKIA...`).

### SMTP Password Generation

```python
import hmac, hashlib, base64

def generate_smtp_password(secret_key: str) -> str:
    """Generate SES SMTP password from IAM secret key."""
    signature = hmac.new(
        key=secret_key.encode('utf-8'),
        msg=b"SendRawEmail",
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode('utf-8')
```

The algorithm:
1. HMAC-SHA256 sign the string `"SendRawEmail"` with the IAM secret key
2. Base64 encode the resulting 32-byte signature
3. That 44-character base64 string is the SMTP password

### SMTP Server

```
email-smtp.<region>.amazonaws.com
```

### Ports

| Port | Protocol | Notes |
|------|----------|-------|
| 465  | Implicit TLS (`smtps://`) | Often blocked on servers |
| 587  | STARTTLS (`smtp://`) | Recommended — works almost everywhere |

**Always test port availability first:**
```bash
nc -zv -w 3 email-smtp.<region>.amazonaws.com 587
nc -zv -w 3 email-smtp.<region>.amazonaws.com 465
```

## Creating a Dedicated IAM User (Recommended)

```bash
# Create user
aws iam create-user --user-name ses-smtp-user

# Create access key
aws iam create-access-key --user-name ses-smtp-user

# Create SES-only policy
cat > /tmp/ses-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "ses:SendEmail",
            "ses:SendRawEmail"
        ],
        "Resource": "*"
    }]
}
EOF

aws iam create-policy --policy-name SESSendEmail --policy-document file:///tmp/ses-policy.json
aws iam attach-user-policy --user-name ses-smtp-user --policy-arn arn:aws:iam::<account>:policy/SESSendEmail
```

## Pitfalls

- **Password is NOT the IAM secret key.** It's HMAC-SHA256 signed +
  base64 encoded. Using the raw secret key as SMTP password will fail
  with `535 Authentication Credentials Invalid`.

- **New IAM users need propagation time.** SMTP auth may fail for
  30-60 seconds after user creation. Retry after a short wait.

- **Region matters.** SMTP endpoint is region-specific:
  `email-smtp.eu-north-1.amazonaws.com` ≠ `email-smtp.us-east-1.amazonaws.com`.

- **Port 465 often blocked.** Use port 587 with STARTTLS if 465 times out.

- **SES sandbox.** New accounts can only send to verified addresses.
  The `ses:SendEmail` permission alone doesn't bypass sandbox — you
  need production access from the AWS console.
