# Hero-library source-refresh reconciliation

Date: 2026-08-06  
Result: same-version reconciliation; no source drift  
Authoritative package: `com.godzilab.idlerpg` 2.0.821 (`versionCode=200821`)

## Why this is a same-version refresh

The current [Google Play listing](https://play.google.com/store/apps/details?id=com.godzilab.idlerpg&hl=en) reports a March 30, 2026 update and the Easter/Cuddles changelog but does not render a numeric version in its public page. Current Google Play metadata tracked by [AppBrain](https://www.appbrain.com/app/crush-them-all-pvp-idle-rpg/com.godzilab.idlerpg) identifies 2.0.821 as the latest version with that same update date. [Chrome-Stats](https://chrome-stats.com/d/com.godzilab.idlerpg) independently reports version 2.0.821 and version code 200821. This exactly matches the retained BlueStacks package dump and the user's launched-package check.

Historical Google Play Games reports 11 and 13 contain the raw string `2.0.822`. No current public listing, package record, or retained APK corroborates it as a released build. It remains historical raw evidence only and must not be described as a newer public release or as evidence that the BlueStacks corpus is stale.

## Reconciliation procedure

The new read-only command records an ignored JSON manifest:

```bash
python3 scripts/audit-cta-source-refresh.py \
  samples/bluestacks \
  extracted/cta-source-refresh-2026-08-06.json
```

It reads the retained package dump, recalculates APK hashes, compares the shared-data listing with the materialized pull, inventories every patch archive, hashes six canonical hero-library sources, and verifies byte-identical canonical members in patch bundles. It does not modify `samples/`, APKs, the cache, or proprietary assets.

## Exact source results

- Package dump: 2.0.821 / 200821.
- APKs: four present; all four SHA-256 values match `com.godzilab.idlerpg.apk-sha256.txt`.
- Shared-data listing: 1,320 files.
- Listed but missing locally: 0.
- Materialized but unlisted: 0.
- Patch bundles: four, containing 133, 2, 26, and 42 files respectively.
- All canonical sources are present and byte-identical to members of `260330102436_data.bin`.

| Canonical source | SHA-256 |
|---|---|
| `Heroes.csv` | `0421e0f25269cc370c2aa6b5e25bb6681189de6496e30751de930d8a3f7b0aba` |
| `Persos.xml` | `09130d1de05c616daad6a5ca9be63cac5bca0ed51449aa38b5da06ee94384380` |
| `Skills.xml` | `007e4d014bcaa506c3ce13423c432ae26c4fd40a71352804b683fb504dfb6636` |
| `Items.xml` | `1934cea62e46d186ca714b9bd1328fccf1d67425202b309cbb1c0d2cf29b05d3` |
| `Config.xml` | `c08c4f68ec40cc67a8e4f7094ad27dc1484eba9bdf3425b98950e02ea55fab6e` |
| `Config_en.xml` | `d7b67c6abfed9a586a34807ffd550ee1d598e6aa1a7326978f19c70467afbdbf` |

The ignored UI-icon provenance references the same base APK hash. Hero-icon provenance references the same base APK, `Heroes.csv`, and `Persos.xml` hashes. Local authentic portrait coverage is 116/116 playable heroes.

## Import and audit reconciliation

The documented import command returned successful import `ad4a751c-470c-4948-b65a-699092bd5eaf` with `reused: true`. Reuse is correct here: source hashes, game/version identity, and current parser identities are unchanged. Persisted successful parser executions are current: heroes 1.8.0/schema 4, characters 1.5.0/schema 1, skills 1.1.0/schema 2, localization 1.3.0/schema 1, and acquisition 1.4.0/schema 2. This is not reuse of an older parser-output contract.

All ignored audits were regenerated:

- completeness: 116 playable; classification counts unchanged; authentic portraits 116/116;
- progression/acquisition: 116 playable;
- stats: 116 playable;
- skill/passive: 116 playable and 348 displayed skills;
- localization/token rendering: 116 playable and 348 displayed skills.

The audit results match reports 20–24: four missing displayed descriptions, seven unresolved placeholders, source-defined rarity, qualified MaxStars, unresolved BaseStars/POW/source calculations, and separate explicit versus legacy acquisition evidence. No new exception or hidden hero appeared.

The completeness audit previously contained an obsolete statement that compact icons had not been extracted. It now accepts `--hero-icon-root`, reports proprietary runtime coverage separately from persisted structured data, and correctly reports 116/116 for the current ignored local assets.

## Decision

There is no newer hero-library source to import and no semantic reason to reinterpret the current data. Version 2.0.821 remains the authoritative public and retained BlueStacks baseline. The next source refresh is event-driven: run it only if the installed version changes, a retained source hash changes, or a concrete player-visible discrepancy identifies a targeted data question.

Final `./scripts/verify.sh` results: 26/26 Python tests, 12/12 API tests, 27/27 frontend tests, .NET build with zero warnings/errors, `npm ci` with zero vulnerabilities, and a successful Vite production build.

No Android interaction was needed. The JSON reconciliation manifest, audits, database, APKs, extraction, and proprietary assets remain ignored and must not be staged.
