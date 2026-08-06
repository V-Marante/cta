#!/usr/bin/env bash
set -euo pipefail
image=${1:-${RELEASE_IMAGE:-cta-api:local}}
docker run --rm --entrypoint sh "$image" -c 'find /app -xdev -type f -printf "%p %s bytes\n" | sort'
