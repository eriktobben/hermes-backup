# Coolify Onboarding & Traefik Domain Setup

Coolify v4 ships with its own **Traefik** reverse proxy container (`coolify-proxy`) that manages ports 80/443 with automatic Let's Encrypt SSL. No Caddy or Nginx needed.

## First Login (Onboarding Wizard)

After install, the first user to log in at `http://<IP>:8000/login` triggers an onboarding wizard.

### Step-by-step

1. **Log in** with the admin credentials from installation
2. **Welcome screen** → Click **"Let's go!"**
3. **Choose Server Type** → Select **"This Machine"** (Quick Start)
   - This registers the localhost server so Coolify can deploy on itself
4. **Project Setup** → Click **"Create My First Project"** or **"Skip Setup"**
5. You land on the **Dashboard**

### What "This Machine" does

- Registers `localhost` as a server in Coolify's database
- Uses the SSH key generated during installation (step 8/9) for localhost access
- Enables deploying applications directly on the Coolify host

## Domain Configuration

### Via Web UI (Settings)

1. Navigate to **Settings → Configuration** (sidebar → Settings)
2. In the **General** tab, find the **URL** field
3. Enter `https://<your-domain>` (e.g., `https://apps.vivalto.no`)
4. Click **Save**
5. Coolify generates/updates `/data/coolify/proxy/dynamic/coolify.yaml`

### What Coolify generates

The generated Traefik YAML creates:

```yaml
http:
  middlewares:
    redirect-to-https:
      redirectscheme:
        scheme: https
    gzip:
      compress: true
  routers:
    coolify-http:
      middlewares:
        - redirect-to-https
      entryPoints:
        - http
      service: coolify
      rule: Host(`<domain>`)
    coolify-https:
      entryPoints:
        - https
      service: coolify
      rule: Host(`<domain>`)
      tls:
        certresolver: letsencrypt
    coolify-realtime-ws:
      entryPoints:
        - http
      service: coolify-realtime
      rule: 'Host(`<domain>`) && PathPrefix(`/app`)'
    coolify-realtime-wss:
      entryPoints:
        - https
      service: coolify-realtime
      rule: 'Host(`<domain>`) && PathPrefix(`/app`)'
      tls:
        certresolver: letsencrypt
    coolify-terminal-ws:
      entryPoints:
        - http
      service: coolify-terminal
      rule: 'Host(`<domain>`) && PathPrefix(`/terminal/ws`)'
    coolify-terminal-wss:
      entryPoints:
        - https
      service: coolify-terminal
      rule: 'Host(`<domain>`) && PathPrefix(`/terminal/ws`)'
      tls:
        certresolver: letsencrypt
  services:
    coolify:
      loadBalancer:
        servers:
          - url: 'http://coolify:8080'
    coolify-realtime:
      loadBalancer:
        servers:
          - url: 'http://coolify-realtime:6001'
    coolify-terminal:
      loadBalancer:
        servers:
          - url: 'http://coolify-realtime:6002'
```

## Verification

```bash
# Check Traefik dynamic config exists
cat /data/coolify/proxy/dynamic/coolify.yaml

# Test from server (DNS must resolve or use --resolve)
curl -sI --resolve <domain>:443:127.0.0.1 https://<domain>
# Expect: HTTP/2 302 → Location: https://<domain>/login

# Test HTTP redirect
curl -sI --resolve <domain>:80:127.0.0.1 http://<domain>
# Expect: HTTP/1.1 307 → Location: https://<domain>/

# External test (requires public DNS)
curl -sI https://<domain>
# Expect: HTTP/2 302 with Set-Cookie headers
```

## SSL Certificates

Let's Encrypt certificates are stored in `/data/coolify/proxy/acme.json` (owned by uid 9999, not readable by root). They are automatically renewed by Traefik.

The first external HTTPS request triggers certificate issuance. Until then, Traefik may serve a self-signed cert.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Port 443 in use | Caddy/Nginx installed separately | Stop/remove other proxy: `systemctl stop caddy` |
| "Server Error" on save | .env file not writable | Check permissions: `/data/coolify/source/.env` |
| SSL cert not issued | DNS not propagated | Verify: `dig +short <domain> A` |
| 404 on domain | Router not created | Re-save URL in Settings |
| HTTP not redirecting | Traefik config stale | Check `coolify.yaml` exists; restart coolify proxy |
