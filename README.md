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

BlueStacks exposed `com.godzilab.idlerpg` through its Windows `HD-Adb.exe`. Version `2.0.821` was reconfirmed on 2026-08-06: no BlueStacks update was available, the launched package reported `versionCode=200821`, and current public Google Play metadata independently reported 2.0.821/200821. Four APKs are retained locally under `samples/bluestacks/apk/`, with approximately 58 MB of accessible runtime content under `samples/bluestacks/shared-data/`. Historical Google Play Games logs contain an uncorroborated `2.0.822` value; it is not evidence of a newer public release. See report 25.

The game uses the custom native `GodzilabEngine`, not Unity. The retained `cache/content/` contains gameplay CSV/XML files, localization, Spine data, sprite atlases, textures, and animation files. Four ZIP-compatible `.bin` files in `cache/patch/` preserve downloaded patch bundles. The base APK also contains authentic UI and character atlases absent from the materialized cache. See `reports/README.md` and `reports/19-bluestacks-reconciliation.md` before using older reports.

## Importer Infrastructure

The `src/cta_importer/` package provides game-agnostic import infrastructure plus the first CTA vertical slice: English localization, heroes, character skill references, skills, and portrait references. Imports are versioned, validated, provenance-preserving, idempotent, and atomic.

Architecture: `docs/importer-architecture.md`

Future-session handoff: `docs/handoff.md`

Hero HTTP contract: `docs/hero-api-contract.md`

Production deployment and local data releases: `docs/deployment.md`

Current release-readiness evidence: `reports/24-hero-library-release-readiness.md`

## Repository Data Boundary

This repository contains extraction and importer tooling, tests, migrations, and investigation documentation—not the extracted game dataset. Extracted content and proprietary assets are intentionally excluded from Git.

## Team Planner

The React application includes a compact client-only Team Planner at `/team-planner`. It loads the existing collectible hero summary response and provides name search, element/job filters, ten portrait slots, and available-hero grouping by job, element, or fourth ability. Clicking an available portrait adds it; clicking that portrait again or its selected-team portrait removes it. Heroes are unique within a team; one through ten selected heroes is a valid team. The informational summary reports team size and element/job distributions, plus the available fourth-ability names. It does not calculate damage, infer synergy, reorder heroes, or write to the API.

Planner cards display the source-backed hero name, portrait (with the existing fallback), an authentic element icon, player-facing job (`class` in the API), fourth ability, traits/attributes, and Flying mobility. Fourth-ability grouping stays generic by ability name, while each hero independently shows `All`, an authentic target-element icon, or the exact non-element target from `SP4 Target`. The selected composition uses two rows of five slots, places element/job counts alongside them, and gives fourth abilities a wider section below. Fourth-ability data comes from the existing nullable `passive` projection of `Heroes.csv` fields `SP4`, `SP4 Target`, and `SP4 Value`; the importer supplies a name/description and buff/debuff semantics only where its established mapping supports them. Missing values display as unavailable rather than being inferred.

The hero IDs are stored under the versioned browser key `cta.team-planner.v1`. Corrupt values, duplicate IDs, and heroes absent from the current import are ignored safely after the hero list loads. Clearing the team removes the key. The portrait-toggle interaction uses native buttons and adds no frontend interaction dependency.

Run planner-focused tests with:

```bash
npm test --prefix web/cta-web -- --run src/test/teamPlannerState.test.ts src/test/TeamPlannerPage.test.tsx
```

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

Reconcile the retained package, APK hashes, complete shared-file listing, patch bundles, and canonical hero sources into an ignored manifest:

```bash
python3 scripts/audit-cta-source-refresh.py \
  samples/bluestacks extracted/cta-source-refresh.json
```

Generate the ignored progression/acquisition semantics audit:

```bash
PYTHONPATH=src python3 scripts/audit-hero-data.py \
  extracted/cta.sqlite extracted/hero-data-audit.md \
  --game-id com.godzilab.idlerpg \
  --hero-icon-root local/proprietary/hero-icons
PYTHONPATH=src python3 scripts/audit-hero-semantics.py \
  extracted/cta.sqlite extracted/hero-semantics-audit.md \
  --game-id com.godzilab.idlerpg
PYTHONPATH=src python3 scripts/audit-hero-stats.py \
  extracted/cta.sqlite extracted/hero-stat-audit.md \
  --game-id com.godzilab.idlerpg
PYTHONPATH=src python3 scripts/audit-hero-skills.py \
  extracted/cta.sqlite extracted/hero-skill-audit.md \
  --game-id com.godzilab.idlerpg
PYTHONPATH=src python3 scripts/audit-hero-localization.py \
  extracted/cta.sqlite extracted/hero-localization-audit.md \
  --game-id com.godzilab.idlerpg
```

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

The frontend includes a compact local tier-list maker at `/tier-list`. It starts with one `S` tier, loads the same collectible-only hero API, and keeps a scrollable Unranked portrait pool sticky in the viewport. Every tile is a compact portrait with a full-name box underneath. Up to 15 renamed tiers receive unique deterministic positional colors; colors are not user-editable. Tiers can be moved up/down after creation, with colors following their positions. Hero placement supports click/keyboard controls and drag-and-drop. Development mode includes random fill for visualization, and ranked tiers export as a lossless PNG with the same portrait/name-card layout. Authentic portraits are attempted first; failed export images use the full hero name rather than initials. Drafts use versioned browser `localStorage`; the tool never writes to the API or database.

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

Open `http://localhost:5173`. The Vite development server proxies API and local-asset requests to `http://localhost:5080`, which also keeps portrait export same-origin. Set `VITE_API_URL` before `npm run dev` only when the API is hosted elsewhere; that API must allow the frontend origin for canvas export.

The roster exposes only heroes classified as playable. It supports job, element, rarity, mobility, acquisition, and attribute filters. Cards use authentic locally extracted CTA job-indicator and element icons when present and accessible text when they are absent. The UI also falls back to names for missing portrait files, canonical names or raw IDs for missing English names, and an unavailable-description message for incomplete skill localization.
