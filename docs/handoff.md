# Project Handoff

## Current state

The extraction investigation and game-agnostic importer infrastructure are complete enough to begin game-specific parser work.

- Android package: `com.godzilab.idlerpg`
- inspected game version: `2.0.821` (`versionCode=200821`)
- engine: custom native `GodzilabEngine`, not Unity
- local extraction source: `samples/bluestacks/shared-data/cache/content/`
- importer package: `src/cta_importer/`
- importer database location used by documentation: `extracted/imports.sqlite`
- game-specific parsers implemented: none
- current core test count: five

Extracted files are local-only and ignored by Git. A new checkout will not contain them. The user must restore or repeat the local BlueStacks extraction before game-parser integration tests can inspect real files.

## Read first

1. `AGENTS.md` — Android/BlueStacks and repository-safety rules.
2. `reports/17-bluestacks-extraction.md` — extraction results and engine confirmation.
3. `reports/18-structured-schema-importer-design.md` — complete source schemas, inferred relationships, and parser order.
4. `docs/importer-architecture.md` — core plugin contracts, validation, versioning, transactions, and SQLite design.

## Verified commands

Run the core tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Initialize or migrate a local database:

```bash
PYTHONPATH=src python3 -m cta_importer init-db extracted/imports.sqlite
```

List installed parser plugins:

```bash
PYTHONPATH=src python3 -m cta_importer list-parsers
```

## Recommended next milestone

Implement the first Crush Them All parser plugin without changing the core importer contracts:

1. Create an in-tree plugin package such as `src/cta_game_parsers/crush_them_all/`; it may depend on `cta_importer`, but core code must not import it.
2. Add lossless shared CSV and XML parsing utilities with source locations and raw-value preservation.
3. Implement `Items.xml` as the first canonical registry parser.
4. Add small synthetic fixtures and parser unit tests; do not commit copied game content.
5. Register the parser through the `cta_importer.parsers` entry-point group in `pyproject.toml`.
6. Run a local, ignored integration import against `samples/bluestacks/shared-data/cache/content/`.
7. Inspect persisted entities and diagnostics before implementing `Skills.xml`.

The subsequent dependency order is `Skills.xml` → `ModMonsters.xml` → `Persos.xml` → `Heroes.csv`, followed by dungeons, goals, artifacts, runes, armory, and Paragon. The full order and relationship model are in report 18.

## Known source issues

- `Skills_ru.xml` is malformed at line 329, column 226. It must produce a deterministic diagnostic and must not block canonical `Skills.xml` import.
- Hero/character IDs include two case-only mismatches: `DDSaberDancer`/`DDSaberdancer` and `Pumpking`/`PumpKing`.
- Localization files contain stale, extra, and missing keys; they are overlays, not canonical entity sources.
- Several CSV files are editor matrices rather than flat tables, especially `GuildQuests.csv`, `HeroRuneSets.csv`, `RuneSets.csv`, and `CrusadeTeams.csv`.
- Resource, effect, environment, and dungeon-wave references are sometimes polymorphic and should remain soft references initially.

## Repository safety

- Never stage `samples/`, `assets/`, `extracted/`, `inventories/`, logs, generated databases, or generated inspection output.
- Do not weaken `.gitignore` for integration tests.
- Keep real-data integration output local and ignored.
- Before committing, run tests and inspect both `git status --short` and the staged file list.

## Android interaction

This project uses BlueStacks. Any future Android interaction must be performed with Windows PowerShell and BlueStacks' `HD-Adb.exe`. Generate the PowerShell command, wait for the user to execute it, and continue from the returned output. Do not use Linux `adb`.
