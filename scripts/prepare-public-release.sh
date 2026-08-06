#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_database=${1:-$repo_root/extracted/cta.sqlite}
output=${PUBLIC_ARTIFACT_DIR:-$repo_root/artifacts/public}
mkdir -p "$output"
python3 "$repo_root/scripts/prepare-public-database.py" "$source_database" "$output/cta.sqlite"
database_hash=$(sha256sum "$output/cta.sqlite" | cut -d' ' -f1)
python3 - "$output/cta.sqlite" "$output/import-manifest.json" "$database_hash" "${CTA_ASSETS_VERSION:-unknown}" <<'PY'
import json, sqlite3, sys
from pathlib import Path
database, path, digest, assets_version = sys.argv[1:]
with sqlite3.connect(f"file:{Path(database).resolve()}?mode=ro", uri=True) as db:
    import_id, game_version, finished_at = db.execute("SELECT id,game_version,finished_at FROM release_info").fetchone()
Path(path).write_text(json.dumps({
    "dataVersion": finished_at[:10], "dataImportId": import_id,
    "gameVersion": game_version, "databaseHash": f"sha256:{digest}",
    "assetsVersion": assets_version,
}, indent=2) + "\n")
PY
"$repo_root/scripts/validate-public-artifacts.sh" "$output"
printf 'Prepared public release in %s; manual content review is still required.\n' "$output"
