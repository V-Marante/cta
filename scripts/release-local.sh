#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
for command in python3 dotnet npm docker curl sha256sum git; do command -v "$command" >/dev/null || { printf 'Missing required command: %s\n' "$command" >&2; exit 1; }; done
if [[ -n "$(git status --porcelain)" ]]; then printf 'Warning: working tree has changes; review them before release.\n' >&2; fi
./scripts/prepare-public-release.sh "${SOURCE_DATABASE:-extracted/cta.sqlite}"
./scripts/verify.sh
./scripts/build-production-image.sh
./scripts/smoke-test-image.sh
printf '\nRelease validation complete. No upload or deployment was performed.\n'
printf 'Database: '; sha256sum "${PUBLIC_ARTIFACT_DIR:-artifacts/public}/cta.sqlite"
if [[ -d local/proprietary/public-assets ]]; then find local/proprietary/public-assets -type f -print0 | sort -z | xargs -0 -r sha256sum; fi
printf 'After manual review, run publish-assets.sh and deploy-fly-image.sh separately with --execute.\n'
