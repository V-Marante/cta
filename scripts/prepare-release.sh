#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

for command in python3 cp find; do command -v "$command" >/dev/null || { printf 'Missing required command: %s\n' "$command" >&2; exit 1; }; done
version=${CTA_ASSETS_VERSION:-}
[[ -n $version && $version != unknown ]] || { printf 'Set CTA_ASSETS_VERSION to an immutable asset version.\n' >&2; exit 1; }
source_database=${SOURCE_DATABASE:-extracted/cta.sqlite}
hero_source=${HERO_ASSET_SOURCE:-local/proprietary/hero-icons}
ui_source=${UI_ASSET_SOURCE:-local/proprietary/ui-icons}
[[ -f $source_database ]] || { printf 'Source database missing: %s\n' "$source_database" >&2; exit 1; }
[[ -d $hero_source ]] || { printf 'Hero asset source missing: %s\n' "$hero_source" >&2; exit 1; }
[[ -d $ui_source/jobs && -d $ui_source/elements ]] || { printf 'UI asset sources missing under: %s\n' "$ui_source" >&2; exit 1; }
find "$hero_source" -maxdepth 1 -type f -name '*.png' -print -quit | grep -q . || { printf 'Hero asset source contains no PNG files.\n' >&2; exit 1; }

PUBLIC_ARTIFACT_DIR=local-release/data CTA_ASSETS_VERSION="$version" ./scripts/prepare-public-release.sh "$source_database"
mkdir -p "local-release/assets/heroes/$version" "local-release/assets/ui-icons/$version/jobs" "local-release/assets/ui-icons/$version/elements"
cp "$hero_source"/*.png "local-release/assets/heroes/$version/"
cp "$ui_source"/jobs/*.png "local-release/assets/ui-icons/$version/jobs/"
cp "$ui_source"/elements/*.png "local-release/assets/ui-icons/$version/elements/"
printf 'Prepared ignored release inputs under local-release/ for asset version %s. Review them before building.\n' "$version"
