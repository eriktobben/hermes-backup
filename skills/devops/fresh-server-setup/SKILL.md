---
name: fresh-server-setup
description: Provision a fresh Linux VPS (Hetzner, DigitalOcean, etc.) with security hardening, Docker, Coolify, and Traefik/auto-SSL.
category: devops
---

# Fresh Server Setup

Provision a brand-new Linux VPS from scratch — security hardening, Docker, Coolify, and Traefik with auto-SSL.

## Trigger

- User wants to set up a new VPS server
- User wants Coolify installed on a fresh machine
- User needs SSH access granted to you (the agent)

## Workflow

### 1. Initial Server Access

1. After user creates the server, generate an SSH keypair for your use:

   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/hermes_<server> -N "" -C "hermes-<server>"
   ```

2. Share the **public key** with the user and ask them to add it to `~/.ssh/authorized_keys` on the server.

3. **Verify connectivity**:

   ```bash
   ssh -i ~/.ssh/hermes_<server> -o StrictHostKeyChecking=accept-new root@<IP> "echo OK; cat /etc/os-release; hostname"
   ```

4. Get the **domain** the user wants to use and check DNS resolution:

   ```bash
   dig +short <domain> A
   ```

### 2. System Updates & Base Packages

```bash
ssh -i ~/.ssh/hermes_<server> root@<IP> '
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    ufw fail2ban unattended-upgrades curl wget git htop
'
```

### 3. Security Hardening

```bash
ssh -i ~/.ssh/hermes_<server> root@<IP> '
# UFW
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment "SSH"
ufw allow 80/tcp comment "HTTP"
ufw allow 443/tcp comment "HTTPS"
ufw allow 8080/tcp comment "Coolify direct"
ufw --force enable

# Unattended upgrades
cat > /etc/apt/apt.conf.d/20auto-upgrades << "EOFA"
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOFA

# SSH hardening — WARNING: see PITFALLS below
# Do NOT delete sshd_config.d overrides!
sed -i "s/^#\?PasswordAuthentication.*/PasswordAuthentication no/" /etc/ssh/sshd_config
sed -i "s/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/" /etc/ssh/sshd_config
sed -i "s/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/" /etc/ssh/sshd_config
sed -i "s/^#\?MaxAuthTries.*/MaxAuthTries 3/" /etc/ssh/sshd_config
sed -i "s/^#\?ClientAliveInterval.*/ClientAliveInterval 300/" /etc/ssh/sshd_config
sed -i "s/^#\?ClientAliveCountMax.*/ClientAliveCountMax 2/" /etc/ssh/sshd_config

# Verify config before restart
sshd -t && systemctl restart sshd

# Fail2ban
cat > /etc/fail2ban/jail.local << "EOFB"
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
maxretry = 3
bantime = 86400
EOFB
systemctl restart fail2ban
'
```

### 4. Docker Installation

```bash
ssh -i ~/.ssh/hermes_<server> root@<IP> '
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
docker --version
docker compose version
'
```

### 5. Coolify Installation

Install with pre-set credentials for non-interactive headless setup:

```bash
ssh -i ~/.ssh/hermes_<server> root@<IP> '
export ROOT_USERNAME="admin"
export ROOT_USER_EMAIL="<user@domain>"
export ROOT_USER_PASSWORD=$(openssl rand -base64 24)
export AUTOUPDATE="true"

# Print credentials for delivery to user
echo "Coolify admin: $ROOT_USERNAME"
echo "Coolify pass: $ROOT_USER_PASSWORD"

curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
'
```

> Save the generated password — deliver it to the user securely.

### 6. Configure Domain via Coolify Web UI

⚠️ **Coolify v4 manages its own Traefik proxy on ports 80/443.** Do NOT install Caddy or Nginx — Coolify already handles reverse proxying and Let's Encrypt SSL automatically once you set the domain in its settings.

After Coolify install and first login, you must complete the onboarding wizard and set the FQDN:

1. Access Coolify at `http://<IP>:8000` in a browser
2. Log in with the credentials from step 5
3. Complete the **onboarding wizard**:
   - Click "Let's go!" → Select "This Machine" → Create project or "Skip Setup"
