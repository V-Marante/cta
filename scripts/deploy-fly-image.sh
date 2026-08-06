#!/usr/bin/env bash
set -euo pipefail
image=${FLY_IMAGE_REF:-}
app=${FLY_APP_NAME:-}
[[ -n "$image" && -n "$app" ]] || { printf 'Set FLY_IMAGE_REF to an already-pushed immutable tag and FLY_APP_NAME.\n' >&2; exit 1; }
if [[ ${1:-} != --execute ]]; then printf 'DRY RUN: flyctl deploy --app %q --image %q\n' "$app" "$image"; exit 0; fi
command -v flyctl >/dev/null || { printf 'Missing flyctl.\n' >&2; exit 1; }
read -r -p "Deploy exact image $image to $app? Type deploy: " confirmation
[[ $confirmation == deploy ]] || { printf 'Cancelled.\n'; exit 1; }
flyctl deploy --app "$app" --image "$image"
