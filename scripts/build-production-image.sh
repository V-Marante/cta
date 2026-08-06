#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
artifact_dir=${PUBLIC_ARTIFACT_DIR:-artifacts/public}
image=${RELEASE_IMAGE:-cta-api:local}
./scripts/validate-public-artifacts.sh "$artifact_dir"
database_hash="sha256:$(sha256sum "$artifact_dir/cta.sqlite" | cut -d' ' -f1)"
docker build --pull --tag "$image" \
  --build-arg "PUBLIC_DATABASE=$artifact_dir/cta.sqlite" \
  --build-arg "APPLICATION_VERSION=${APPLICATION_VERSION:-0.1.0}" \
  --build-arg "VCS_REF=${VCS_REF:-unknown}" \
  --build-arg "DATA_IMPORT_ID=${DATA_IMPORT_ID:-unknown}" \
  --build-arg "GAME_VERSION=${CTA_GAME_VERSION:-unknown}" \
  --build-arg "DATABASE_HASH=$database_hash" \
  --build-arg "ASSETS_VERSION=${CTA_ASSETS_VERSION:-unknown}" \
  --build-arg "PORTRAIT_MODE=${CTA_PORTRAIT_MODE:-none}" .
printf 'Built %s with %s\n' "$image" "$database_hash"
