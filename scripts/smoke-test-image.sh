#!/usr/bin/env bash
set -euo pipefail
image=${RELEASE_IMAGE:-cta-api:local}
container="cta-api-smoke-$$"
cleanup() { docker rm -f "$container" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker run --detach --name "$container" --publish 127.0.0.1::8080 \
  --read-only --tmpfs /tmp "$image" >/dev/null
port=$(docker port "$container" 8080/tcp | sed 's/.*://')
for _ in $(seq 1 30); do
  if curl --fail --silent "http://127.0.0.1:$port/ready" >/dev/null; then break; fi
  sleep 1
done
curl --fail --show-error "http://127.0.0.1:$port/health"
curl --fail --show-error "http://127.0.0.1:$port/ready"
curl --fail --show-error "http://127.0.0.1:$port/api/meta"
curl --fail --show-error "http://127.0.0.1:$port/api/heroes?pageSize=1"
curl --fail --show-error "http://127.0.0.1:$port/"
curl --fail --show-error "http://127.0.0.1:$port/team-planner"
portrait_path=$(curl --fail --silent "http://127.0.0.1:$port/api/heroes?pageSize=1" | python3 -c 'import json,sys; print(json.load(sys.stdin)["items"][0]["portraitUrl"])')
curl --fail --show-error "http://127.0.0.1:$port$portrait_path" >/dev/null
assets_version=$(curl --fail --silent "http://127.0.0.1:$port/api/meta" | python3 -c 'import json,sys; print(json.load(sys.stdin)["assetsVersion"])')
curl --fail --show-error "http://127.0.0.1:$port/assets/ui-icons/$assets_version/jobs/brawler.png" >/dev/null
curl --fail --show-error "http://127.0.0.1:$port/assets/ui-icons/$assets_version/elements/fire.png" >/dev/null
[[ $(curl --silent --output /dev/null --write-out '%{http_code}' "http://127.0.0.1:$port/assets/missing.png") == 404 ]]
[[ $(curl --silent --output /dev/null --write-out '%{http_code}' "http://127.0.0.1:$port/api/missing") == 404 ]]
unexpected=$(docker export "$container" | tar -tf - | grep -E '(^|/)(samples|extracted|local/proprietary|\.git|node_modules)(/|$)' || true)
if [[ -n "$unexpected" ]]; then printf 'Unexpected private paths:\n%s\n' "$unexpected" >&2; exit 1; fi
printf '\nContainer smoke test passed for %s\n' "$image"
