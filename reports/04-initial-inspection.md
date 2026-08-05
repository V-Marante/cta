# Phase 4: Initial Inspection

## Samples Copied

Small databases copied to `samples/` before parsing:

- `samples/store.db`
- `samples/phenotype.db`
- `samples/installer_phenotype.db`

No large assets or disk images were copied.

## SQLite

Inspection command:

```bash
python3 scripts/inspect-sqlite.py samples/store.db samples/phenotype.db samples/installer_phenotype.db --output reports/sqlite-inspection.json --sample-rows 3
```

Results:

- `samples/store.db`: integrity check `ok`
- `samples/phenotype.db`: integrity check `ok`
- `samples/installer_phenotype.db`: integrity check `ok`

Promising `store.db` tables:

| Table | Rows | Relevance |
|---|---:|---|
| `InstallIntentAttributes` | 1 | BLOB contains `com.godzilab.idlerpg` |
| `UserSettingsState` | 1 | BLOB contains `com.godzilab.idlerpg` and window settings |
| `UserDataState` | 1 | clear text user data set ID and AVD serial |
| `LastSession` | 1 | timestamp-like last run value |
| `AppLibrary` | 1 | encrypted or serialized library state BLOB |

Most `store.db` state is either protobuf-like BLOBs or encrypted BLOBs. It is useful for provenance and lifecycle, not direct hero/item/stat extraction.

## Structured Files

Inspection command:

```bash
python3 scripts/inspect-structured-files.py \
  /mnt/c/Users/<windows-user>/AppData/Local/Google/'Play Games'/gpg_events.json \
  /mnt/c/Users/<windows-user>/AppData/Local/Google/'Play Games'/CEF/LocalPrefs.json \
  /mnt/c/'Program Files'/Google/'Play Games'/current/client/manifest.xml \
  /mnt/c/'Program Files'/Google/'Play Games'/current/service/manifest.xml \
  --output reports/structured-inspection.json
```

These files describe Play Games client/service behavior, not game content. They are supporting evidence only.

## Strings

Inspection command:

```bash
python3 scripts/scan-strings.py \
  samples/store.db \
  /mnt/c/Users/<windows-user>/AppData/Local/Google/'Play Games'/Logs/Client.log \
  /mnt/c/Users/<windows-user>/AppData/Local/Google/'Play Games'/Logs/emulator_logs/gpu_syslog.log \
  /mnt/c/Users/<windows-user>/AppData/Local/Google/'Play Games'/Logs/emulator_logs/metrics_syslog.log \
  --output reports/string-hits.txt \
  --limit-per-file 100
```

Useful string hits:

- package ID: `com.godzilab.idlerpg`
- display title: `Crush Them All - PVP Idle RPG`
- Play Store details URLs for the package
- install/download/launch lifecycle events
- app icon reference: `com.godzilab.idlerpg.appicon.ico`

No host-visible files produced hero, character, item, ability, stat, quest, reward, shop, or localization data in this phase.
