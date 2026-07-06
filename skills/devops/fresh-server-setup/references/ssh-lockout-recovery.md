# SSH Lockout Recovery

When SSH hardening goes wrong and your (the agent's) key is rejected.

## Root Cause

### Cause 1: Deleted sshd_config.d overrides
Deleting `/etc/ssh/sshd_config.d/*.conf` on modern Ubuntu (24.04+) can break root key-based authentication because cloud-init places critical overrides there (e.g., `PermitRootLogin yes`, `PasswordAuthentication` settings). The `sed` operations on the main `sshd_config` may not properly activate if the override files were the ones actually governing the behavior.

### Cause 2: Coolify installer SSH key generation
Coolify v4's install script (step 8/9 "Checking SSH key for localhost access") generates a dedicated SSH keypair for localhost Docker access. This process can occasionally race with or trigger an `sshd` restart that temporarily invalidates existing key-based sessions. The agent's key may still be present in `authorized_keys` but sshd rejects it until a restart.

## Actual Incident

In a real session (2026-07-06, Hetzner Ubuntu 26.04 VPS):

1. During SSH hardening, `rm -f /etc/ssh/sshd_config.d/*.conf` was run
2. `/etc/ssh/sshd_config` was modified with `sed` to set `PermitRootLogin prohibit-password`
3. `systemctl restart sshd` succeeded
4. Next SSH attempt: `root@<IP>: Permission denied (publickey)`
5. Verbose debug showed the key was offered but server rejected it

The `ssh -v` output showed:
```
debug1: Offering public key: ... ED25519 ... explicit
debug1: Authentications that can continue: publickey
debug1: No more authentication methods to try.
root@95.217.216.197: Permission denied (publickey).
```

## Recovery Steps

**The user must help** — the agent cannot reconnect on its own.

1. Ask the user to SSH in using **their own key** (the one provisioned via Hetzner/DigitalOcean console):

   ```bash
   ssh root@<IP>
   ```

2. Check the actual active SSH configuration:

   ```bash
   sshd -T | grep -E "permitrootlogin|pubkeyauthentication|authorizedkeysfile"
   ```

3. Verify the agent's public key is in authorized_keys:

   ```bash
   cat ~/.ssh/authorized_keys
   ```

4. If missing, re-add the agent's public key:

   ```bash
   echo '<agent-public-key>' >> ~/.ssh/authorized_keys
   ```

5. Check if any sshd_config.d overrides are missing/inconsistent:

   ```bash
   ls -la /etc/ssh/sshd_config.d/
   ```

6. Fix by adding a minimal override file:

   ```bash
   echo "PermitRootLogin prohibit-password" > /etc/ssh/sshd_config.d/99-agent.conf
   echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config.d/99-agent.conf
   systemctl restart sshd
   ```

7. Verify the agent can now connect:

   ```bash
   ssh -i ~/.ssh/hermes_<key> root@<IP> "echo RECOVERED"
   ```

## Prevention

- **Never run** `rm -f /etc/ssh/sshd_config.d/*.conf`
- Add targeted override files to `sshd_config.d/` instead (e.g., `99-hardening.conf`)
- Always verify with `sshd -t` AND a new SSH connection before declaring hardening "done"
- Use `sed -i "s/^#\?<directive>.*/<directive> <value>/"` to handle both commented and uncommented lines safely
