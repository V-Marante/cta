#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

for command in docker python3 sha256sum git; do
  command -v "$command" >/dev/null || { printf 'Missing required command: %s\n' "$command" >&2; exit 1; }
done
[[ -n ${RELEASE_IMAGE:-} ]] || { printf 'Set RELEASE_IMAGE to an immutable image tag.\n' >&2; exit 1; }
[[ -n ${CTA_ASSETS_VERSION:-} && ${CTA_ASSETS_VERSION} != unknown ]] || { printf 'Set CTA_ASSETS_VERSION to the prepared version directory.\n' >&2; exit 1; }
[[ -f web/cta-web/package-lock.json ]] || { printf 'Missing frontend lock file: web/cta-web/package-lock.json\n' >&2; exit 1; }
[[ -f local-release/data/cta.sqlite ]] || { printf 'Missing production database: local-release/data/cta.sqlite\n' >&2; exit 1; }
./scripts/validate-public-artifacts.sh local-release/data
for directory in \
  "local-release/assets/heroes/$CTA_ASSETS_VERSION" \
  "local-release/assets/ui-icons/$CTA_ASSETS_VERSION/jobs" \
  "local-release/assets/ui-icons/$CTA_ASSETS_VERSION/elements"; do
  [[ -d $directory ]] || { printf 'Missing production asset directory: %s\n' "$directory" >&2; exit 1; }
  find "$directory" -type f -name '*.png' -print -quit | grep -q . || { printf 'Production asset directory contains no PNG files: %s\n' "$directory" >&2; exit 1; }
done
if [[ -n $(git status --porcelain) ]]; then printf 'Warning: working tree has changes; review them before release.\n' >&2; fi

database_hash="sha256:$(sha256sum local-release/data/cta.sqlite | cut -d' ' -f1)"
docker build --pull --target runtime --tag "$RELEASE_IMAGE" \
  --build-arg RELEASE_MODE=production \
  --build-arg "ASSETS_VERSION=$CTA_ASSETS_VERSION" \
  --build-arg "APPLICATION_VERSION=${APPLICATION_VERSION:-0.1.0}" \
  --build-arg "VCS_REF=${VCS_REF:-unknown}" \
  --build-arg "DATA_IMPORT_ID=${DATA_IMPORT_ID:-unknown}" \
  --build-arg "GAME_VERSION=${CTA_GAME_VERSION:-unknown}" \
  --build-arg "DATABASE_HASH=$database_hash" .
printf 'Built %s with %s\n' "$RELEASE_IMAGE" "$database_hash"
