#!/usr/bin/env bash
set -euo pipefail
source_dir=${PUBLIC_ASSET_DIR:-local/proprietary/public-assets}
destination=${R2_DESTINATION:-}
[[ -d "$source_dir" ]] || { printf 'Asset directory missing: %s\n' "$source_dir" >&2; exit 1; }
[[ -n "$destination" ]] || { printf 'Set R2_DESTINATION (for example s3://bucket/heroes/version).\n' >&2; exit 1; }
if [[ ${1:-} != --execute ]]; then printf 'DRY RUN: aws s3 sync %q %q --endpoint-url <R2 endpoint>\n' "$source_dir" "$destination"; exit 0; fi
[[ -n ${R2_ENDPOINT_URL:-} ]] || { printf 'Set R2_ENDPOINT_URL.\n' >&2; exit 1; }
command -v aws >/dev/null || { printf 'Missing aws CLI.\n' >&2; exit 1; }
read -r -p "Upload reviewed versioned assets to $destination? Type publish: " confirmation
[[ $confirmation == publish ]] || { printf 'Cancelled.\n'; exit 1; }
aws s3 sync "$source_dir" "$destination" --endpoint-url "$R2_ENDPOINT_URL" --cache-control 'public,max-age=31536000,immutable' --no-progress
