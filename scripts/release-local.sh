#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
for command in python3 dotnet npm docker curl sha256sum git; do command -v "$command" >/dev/null || { printf 'Missing required command: %s\n' "$command" >&2; exit 1; }; done
[[ -n ${RELEASE_IMAGE:-} ]] || { printf 'Set RELEASE_IMAGE to an immutable image tag.\n' >&2; exit 1; }
./scripts/prepare-release.sh
./scripts/verify.sh
./scripts/build-production-image.sh
./scripts/smoke-test-image.sh
printf '\nUnified release image validated locally; nothing was pushed or deployed.\n'
printf 'Database: '; sha256sum local-release/data/cta.sqlite