4. Navigate to **Settings → Configuration** (sidebar → Settings)
5. In the **URL** field, enter `https://<domain>` (e.g., `https://apps.vivalto.no`)
6. Click **Save**
7. Coolify auto-generates Traefik dynamic config at `/data/coolify/proxy/dynamic/coolify.yaml`
8. Let's Encrypt SSL certificate is issued on first external HTTPS request

Verify the configuration took effect:

```bash
# From the server itself
curl -sI --resolve <domain>:443:127.0.0.1 https://<domain>

# Should return: HTTP/2 302 → Location: https://<domain>/login
```

Check the generated Traefik config:

```bash
cat /data/coolify/proxy/dynamic/coolify.yaml
```

You should see routers for `<domain>` with `certresolver: letsencrypt` on HTTPS entrypoints.

## Pitfalls

### 🚨 CRITICAL: SSH lockout risk

**DO NOT** delete or remove files from `/etc/ssh/sshd_config.d/` — modern Ubuntu/Debian ships cloud-init overrides there that may set `PermitRootLogin yes` or similar. Deleting them can cause the **agent's own SSH key to be rejected**, locking the agent (and potentially the user) out.

**Correct approach**: Only modify `/etc/ssh/sshd_config` directly using `sed` with the `^#\\?` pattern to handle both commented and uncommented lines. Never run `rm -f /etc/ssh/sshd_config.d/*.conf`.

**Additional lockout trigger**: The Coolify installer (step 8/9 "Checking SSH key for localhost access") generates its own SSH key and may trigger an sshd restart or race condition that temporarily invalidates existing key-based connections. If SSH fails immediately after Coolify install, ask the user to verify keys are present and restart sshd.

If lockout happens:
- Ask the user to SSH in using their own key (from Hetzner/DigitalOcean console) and verify authorized_keys
- Check `sshd -T | grep permitrootlogin` to confirm the actual active config
- Check `cat ~/.ssh/authorized_keys` to ensure the agent's key is present
- Restore any needed overrides in sshd_config.d/ or create a `99-hardening.conf` file
- Run `systemctl restart sshd` after any authorized_keys changes

### Coolify install blocks on missing TTY

The Coolify install script may warn about `debconf: unable to initialize frontend: Dialog` — this is harmless in headless mode. Pre-setting env vars (`ROOT_USERNAME`, `ROOT_USER_EMAIL`, `ROOT_USER_PASSWORD`) avoids interactive prompts.

### DNS must resolve before proxy setup

Verify the domain points to the server IP *before* configuring Caddy, or Let's Encrypt certificate issuance will fail.

### UFW may block Docker networking

Docker manipulates iptables directly. If Docker networking breaks after UFW enable, check `/etc/ufw/after.rules` for Docker chain integration. Usually Docker + UFW works out of the box on modern systems.

## Verification

- ✅ SSH key-based login works after hardening: `ssh -i ~/.ssh/hermes_<server> root@<IP> "echo OK"`
- ✅ UFW active: `ufw status verbose`
- ✅ Fail2ban active: `fail2ban-client status sshd`
- ✅ Docker running: `docker ps`
- ✅ Coolify accessible: `curl -sI http://localhost:8000` (from server)
- ✅ Domain accessible via HTTPS: `curl -sI https://<domain>` (external)
- ✅ Traefik config generated: `cat /data/coolify/proxy/dynamic/coolify.yaml`
- ✅ SSL valid: `curl -vI https://<domain> 2>&1 | grep "SSL certificate"`

## References

- `references/ssh-lockout-recovery.md` — Detailed recovery steps if SSH hardening or Coolify installer causes a lockout
- `references/coolify-credentials.md` — How credentials are generated, delivered, and used post-install
- `references/coolify-onboarding-traefik.md` — First-login onboarding wizard, domain setup through Coolify UI, Traefik config inspection, and SSL troubleshooting
- `references/coolify-service-credentials.md` — Patterns for finding and recovering credentials for Coolify-deployed services (Umami, etc.), including direct database password reset for Umami v3