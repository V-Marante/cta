# Crush Them All Game Data Investigation

This workspace contains extraction, import, API, and frontend tooling for locally inspected Crush Them All data. The current extraction route is BlueStacks with its Windows `HD-Adb.exe`; the earlier Google Play Games investigation is retained only as historical provenance.

- Game: `Crush Them All - PVP Idle RPG`
- Android package: `com.godzilab.idlerpg`
- Play Store publisher noted by user: `Imperia Online JSC`
- Rights holder noted by user: `Stillfront Group AB`
- Related developer/company noted by user: `Godzillab` / local package namespace `godzilab`

The original installations were not modified. BlueStacks provided package-scoped, read-only copies of the APK splits and shared runtime data without requiring emulator-image extraction.

## Workspace

- `reports/`: chronological reports; start with `reports/README.md`
- `inventories/files.csv`: machine-readable file inventory
- `inventories/files.json`: JSON equivalent of the file inventory
- `samples/`: copied small samples used for inspection
- `scripts/`: reusable read-only investigation scripts
- `logs/`: reserved for future script logs
- `extracted/`: ignored local importer databases and derived data

## Historical Google Play Games inventory

The commands below reproduce only the original host-level Google Play Games inventory. They are not the current CTA extraction workflow and should not be used to infer the current game corpus.

From WSL:

```bash
python3 scripts/inventory-files.py \
  --source /mnt/c/Users/<windows-user>/AppData/Local/Google/'Play Games' \
  --source /mnt/c/ProgramData/Google/'Play Games' \
  --source /mnt/c/ProgramData/Google/'Play Games Services' \
  --source /mnt/c/'Program Files'/Google/'Play Games' \
  --source /mnt/c/'Program Files'/Google/'Play Games Services' \
  --output-dir inventories \
  --max-hash-size-mb 512
```

From PowerShell:

```powershell
.\scripts\find-game-files.ps1 -OutputDir .\inventories -DryRun
.\scripts\find-game-files.ps1 -OutputDir .\inventories
```

## Current Conclusion

BlueStacks exposed `com.godzilab.idlerpg` through its Windows `HD-Adb.exe`. Version `2.0.821` was reconfirmed on 2026-08-06 as the latest version offered by the installed BlueStacks distribution: no update was available and the launched package reported `versionCode=200821`. Four APKs are retained locally under `samples/bluestacks/apk/`, with approximately 58 MB of accessible runtime content under `samples/bluestacks/shared-data/`. Historical Google Play Games logs observed `2.0.822`; this remains cross-distribution provenance rather than the source version used by the repository.

The game uses the custom native `GodzilabEngine`, not Unity. The retained `cache/content/` contains gameplay CSV/XML files, localization, Spine data, sprite atlases, textures, and animation files. Four ZIP-compatible `.bin` files in `cache/patch/` preserve downloaded patch bundles. The base APK also contains authentic UI and character atlases absent from the materialized cache. See `reports/README.md` and `reports/19-bluestacks-reconciliation.md` before using older reports.

## Importer Infrastructure

The `src/cta_importer/` package provides game-agnostic import infrastructure plus the first CTA vertical slice: English localization, heroes, character skill references, skills, and portrait references. Imports are versioned, validated, provenance-preserving, idempotent, and atomic.

Architecture: `docs/importer-architecture.md`

Future-session handoff: `docs/handoff.md`

## Repository Data Boundary

This repository contains extraction and importer tooling, tests, migrations, and investigation documentation—not the extracted game dataset. Extracted content and proprietary assets are intentionally excluded from Git.

The importer currently expects locally extracted source content at:

```text
samples/bluestacks/shared-data/cache/content/
```

Users must perform their own local extraction. The contents of `samples/`, `assets/`, and `extracted/` remain local and must not be committed. Authentic copied, decoded, or application-ready assets belong under `local/proprietary/`, which is also ignored. Local builds should use authentic game material from that directory where available; clean checkouts retain text or synthetic fallbacks.

Initialize the importer database:

```bash
PYTHONPATH=src python3 -m cta_importer init-db extracted/imports.sqlite
```

Run the complete reproducible verification workflow:

```bash
./scripts/verify.sh
```

This runs the Python importer tests, restores/builds/tests the .NET API, performs `npm ci`, runs the frontend tests, and creates a frontend production build. It does not read or generate extracted game data.

## Hero library local development

The commands below read the locally extracted content and generate only ignored local outputs. Replace the version values with the installed game version when it changes.

1. Import the local content into SQLite:

```bash
PYTHONPATH=src python3 -m cta_importer import \
  samples/bluestacks/shared-data/cache/content \
  extracted/cta.sqlite \
  --game-id com.godzilab.idlerpg \
  --version 2.0.821
```

Warnings for incomplete localization, unresolved legacy skills, or missing portrait references are stored with the successful import. Errors such as duplicate hero IDs reject the import atomically.

2. Start the read-only ASP.NET Core API from the repository root:

Extract the authentic job-indicator and element icons from the retained read-only APK into the ignored proprietary runtime directory:

```bash
python3 scripts/extract-cta-ui-icons.py \
  samples/bluestacks/apk/base.apk \
  local/proprietary/ui-icons
```

The dependency-free extractor validates PVR/plist dimensions and frame bounds and writes a SHA-256-backed `provenance.json`. It uses the ten distinct neutral `HE_Job*.png` indicators from `UI1`; internal `Fighter` maps to the fist-shaped Brawler indicator. It intentionally does not use the similarly named `Rs_HeJob_*` awakening-resource frames.

Install the pinned optional ETC1 decoder and extract compact hero portraits:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[assets]'
.venv/bin/python scripts/extract-cta-hero-icons.py \
  samples/bluestacks/apk/base.apk \
  samples/bluestacks/shared-data/cache/content \
  local/proprietary/hero-icons
```

The extractor uses the same element/index mapping as the importer, validates atlas metadata and 162×162 frames, and writes source hashes plus every resolved/unresolved mapping to ignored `provenance.json`. In the verified BlueStacks `2.0.821` corpus it extracts 125 source-row icons and covers all 116 playable heroes.

Then start the API:

```bash
Database=extracted/cta.sqlite GameId=com.godzilab.idlerpg \
  dotnet run --project api/Cta.Api --urls http://localhost:5080
```

Authentic compact hero portraits are served from `HeroIconRoot`, which defaults to `local/proprietary/hero-icons`. Authentic job and element icons are served from `UiIconRoot`, which defaults to `local/proprietary/ui-icons`. Both directories are ignored and must not be staged. The API exposes them only through static GET/HEAD handling and never modifies them or the importer database.

3. In another terminal, start the React application:

```bash
cd web/cta-web
npm ci
npm run dev
```

Open `http://localhost:5173`. Set `VITE_API_URL` before `npm run dev` if the API is not at `http://localhost:5080`.

The roster exposes only heroes classified as playable. It supports job, element, rarity, mobility, acquisition, and attribute filters. Cards use authentic locally extracted CTA job-indicator and element icons when present and accessible text when they are absent. The UI also falls back to names for missing portrait files, canonical names or raw IDs for missing English names, and an unavailable-description message for incomplete skill localization.
