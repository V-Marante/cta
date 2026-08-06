#!/usr/bin/env bash
set -euo pipefail
image=${RELEASE_IMAGE:-cta-api:local}
container="cta-api-smoke-$$"
cleanup() { docker rm -f "$container" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker run --detach --name "$container" --publish 127.0.0.1::8080 \
  --env AllowedOrigins__0=http://localhost:5173 "$image" >/dev/null
port=$(docker port "$container" 8080/tcp | sed 's/.*://')
for _ in $(seq 1 30); do
  if curl --fail --silent "http://127.0.0.1:$port/ready" >/dev/null; then break; fi
  sleep 1
done
curl --fail --show-error "http://127.0.0.1:$port/health"
curl --fail --show-error "http://127.0.0.1:$port/ready"
curl --fail --show-error "http://127.0.0.1:$port/api/meta"
curl --fail --show-error "http://127.0.0.1:$port/api/heroes?pageSize=1"
unexpected=$(docker export "$container" | tar -tf - | grep -E '(^|/)(samples|extracted|local/proprietary|\.git|node_modules)(/|$)' || true)
if [[ -n "$unexpected" ]]; then printf 'Unexpected private paths:\n%s\n' "$unexpected" >&2; exit 1; fi
printf '\nContainer smoke test passed for %s\n' "$image"
