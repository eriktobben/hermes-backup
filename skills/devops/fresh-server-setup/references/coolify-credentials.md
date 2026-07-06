# Coolify Credential Delivery

When installing Coolify non-interactively on a headless server, the admin password is auto-generated and must be delivered to the user securely.

## Credential Generation Pattern

```bash
export ROOT_USERNAME="admin"
export ROOT_USER_EMAIL="user@example.com"
export ROOT_USER_PASSWORD=$(openssl rand -base64 24)
```

The `openssl rand -base64 24` produces a 32-character random alphanumeric string (e.g., `L95YYHZ7dpbj07j7aM9RDUw/EYCJXN8I`).

## Delivery

- Print credentials in the SSH command output so they appear in the agent's tool result
- The agent must **repeat the credentials clearly** to the user in their final response
- Remind the user to save them in a password manager
- The `.env` file is stored at `/data/coolify/source/.env` on the server — tell the user to back this up

## After Install

First login at `http://<server-ip>:8000` triggers Coolify's **onboarding wizard**:

1. Click "Let's go!" to start
2. **Select "This Machine"** as the server type (Coolify runs on the same machine)
3. Create a project or click "Skip Setup"
4. You'll land on the dashboard

### Configure Domain

Do NOT install Caddy/Nginx — Coolify v4 ships its own **Traefik** reverse proxy handling ports 80/443 with auto-SSL.

1. Go to **Settings → Configuration** (sidebar → Settings)
2. Set **URL** to `https://<your-domain>` (e.g. `https://apps.vivalto.no`)
3. Click **Save**
4. Coolify auto-generates Traefik config at `/data/coolify/proxy/dynamic/coolify.yaml`
5. Let's Encrypt SSL is issued on first external request

Access via `https://<your-domain>/login` once DNS propagates.

Reference: `references/coolify-onboarding-treafik.md` for detailed Traefik config inspection and troubleshooting.
