#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_database=${1:-$repo_root/extracted/cta.sqlite}
output=${PUBLIC_ARTIFACT_DIR:-$repo_root/artifacts/public}
mkdir -p "$output"
python3 "$repo_root/scripts/prepare-public-database.py" "$source_database" "$output/cta.sqlite"
database_hash=$(sha256sum "$output/cta.sqlite" | cut -d' ' -f1)
python3 - "$output/import-manifest.json" "$database_hash" "${CTA_GAME_VERSION:-unknown}" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
path, digest, game_version = sys.argv[1:]
Path(path).write_text(json.dumps({"dataVersion": datetime.now(timezone.utc).date().isoformat(), "gameVersion": game_version, "databaseHash": f"sha256:{digest}"}, indent=2) + "\n")
PY
"$repo_root/scripts/validate-public-artifacts.sh" "$output"
printf 'Prepared public release in %s; manual content review is still required.\n' "$output"
