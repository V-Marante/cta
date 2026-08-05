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

The `src/cta_importer/` package provides game-agnostic, plugin-based import infrastructure with version-aware parser dispatch, validation, structured diagnostics, checksummed SQLite migrations, idempotent source manifests, and atomic dataset persistence. Game-specific parsers are intentionally not implemented yet.

Architecture: `docs/importer-architecture.md`

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

Run the core tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
