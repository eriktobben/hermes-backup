# Coolify "Degraded (unhealthy)" Service Diagnosis

When a Coolify-managed Docker service shows **Degraded (unhealthy)** in the Coolify UI, it means one or more containers in the stack have failing Docker health checks. This reference covers the diagnostic workflow.

## Quick Overview

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Single container unhealthy | Health check timing or config | Check logs, adjust healthcheck params |
| DB container restarting | Image version vs volume incompatibility | Pin a compatible PostgreSQL version |
| Proxy returns 503/gateway timeout | Traefik not on the service's Docker network | `docker network connect <network> coolify-proxy` |
| App container shows "Created" but not running | Depends on an unhealthy dependency | Fix the dependency first |

## Diagnostic Workflow

### 1. SSH into the Coolify server

Coolify stores SSH keys under `/data/coolify/ssh/` or `~/.ssh/hermes_*`:

```bash
ssh -i ~/.ssh/hermes_<key> root@<IP> "hostname && docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'"
```

### 2. Find the service UUID

From the Coolify UI URL: `.../service/<uuid>` — or on the server, use the container names which contain the UUID:

```bash
docker ps --filter name=<uuid> --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
```

### 3. Read the docker-compose.yml

Coolify stores service stacks under `/data/coolify/services/<uuid>/docker-compose.yml`:

```bash
cat /data/coolify/services/<uuid>/docker-compose.yml
```

Key things to check:
- `image:` tags — are they `:latest` or pinned?
- `healthcheck:` blocks — what tests are configured?
- `depends_on:` — are containers waiting for healthy dependencies?
- `networks:` — is the service on its own network or the proxy network?

### 4. Check container logs

```bash
docker logs <container-name> --tail 50
```

## Common Patterns

### Pattern A: PostgreSQL `:latest` → PG18 volume incompatibility

**Symptom**: PostgreSQL container keeps restarting. Logs show:

```
Error: in 18+, these Docker images are configured to store database data in a
format which is compatible with "pg_ctlcluster"...
Counter to that, there appears to be PostgreSQL data in:
  /var/lib/postgresql/data (unused mount/volume)
```

**Cause**: `postgres:latest` now resolves to PostgreSQL 18+, which uses a new major-version-specific data directory structure (`/var/lib/postgresql/18/docker`). The old volume mounted at `/var/lib/postgresql/data` is incompatible.

**Fix**: Pin a specific PostgreSQL version in docker-compose.yml:

```bash
# On the server, edit the compose file
sed -i "s|image: 'postgres:latest'|image: 'postgres:16-alpine'|g" /data/coolify/services/<uuid>/docker-compose.yml

# Remove the old empty/unused volume
docker volume rm <uuid>_faraday-db 2>/dev/null || true

# Restart the stack
cd /data/coolify/services/<uuid> && docker compose up -d
```

PostgreSQL 15 or 16-alpine are stable choices with broad compatibility.

> **Pitfall**: The `postgres:latest` tag is a moving target. Always pin to a specific major version (e.g., `postgres:16-alpine`) for production services. Coolify's service wizard uses `:latest` by default for database services.

### Pattern B: Traefik not connected to the service Docker network

**Symptom**: Coolify shows "Running (healthy)" but the app is unreachable with a gateway timeout/503.

**Cause**: Coolify's Traefik proxy (`coolify-proxy`) is not attached to the service's Docker network, so it can't route traffic to the app container.

**Diagnosis**:

```bash
# Check which networks Traefik is on
docker inspect coolify-proxy --format '{{range .NetworkSettings.Networks}}{{.NetworkID}} -> {{.IPAddress}}{{"\n"}}{{end}}'

# Check which network the service is on
docker inspect <app-container> --format '{{range .NetworkSettings.Networks}}{{.NetworkID}} -> {{.IPAddress}}{{"\n"}}{{end}}'
```

**Fix**:

```bash
docker network connect <service-network-name> coolify-proxy
docker restart coolify-proxy  # Restart Traefik to pick up the new network
```

> **Pitfall**: `docker network connect` is ephemeral and may be lost on Coolify stack redeploy. The durable fix is to configure the service's docker-compose.yml to use an external network that Traefik is also on, or to set up the service's `networks:` section to include the Coolify proxy network. In Coolify v4, this can be done via "Connect To Predefined Network" checkbox in the service Configuration page.

### Pattern C: Python site-packages vs source directory mismatch

**Symptom**: Editing a Python source file inside a container (e.g., `/src/faraday/server/app.py`) has no effect after `docker restart`.

**Cause**: The running Python process imports from the installed `site-packages` directory (e.g., `/src/.venv/lib/python3.11/site-packages/`), not the source checkout.

**Fix**: Edit the file in `site-packages` as well, or symlink it:

```bash
# Check which file Python actually loads
docker exec <container> python3 -c "import <module>; print(<module>.__file__)"

# Edit the right file
docker exec <container> sed -i 's/old/new/' /path/to/site-packages/<module>.py

# Clear bytecode cache
docker exec <container> find /path/to/site-packages -path "*/<module>/__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Restart
docker restart <container>
```

## Verification

After fixes:

```bash
# All containers healthy?
docker ps --filter name=<uuid> --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# App responds?
curl -sk --connect-timeout 10 https://<domain>/
curl -sk --connect-timeout 10 https://<domain>/_api/config  # Faraday-specific health endpoint

# Check Coolify UI (wait a minute for status refresh)
```
