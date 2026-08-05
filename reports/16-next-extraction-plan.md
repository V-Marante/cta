# Phase 10: Next Extraction Plan

## Prioritized Candidates

| Priority | Source | Format | Confirmed/Inferred Content | Parser Needed | Link Names/Stats/Images | Complexity | Confidence | Automation |
|---|---|---|---|---|---|---|---|---|
| A | `/data/app/.../base.apk` | APK/ZIP | Manifest, DEX, assets, possible engine markers | `unzip`, `aapt2` if available | Unknown until inspected | Low after copy | High | Yes |
| A | `/data/app/.../split_config.x86_64.apk` | APK/ZIP | Native libraries and ABI-specific assets | `unzip`, `file`, `strings` | Engine-dependent | Low after copy | High | Yes |
| B | `/data/user/0/com.godzilab.idlerpg/cache/remote_config_resources_lib.jar` | JAR/ZIP | Remote-config resources inferred from filename | `unzip`, JSON/XML validators, strings | Possible config keys, unlikely images | Medium | Medium | Yes |
| B | `/data/user/0/com.godzilab.idlerpg/cache/app_resources_lib.jar` | JAR/ZIP | App-generated resources inferred from filename | `unzip`, JSON/XML validators, strings | Possible resource names | Medium | Medium | Yes |
| C | `/data/user/0/com.godzilab.idlerpg/files/didomi_config_cache_...json` | JSON | Consent/privacy SDK config | JSON parser | No game stats | Low | High for file role | Yes |
| D | ART `oat/x86_64` files | ODEX/VDEX | Runtime optimization artifacts | none recommended | No | High | High as irrelevant | No |

## Google Play Games Practicality

The consumer Google Play Games installation is currently impractical for ordinary ADB retrieval from this session:

- Linux `adb` is installed and starts
- `adb devices -l` shows no attached devices
- `adb connect 127.0.0.1:6520` and `adb connect 127.0.0.1:38068` both return connection refused
- the logged VM boot disabled the ADB proxy
- Windows interop is unavailable, so Windows process and port inspection cannot be performed
- copying the image was retried after user-confirmed VM shutdown but failed through `/mnt/c` with an input/output error at a partial 54,362,382,336-byte output

## Migration Recommendation

Best standard-access option: Android Studio Emulator with Google Play support.

Reason: it provides clean, documented access to:

- `adb shell pm path com.godzilab.idlerpg`
- `adb pull`
- APK split files
- package-scoped shared storage under `/sdcard/Android/data` and `/sdcard/Android/obb`

Google Play Games on PC Developer Emulator may also be appropriate if the game can be installed there and it exposes documented ADB access. BlueStacks can expose ADB, but it adds vendor-specific behavior and is a less clean baseline.

## Exactly One Recommended Primary Next Implementation Task

Retrieve the APK and split APKs for `com.godzilab.idlerpg` through a standard ADB-enabled Android environment, then run archive-based APK inspection to confirm the game engine.

This is not a broad scan: it targets the already identified package and the four log-confirmed APK filenames.
