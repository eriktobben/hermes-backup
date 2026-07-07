# Coolify HTTP Error Troubleshooting

Debug HTTP errors (429, 503, 502, 504) from applications deployed behind Coolify's reverse proxy.

## Quick Reference

| HTTP Status | Most Likely Cause | First Check |
|-------------|------------------|-------------|
| **429** Too Many Requests | Application-level rate limiter (Rack::Attack, rate-limiter middleware) | Check app container's rate limit config |
| **503** Service Unavailable | Container still starting / health check failing | Check `docker ps` status column |
| **502** Bad Gateway | App crashed or port mismatch | Check Traefik labels for correct `loadbalancer.server.port=PORT` |
| **504** Gateway Timeout | App too slow, `RAILS_MAX_THREADS` too low | Check app logs for slow queries |

---

## Identifying the Proxy

Coolify v4 uses **Traefik** by default (`coolify-proxy` container). It may also apply Caddy labels on containers for compatibility. Both label sets can coexist.

```bash
# Check which proxy is actually proxying
docker ps --filter name=coolify-proxy --format "{{.Image}}"
# Output: traefik:v3.x → Traefik
#         caddy:latest  → Caddy
```

To determine what handles a service:

```bash
# Check Docker labels on a service container
docker inspect <container> --format '{{json .Config.Labels}}' | \
  python3 -c "import sys,json; [print(k+':',v) for k,v in json.load(sys.stdin).items() if 'traefik' in k.lower() or 'caddy' in k.lower()]"
```

If Traefik labels are present, Traefik handles routing. If only Caddy labels are present, Caddy handles routing. Coolify sometimes generates **both**, in which case Traefik is still the active proxy (it binds ports 80/443 on `coolify-proxy`).

---

## Rate Limiting (429) Debugging

### Step 1 — Is it the proxy or the app?

```bash
# Test the endpoint repeatedly to trigger rate limits
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "Req $i: %{http_code}\n" https://<domain>/<path>
done
```

### Step 2 — Check Traefik middleware

```bash
docker inspect <app-container> --format '{{json .Config.Labels}}' | \
  python3 -c "import sys,json; print([v for k,v in json.load(sys.stdin).items() if 'middleware' in k.lower() and 'ratelimit' in v.lower()])"
```

If no Traefik rate-limit middleware is found, the 429 comes from **inside the app**.

### Step 3 — Check app-level rate limiting (Rack::Attack for Rails)

```bash
docker exec <app-container> find /app -path "*/initializers/rack_attack*" 2>/dev/null
```

If found, inspect it:

```bash
docker exec <app-container> cat /app/config/initializers/rack_attack.rb
```

Common Chatwoot widget rate limit (very aggressive — 5 req/hour/IP):

```ruby
throttle('widget?...', limit: 5, period: 1.hour) do |req|
  req.ip if req.path_without_extensions == '/widget' && params['cw_conversation'].blank?
end
```

### Step 4 — Fix: disable widget rate limiting

Chatwoot's `rack_attack.rb` checks for `ENABLE_RACK_ATTACK_WIDGET_API`. Set to `false` to disable widget rate limiting entirely:

```bash
# Add to service's .env file
echo "ENABLE_RACK_ATTACK_WIDGET_API=false" >> /data/coolify/services/<uuid>/.env

# Recreate containers to pick up the new env var
cd /data/coolify/services/<uuid> && docker compose up -d <app-service>
```

### Step 5 — Verify

```bash
# Wait for healthy status
docker ps --filter name=<app> --format "{{.Names}} {{.Status}}"

# Confirm env var is loaded
docker exec <app-container> env | grep RACK_ATTACK

# Test rate limiting is gone
for i in $(seq 1 10); do
  curl -s -o /dev/null -w "Req $i: %{http_code}\n" https://<domain>/<path>
done
# Should all return 200
```

---

## Service Unavailable (503) Debugging

503 typically means the container isn't ready yet:

```bash
# Check container health status
docker ps --filter name=<app> --format "{{.Names}}\t{{.Status}}"
# "(health: starting)"  → still booting
# "(unhealthy)"         → app crashed or port mismatch
# "Up X minutes"        → healthy

# Check logs
docker logs <app-container> --tail 50

# Verify Traefik port label matches app port
docker inspect <app-container> --format '{{index .Config.Labels "traefik.http.services.https-0-<uuid>.<service>.loadbalancer.server.port"}}'
```

---

## Adding Environment Variables to Coolify Services

Coolify services read from: the `environment:` block in docker-compose.yml + `.env` files.

### Via .env file (persistent across Coolify re-deploys)

```bash
# Find the service directory (hash-based UUID)
ls /data/coolify/services/

# Append env var
echo "VAR_NAME=value" >> /data/coolify/services/<uuid>/.env

# Recreate containers
cd /data/coolify/services/<uuid> && docker compose up -d
```

### Via docker-compose.yml (overwritten on Coolify re-deploy)

For temporary fixes only — Coolify regenerates the compose file during re-deployment.

---

## Useful Diagnostic Commands

```bash
# Full label dump for any container
docker inspect <container> --format '{{json .Config.Labels}}' | python3 -m json.tool

# Environment variables inside running container
docker exec <container> env | grep -i 'RACK\|RATE\|LIMIT\|ATTACK'

# Find Traefik dynamic config location
docker exec coolify-proxy find /traefik/dynamic -name "*.yaml"

# Check Docker compose file for a service
cat /data/coolify/services/<uuid>/docker-compose.yml

# Reset Redis-based rate limit counters (if Rack::Attack uses Redis)
docker exec <redis-container> redis-cli -a $REDIS_PASSWORD KEYS "rack:attack:*" 2>/dev/null | xargs -r docker exec <redis-container> redis-cli -a $REDIS_PASSWORD DEL 2>/dev/null
```
