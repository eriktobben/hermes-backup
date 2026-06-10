# MasterFeed image encryption — worked example

Full security architecture review performed 2026-06-03.

## Subsystem overview

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Cipher | `sodium_crypto_secretbox` (XSalsa20-Poly1305) | Authenticated symmetric encryption of each image file |
| Per-file key | 256-bit from `encrypted.enc` passcode | Unique nonce (24 bytes) per encryption via `random_bytes()` |
| Passcode file | `storage/app/files/passcode.json` | Stores the image encryption key, double-encrypted with Laravel's APP_KEY |
| Key wrapper 1 | Laravel `encrypt()` (AES-256-CBC) | Encrypts the JSON structure in passcode.json |
| Key wrapper 2 | Laravel `encrypt()` again | Encrypts the passcode value itself |
| Storage | Local disk + Backblaze B2 | `.enc` files, never stored in plaintext |

## Files examined

- `app/Helpers/EncryptedFileHelper.php` — core encrypt/decrypt using libsodium
- `app/Helpers/EncryptionKeyGenerator.php` — key generation
- `app/Helpers/PasscodeFileHelper.php` — passcode retrieval from passcode.json
- `app/Helpers/EncryptedFileFromDisk.php` — reads + decrypts files from storage
- `app/Http/Controllers/ImagesController.php` — serves decrypted images to browser
- `app/Http/Controllers/UploadImagesController.php` — encrypts + stores uploads
- `app/Livewire/Passcode/Index.php` — passcode entry via web UI (sets up passcode.json)
- `app/Models/Image.php` — path generation (`encrypted/images/{profile_id}/{uuid}.enc`)

## Findings

### ✅ Strengths

- **XSalsa20-Poly1305** — well-vetted AEAD; provides both confidentiality and integrity
- **Unique nonce per operation** — `random_bytes(24)` each call; correct length for XSalsa20
- **Memory zeroing** — `sodium_memzero()` consistently applied to keys, plaintext, and passcode after use
- **Defense in depth** — files encrypted before upload to Backblaze B2; passcode.json double-encrypted with APP_KEY
- **CoreEncryptionFile kill switch** — can instantly block all image serving globally
- **Private cache headers** — `cache.headers:private;max_age=2628000;etag` prevents shared-cache leakage
- **UUID filenames** — no information leakage from filenames

### ⚠️ Weaknesses

| Severity | Finding | Impact | Recommendation |
|----------|---------|--------|---------------|
| 🔴 HØY | Key stored on same server as encrypted data | Server compromise (root/SSH/RCE) = full decryption | Separate key storage (env var sourced at deploy time, or external KMS) |
| 🟡 MEDIUM | APP_KEY is single point of failure | Leaked APP_KEY defeats all encryption layers | Key rotation mechanism; periodic re-keying |
| 🟢 LAV | Passcode entered via web UI (plaintext POST) | Exists in PHP memory during request | Acceptable — mitigated by TLS and `sodium_memzero()` |

### 🔍 Cryptographically correct?

| Check | Status |
|-------|--------|
| Nonce uniqueness per operation | ✅ `random_bytes(24)` each encrypt call |
| Nonce length (24 bytes for XSalsa20) | ✅ Correct |
| Key length validation (32 bytes) | ✅ `strlen($key) !== 32` check |
| AEAD (authenticated encryption) | ✅ `sodium_crypto_secretbox` is AEAD |
| Memory zeroing | ✅ `sodium_memzero()` used consistently |
| Base64 strict mode | ✅ `base64_decode($x, true)` |
| Error handling — auth failure returns null | ✅ |
| No homegrown crypto | ✅ Uses libsodium |

## Summary

**Protects against:** Backblaze B2 breach, physical disk theft, storage misconfiguration, unathorized DB access to metadata.

**Does NOT protect against:** Full server compromise (root + APP_KEY access), memory scraping during active decryption, malicious insider with both filesystem and APP_KEY.
