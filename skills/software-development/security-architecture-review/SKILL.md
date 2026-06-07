---
name: security-architecture-review
description: Systematic security architecture review of application subsystems. Trace data flows, verify cryptographic primitives, analyze key management, build threat models, and present structured findings. Use when the user asks for a «security assessment», «sikkerhetsvurdering», «security audit», «gå gjennom sikkerheten», or wants a security-focused code review of encryption/auth/infrastructure.
---

# Security Architecture Review

A disciplined approach for systematically assessing security properties of an application subsystem — encryption, authentication, key management, or data handling.

## Phase 1 — Map the subsystem

Trace the complete data flow before making any security claims.

1. **Find entry points** — controllers, commands, jobs, API routes that handle sensitive data
2. **Find helpers/services** — classes that implement encryption, decryption, hashing, signing
3. **Find storage** — where encrypted/sensitive data lives (local disk, cloud storage, DB columns)
4. **Find key/secret management** — how keys are generated, stored, retrieved, and zeroed

For Laravel apps specifically: check `app/Helpers/`, `app/Actions/`, `app/Jobs/`, `routes/`, and `config/` for the above.

## Phase 2 — Identify cryptographic primitives

For each cryptographic operation, determine:

| Question | Importance |
|----------|-----------|
| What algorithm/library? (`sodium_crypto_secretbox`, `openssl_encrypt`, Laravel `encrypt()`) | Foundation — everything else depends on this |
| Is it AEAD (authenticated encryption)? | Non-AEAD ciphers can be silently tampered with |
| Is it a modern, well-vetted algorithm? | Custom or ancient ciphers are an instant finding |
| What key size? | < 128 bits is critical; 256 bits is standard |

## Phase 3 — Verify implementation correctness

Check these specific properties systematically:

- **Nonce/IV**: Generated with `random_bytes()` (CSPRNG)? Unique per operation? Correct length for the algorithm?
- **Key validation**: Length and format checked before use? Rejects invalid keys gracefully?
- **Encoding**: Base64 encode/decode with strict mode (`base64_decode($x, true)`)?
- **Memory safety**: Sensitive data (`sodium_memzero()`) and keys zeroed after use?
- **Authentication**: MAC verified before plaintext is returned? `sodium_crypto_secretbox_open()` returns false on auth failure?
- **Error handling**: Decryption failures return null/throw, not partial or garbled data?
- **Timing attacks**: `hash_equals()` or libsodium for comparisons? No `===` on secrets?

## Phase 4 — Analyze key management

The weakest link in most systems. Map these:

1. **Storage**: Where is the key? Same server as data? Encrypted at rest (wrapped)?
2. **Generation**: CSPRNG (`random_bytes()`)? Or something predictable?
3. **Lifecycle**: Rotation mechanism? Revocation? Secure deletion?
4. **Blast radius**: One key for everything, or per-file/per-user keys?
5. **Supply chain**: How does an operator first set up the key? Web UI? CLI? Config file?

Rate the finding:
- 🔴 **Key and data on same host** — protects against storage-level breach, not server compromise
- 🟡 **Layered key wrapping** — defense in depth, good practice
- 🟢 **Separate KMS/HSM/Vault** — ideal but operationally heavy

## Phase 5 — Build a threat model

For each asset, enumerate:

| Asset | Threat | Protected? | Not protected? |
|-------|--------|-----------|----------------|
| Encrypted files | Cloud provider breach | ✅ Encrypted before upload | ❌ Server compromise (key on same host) |
| ... | Physical disk theft | ✅ Encrypted at rest | ❌ Memory scraping during active decryption |
| ... | Malicious insider w/ DB only | ✅ Files not in DB | ❌ Insider w/ filesystem + APP_KEY |

## Phase 6 — Present findings

Structure the output in these sections:

```
## ✅ Strengths
- What is done correctly and exceeds common practice

## ⚠️ Svakheter
- Real issues grouped by severity
- Each with: finding, impact, recommendation

## 🔍 Cryptographically correct?
- Table with all Phase 3 checks

## 📊 Oppsummering
- What the system protects against
- What it does NOT protect against
```

Use a clear, visual format with ✅/❌/⚠️ markers so the user can scan quickly.

## Pitfalls

- ❌ **Don't** call "key on same server" a cryptographic implementation error — it's an architectural constraint. Call it for what it is: the system protects against storage-level breaches, not full server compromise.
- ❌ **Don't** confuse Laravel's `encrypt()` (AES-256-CBC, APP_KEY) with application-level encryption — they solve different problems (session crypto vs. data-at-rest crypto).
- ❌ **Don't** recommend HSMs/KMS without understanding deployment scale — for a single-server Laravel app, the operational cost often outweighs the benefit.
- ❌ **Don't** stop at "this is secure" — state explicitly what threat model it *does* and *does not* protect against. The user needs to know their actual risk.
- ❌ **Don't** skip memory zeroing checks — `sodium_memzero()` is often forgotten and is a genuine finding.
- ✅ **Do** verify nonce uniqueness at the call sites, not just in the helper — one caller passing the same nonce twice defeats the cipher regardless of how well the helper is written.
