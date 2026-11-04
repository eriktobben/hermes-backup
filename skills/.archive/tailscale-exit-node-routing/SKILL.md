---
name: tailscale-exit-node-routing
description: "Route outbound traffic (curl, browser, API calls) through a remote Tailscale-connected machine to bypass IP-based restrictions. Covers Tailscale SSH, Exit Node approval, SOCKS5 proxy tunnels, and diagnostic checks. Use when a remote server's IP is blocked/rate-limited and a home/office machine on the same tailnet can serve as an egress point."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tailscale, vpn, proxy, networking, ip-bypass, exit-node]
    related_skills: [hermes-agent]
---

# Tailscale Exit Node Routing

## Overview

When this server's public IP gets blocked by anti-bot measures, rate-limited, or restricted by geo-checks, you can route traffic through a **Tailscale Exit Node** — typically a Mac Mini, laptop, or desktop at the user's home — so requests appear to come from their home network instead of a cloud datacenter.

Two approaches, from simplest to most capable:

| Approach | What it gives you | Setup effort |
|----------|-------------------|-------------|
| **Exit Node** | All traffic routed through the remote machine | Low (enable + approve) |
| **SOCKS5 tunnel** | Selective traffic routing (per-command, per-curl) | Medium (Tailscale SSH + tunnel) |

## When to Use

- A website/service blocks the Hetzner/cloud IP and you need residential IP egress
- Rate limiting based on datacenter ASN
- Geo-restricted content that needs to appear from the user's home country
- User has a Mac/PC at home on the same Tailscale network

**Don't use for:** tasks where the current IP works fine, or where latency matters (residential uplinks are slower).

## Prerequisites

- The user's machine **must be on the same Tailscale tailnet** as this server
- The remote machine must be **online and reachable** (`tailscale status` shows `-` not `offline`)
- For Tailscale SSH: the user enables it in their macOS/Windows Tailscale settings
- For Exit Node: the user enables it in Tailscale settings AND admin console approves it

## Discovery: Check Tailscale State

```bash
# Quick overview of all devices and their status
tailscale status

# Parseable JSON with rich peer metadata
tailscale status --json | python3 -m json.tool
```

Key fields from the JSON output:

| Field | What it tells you |
|-------|-------------------|
| `Peer[].Online` | Is the machine reachable right now? |
| `Peer[].ExitNode` | True if THIS server is currently using it as exit node |
| `Peer[].ExitNodeOption` | True if the peer advertises exit node availability |
| `Peer[].Capabilities` | List of cap URLs; look for `ssh` to detect Tailscale SSH |
| `Peer[].OS` | linux / macOS / iOS / android |

**Quick check for exit nodes:**

```bash
tailscale exit-node list
```

## Approach A: Tailscale Exit Node (simple, full routing)

**User-side setup:**
1. On the remote machine: open Tailscale → Settings → enable "Use as Exit Node"
2. In Tailscale admin console (https://login.tailscale.com/admin/machines): select the machine → approve exit node
3. On this server, set it as the exit node:
   ```bash
   tailscale set --exit-node=<tailscale-ip>
   tailscale set --exit-node-allow-lan-access=true  # optional: keep LAN access
   ```

**Verify:**
```bash
curl -s https://ifconfig.me       # should show the remote machine's public IP
```

## Approach B: SOCKS5 Proxy via Tailscale SSH (selective routing)

Two sub-approaches depending on what's available on the Mac:

### B1: Tailscale SSH (simplest, no password setup)

**User-side setup (one time):**
1. Open Tailscale on the remote Mac → **Settings** → **Tailscale SSH** → toggle ON
2. If the toggle is missing: update Tailscale or use B2 below

### B2: macOS Remote Login + SSH Keys (fallback when Tailscale SSH unavailable)

**User-side setup (one time):**

1. **Enable Remote Login:** System Settings → General → Sharing → Remote Login → ON
2. **Create a dedicated user (optional):** System Settings → Users & Groups → Add Account (type: Standard). User can be named e.g. `hermes` or `tunnel`.
3. **Add the agent's SSH public key** to the user's authorized_keys:
   ```bash
   # Get the public key from the agent and run on the Mac:
   sudo -u hermes mkdir -p ~hermes/.ssh
   echo "<agent-public-key>" | sudo -u hermes tee -a ~hermes/.ssh/authorized_keys
   sudo chmod 700 ~hermes/.ssh
   sudo chmod 600 ~hermes/.ssh/authorized_keys
   ```

**Server-side setup (this machine):**

```bash
# Verify SSH works (no password prompt)
ssh -o StrictHostKeyChecking=accept-new hermes@<tailscale-ip> "echo SSH OK"

# Start a persistent SOCKS5 proxy (binds to localhost:1080)
ssh -D 1080 -N -q -C hermes@<tailscale-ip> &
```

**Using the proxy:**

```bash
# curl
curl -x socks5h://localhost:1080 https://ifconfig.me

# Browser: set SOCKS5 proxy to localhost:1080
# python requests
#   proxies = {"http": "socks5://localhost:1080", "https": "socks5://localhost:1080"}
```

## Common Pitfalls

1. **Tailscale SSH not enabled (no passwordless login)** — The user MUST toggle it on in their Tailscale desktop app settings. If the toggle is missing, the Tailscale version may be old; use macOS Remote Login + SSH keys instead (Approach B2).
2. **SSH does NOT accept passwords via stdin in non-interactive mode** — When running SSH from an automated agent (terminal tool, subprocess, script), SSH ignores stdin for password prompts and opens /dev/tty directly. You cannot pipe a password or use heredocs. Always use SSH keys (Approach B2) or Tailscale SSH (B1).
3. **Exit Node not approved in admin console** — Even if the machine advertises exit node, the tailnet admin must approve it at https://login.tailscale.com/admin/machines
4. **Remote machine goes to sleep** — macOS machines can sleep after inactivity; the user may need to adjust Energy Saver settings. Ping it first: `ping -c 2 <tailscale-ip>`
5. **SOCKS5 tunnel drops** — Start it via `autossh` or a process supervisor for long-lived use
6. **Exit node requires sudo to set** — `tailscale set --exit-node=<ip>` requires root. Set an operator once: `sudo tailscale set --operator=$USER` so subsequent calls work without sudo.
7. **`tailscale exit-node list` returns empty** — Either the remote machine hasn't enabled "Use as Exit Node" in its settings, or the admin hasn't approved it yet

## Verification Checklist

- [ ] `tailscale status` shows remote machine as online
- [ ] Exit Node approach: `curl -s https://ifconfig.me` returns the remote machine's IP
- [ ] SOCKS5 approach: `curl -x socks5h://localhost:1080 -s https://ifconfig.me` returns remote IP
- [ ] The target website loads without IP-block errors through the tunnel
