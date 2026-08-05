# Phase 7: Prioritized Sources

| Priority | Source | Format | Likely Content | Confidence | Difficulty | Recommended Parser/Tool | Linkable Names/Stats/Images | Version-specific | Automatable |
|---|---|---|---|---|---|---|---|---|---|
| A | `C:\Users\<windows-user>\AppData\Local\Google\Play Games\userdata_<instance>.gz5\avd\userdata.img` | Android/AVD disk image | Installed APK/splits, app-private files, downloaded game cache, databases | High | Medium to high; read access needed | Read-only image mount or normal Android package listing tooling | Likely yes after APK/cache discovery | Yes | Yes, after reviewed method |
| A | APK/split APKs for `com.godzilab.idlerpg` inside Android environment | ZIP/APK | Manifest, DEX/native libs, assets, engine markers | High, once located | Low to medium | `unzip -l`, `aapt2 dump badging`, `jadx` for metadata only | Names possible; stats depend on assets/code | Yes | Yes |
| B | App-private data under Android `/data/data/com.godzilab.idlerpg` or equivalent | Mixed | Runtime databases, downloaded bundles, configs, manifests | High, once accessible normally | Medium | Read-only file copy after package-path discovery | Likely yes | Yes | Yes |
| B | `store.db` | SQLite | Play Games library state, package lifecycle, user AVD ID | Medium for provenance; low for game content | Low | `scripts/inspect-sqlite.py` | No game stats; package linkage only | Yes | Yes |
| C | `image_cache\com.godzilab.idlerpg.*` | PNG/ICO | Store icon, logo, background | High for artwork metadata | Low | image metadata tools | Images only, not internal entity art | Yes | Yes |
| C | `Logs\Client.log` and `Logs\emulator_logs\*.log` | Text logs | Install/launch/download timing, package name, runtime clues | Medium | Low | `scripts/scan-strings.py` | No direct stats | Yes | Yes |
| C | `C:\Program Files\Google\Play Games\current\emulator\avd\aggregate.img` | Emulator base disk image | Base Android/Play Games system image | Medium for platform context; low for game content | Medium | `file`, read-only image tooling | No | Yes | Partly |
| D | Play Games client/service DLLs and CEF cache | PE, CEF/Chromium caches | Platform implementation, not game content | Low | Low to high | No further work recommended | No | Yes | No |

## Recommended Next Extraction Shape

Before bulk extraction, locate and copy only:

- package APK/split APK paths for `com.godzilab.idlerpg`
- manifest/catalog/version files under app-private storage
- small SQLite/JSON/XML/CSV files under app-private storage
- representative Unity/asset bundle containers if present

Expected output should preserve:

- `source_file`
- `source_hash`
- `source_path`
- `source_record_key`
- `game_version`
- `extraction_timestamp`
- `extractor_version`
