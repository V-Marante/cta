# Phase 2: File Inventory

## Outputs

- `inventories/files.csv`
- `inventories/files.json`

Inventory command:

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

## Results

- Successful candidate records: 531
- Additional inaccessible/error candidate records: 11
- Total size of successfully inventoried candidates: 3,294,693,297 bytes
- Hashing: 530 files hashed; 1 file skipped by size limit

Largest candidate files:

| Size | Type | Path |
|---:|---|---|
| 2,523,922,432 | application/octet-stream | `C:\Program Files\Google\Play Games\current\emulator\avd\aggregate.img` |
| 209,165,464 | Windows PE executable/library | `C:\Program Files\Google\Play Games\current\client\libcef.dll` |
| 39,409,304 | Windows PE executable/library | `C:\Program Files\Google\Play Games Services\26.7.546.0\Service\execute_challenge.dll` |
| 27,596,952 | Windows PE executable/library | `C:\Program Files\Google\Play Games\current\service\pss.dll` |
| 22,318,901 | text/plain | `C:\Program Files\Google\Play Games\current\licenses\LICENSES_android.txt` |

Game-specific host-visible files:

| Size | Type | Path |
|---:|---|---|
| 126,976 | SQLite database | `C:\Users\<windows-user>\AppData\Local\Google\Play Games\store.db` |
| 257,546 | ICO image | `C:\Users\<windows-user>\AppData\Local\Google\Play Games\image_cache\com.godzilab.idlerpg.appicon.ico` |
| 257,524 | PNG image | `C:\Users\<windows-user>\AppData\Local\Google\Play Games\image_cache\com.godzilab.idlerpg.appicon.png` |
| 613,930 | PNG image | `C:\Users\<windows-user>\AppData\Local\Google\Play Games\image_cache\com.godzilab.idlerpg.background.png` |
| 22,414 | PNG image | `C:\Users\<windows-user>\AppData\Local\Google\Play Games\image_cache\com.godzilab.idlerpg.logo.png` |

User AVD image files were found but not readable from this WSL session. These are the important inaccessible records:

- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\userdata_<instance>.gz5\avd\metadata.img`
- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\userdata_<instance>.gz5\avd\misc.img`
- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\userdata_<instance>.gz5\avd\userdata.img` at 85,899,345,920 bytes by `stat`

The remaining inaccessible/error records are Play Games active marker files, CEF cookie files, and CEF LevelDB lock files. They are not currently strong game-content candidates.

## Notes

The inventory records full paths, relative paths, sizes, timestamps, SHA-256 hashes when below the configured size limit, detected type, first header bytes, and a relevance reason. The user-data image is the most important unresolved container and should be reviewed before any mount, extraction, or package copy.
