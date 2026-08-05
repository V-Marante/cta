# Final Summary

## 1. Where Files Were Found

Google Play Games for Windows data was found under:

- `C:\Users\<windows-user>\AppData\Local\Google\Play Games`
- `C:\ProgramData\Google\Play Games`
- `C:\ProgramData\Google\Play Games Services`
- `C:\Program Files\Google\Play Games`
- `C:\Program Files\Google\Play Games Services`

The strongest game-specific directory is:

- `C:\Users\<windows-user>\AppData\Local\Google\Play Games`

## 2. Likely Game Engine

Unconfirmed. The host-visible files do not expose the game's APK/splits or internal assets, so Unity/Unreal/native framework detection is not yet reliable.

Confirmed platform: Google Play Games Android virtualization using `crosvm`.

## 3. APK, Splits, Images, or Asset Directory

Found:

- base emulator image: `C:\Program Files\Google\Play Games\current\emulator\avd\aggregate.img`
- user Android data image: `C:\Users\<windows-user>\AppData\Local\Google\Play Games\userdata_<instance>.gz5\avd\userdata.img`
- user AVD metadata/misc images under the same directory

Not found as ordinary host-visible files:

- APK
- split APKs
- OBB/XAPK
- extracted game asset directory

## 4. Most Useful Discovered Files

1. `C:\Users\<windows-user>\AppData\Local\Google\Play Games\userdata_<instance>.gz5\avd\userdata.img`
2. `C:\Users\<windows-user>\AppData\Local\Google\Play Games\store.db`
3. `C:\Users\<windows-user>\AppData\Local\Google\Play Games\Logs\Client.log`
4. `C:\Users\<windows-user>\AppData\Local\Google\Play Games\Logs\emulator_logs\gpu_syslog.log`
5. `C:\Users\<windows-user>\AppData\Local\Google\Play Games\image_cache\com.godzilab.idlerpg.*`

## 5. Useful Data Identified

- package name: `com.godzilab.idlerpg`
- game title: `Crush Them All - PVP Idle RPG`
- installed version code: `200822`
- install/download/launch timeline
- user data set ID: `bdhfv2nx.gz5`
- AVD serial: `043383d722e244e2997b24a312d415fa`
- store artwork: app icon, logo, and background PNG/ICO files

No hero/item/stat/localization records were found in host-visible files during this phase.

## 6. Inaccessible or Uncertain

- The user AVD image files were not readable from WSL without elevated or different host access.
- The live Windows process list, loaded modules, and open file handles were not collected because `powershell.exe` was unavailable in this WSL session.
- The game engine remains unknown until the APK/splits or app-private asset files are copied and inspected.
- Some Play Games SQLite tables contain encrypted or protobuf-like BLOBs; they were not decoded beyond safe schema/sample inspection.

## 7. Recommended Next Step

Use normal Windows/Google Play Games/Android tooling to locate the installed package path for `com.godzilab.idlerpg`, then copy only the APK/split APKs and small app-private manifest/config/database files into `samples/`. Inspect archive listings and engine markers before any asset export.

## 8. Interpretation Risks

- Google Play Games platform assets can look like game assets but are unrelated to `Crush Them All`.
- Store artwork is not the same as in-game sprites or portraits.
- AVD disk images may contain unrelated Android/user state; searches should remain package-scoped.
- Encrypted Play Games state BLOBs should not be treated as game data unless decoded through documented, normal mechanisms.

## 9. Suggested Normalized Data Model

Core entities:

- `Game`
- `GameVersion`
- `Entity`
- `EntityType`
- `Character`
- `Item`
- `Ability`
- `Stat`
- `Upgrade`
- `Stage`
- `Reward`
- `LocalizationEntry`
- `Asset`
- `SourceFile`
- `SourceRecord`

Required provenance fields on extracted records:

- `source_file`
- `source_hash`
- `source_path`
- `source_record_key`
- `game_version`
- `extraction_timestamp`
- `extractor_version`

## Stopping Point

Discovery, inventory, engine triage, sample inspection, scripts, and reports have been completed. Bulk asset export, full database dumps, custom binary reverse engineering, and ingestion into a final application were intentionally not performed.
