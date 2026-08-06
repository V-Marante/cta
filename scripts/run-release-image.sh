#!/usr/bin/env bash
set -euo pipefail
command -v docker >/dev/null || { printf 'Missing required command: docker\n' >&2; exit 1; }
[[ -n ${RELEASE_IMAGE:-} ]] || { printf 'Set RELEASE_IMAGE to the exact image tag to run.\n' >&2; exit 1; }
port=${PORT:-8080}
exec docker run --rm --read-only --tmpfs /tmp --publish "127.0.0.1:$port:8080" "$RELEASE_IMAGE"
