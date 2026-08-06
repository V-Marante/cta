# Crush Them All Game Data Investigation

This workspace contains a read-only local investigation of Google Play Games for Windows data related to:

- Game: `Crush Them All - PVP Idle RPG`
- Android package: `com.godzilab.idlerpg`
- Play Store publisher noted by user: `Imperia Online JSC`
- Rights holder noted by user: `Stillfront Group AB`
- Related developer/company noted by user: `Godzillab` / local package namespace `godzilab`

The original installation was not modified. Small SQLite databases were copied into `samples/` before inspection. Large emulator images were inventoried only by metadata and were not extracted.

## Workspace

- `reports/`: phase reports and inspection artifacts
- `inventories/files.csv`: machine-readable file inventory
- `inventories/files.json`: JSON equivalent of the file inventory
- `samples/`: copied small samples used for inspection
- `scripts/`: reusable read-only investigation scripts
- `logs/`: reserved for future script logs
- `extracted/`: reserved; no bulk extraction was performed

## Re-run

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

BlueStacks exposed `com.godzilab.idlerpg` through its Windows `HD-Adb.exe`. Version `2.0.821` and its four APKs were copied to `samples/bluestacks/apk/`; approximately 58 MB of accessible runtime content was copied to `samples/bluestacks/shared-data/`.

The game uses the custom native `GodzilabEngine`, not Unity. Its current downloaded content is directly extractable: `cache/content/` contains gameplay CSV/XML files, localization, Spine data, sprite atlases, textures, and animation files. Four ZIP-compatible `.bin` files in `cache/patch/` preserve the downloaded patch bundles. See `reports/17-bluestacks-extraction.md`.

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

Users must perform their own local extraction. The contents of `samples/`, `assets/`, and `extracted/` remain local and must not be committed.

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

```bash
Database=extracted/cta.sqlite GameId=com.godzilab.idlerpg \
  dotnet run --project api/Cta.Api --urls http://localhost:5080
```

The large `HP_<hero>` presentation artwork is deliberately ignored. The collection view uses a live assembled character rather than a standalone small portrait, so heroes currently use name-only placeholders. A future genuine small-icon set can be supplied through `HeroIconRoot`; it defaults to `generated/hero-icons`. The API never modifies the importer database.

3. In another terminal, start the React application:

```bash
cd web/cta-web
npm ci
npm run dev
```

Open `http://localhost:5173`. Set `VITE_API_URL` before `npm run dev` if the API is not at `http://localhost:5080`.

The roster defaults to collectible heroes and can optionally include classified variants, enemies, and NPCs. It supports job, element, rarity, mobility, acquisition, and attribute filters. The UI falls back to initials for missing portrait files, canonical names or raw IDs for missing English names, and an unavailable-description message for incomplete skill localization.
