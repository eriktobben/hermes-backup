---
name: smooth-fire-proxy
description: Route outbound traffic through Tobben's Mac Mini (smooth-fire) via SOCKS5 proxy over Tailscale SSH, to bypass Hetzner IP blocks and anti-bot restrictions.
---

# Smooth-fire SOCKS5 Proxy

Route traffic through Tobben's Mac Mini **smooth-fire** (Tailscale IP: `100.71.230.118`) from this Hetzner server via a SSH SOCKS5 tunnel.

## Connection Details

| Detail | Value |
|---|---|
| Mac Mini hostname | smooth-fire |
| Tailscale IP | `100.71.230.118` |
| SSH user | `hermes` |
| Authentication | SSH key (`~/.ssh/id_ed25519`) — already deployed |
| SOCKS5 proxy port | `127.0.0.1:1080` |
| OS | macOS (Darwin smooth-fire.local 21.6.0) |

## Start the SOCKS5 Proxy

Run this to start the SSH tunnel in the background:

```bash
ssh -D 1080 -N -f \
  -o ServerAliveInterval=30 \
  -o ExitOnForwardFailure=yes \
  -o StrictHostKeyChecking=accept-new \
  hermes@100.71.230.118
```

Verify it's running:

```bash
ss -tlnp 'sport = 1080'
# Should show LISTEN on 127.0.0.1:1080
```

## Use the Proxy

### curl (single request)

```bash
curl -s --socks5 127.0.0.1:1080 https://ifconfig.me
```

### curl (all requests in a session)

```bash
export ALL_PROXY="socks5://127.0.0.1:1080"
curl -s https://ifconfig.me  # goes through smooth-fire
```

### Check which IP you're using

```bash
echo "Uten proxy:"
curl -s https://ifconfig.me

echo "Med proxy via smooth-fire:"
curl -s --socks5 127.0.0.1:1080 https://ifconfig.me
```

Expected: proxy should show a different IP (Tobben's home network, not Hetzner).

## Stop the Proxy

```bash
# Find the tunnel process
ps aux | grep "ssh.*-D 1080" | grep -v grep

# Kill it
kill <PID>
```

Or stop all matching:

```bash
pkill -f "ssh.*-D 1080.*hermes@100.71.230.118" 2>/dev/null; echo "Stopped"
```

## Test Connectivity (if it stops working)

```bash
# 1. Is smooth-fire online on Tailscale?
tailscale status | grep smooth-fire
# Should show "online" or "idle"

# 2. Can we SSH?
ssh -o ConnectTimeout=5 hermes@100.71.230.118 "echo OK"

# 3. Restart the tunnel if needed
```

## Troubleshooting

- **"Connection refused"**: Run `tailscale status` to verify smooth-fire is online
- **"Permission denied"**: The SSH key was deployed to `~hermes/.ssh/authorized_keys` on smooth-fire. If it was wiped, re-deploy: copy `~/.ssh/id_ed25519.pub` and ask Tobben to append it.
- **Proxy slow/unresponsive**: The SSH tunnel might have died. Restart it with the command above.
