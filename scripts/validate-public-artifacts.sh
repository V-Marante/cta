#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec python3 "$repo_root/scripts/validate-public-artifacts.py" "${1:-$repo_root/artifacts/public}"
