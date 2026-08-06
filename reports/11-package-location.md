# Phase 6: Package Location

> **Historical — Google Play Games.** BlueStacks supplied a separately versioned package and its APKs; do not treat these paths or version values as current. See `reports/19-bluestacks-reconciliation.md`.

## Outputs

- `inventories/package-files.csv`
- `inventories/package-files.json`

These inventories are log-inferred, not image-derived. No package files were copied.

## Confirmed From Logs

The Android serial log contains package-scoped runtime paths for `com.godzilab.idlerpg`.

Base APK:

```text
/data/app/~~E9VgB-8yLOlyAsDdCZXTTg==/com.godzilab.idlerpg-QazFZTRUuhLVpsoMpLOu_A==/base.apk
```

Split APKs observed in class loader paths:

```text
/data/app/~~E9VgB-8yLOlyAsDdCZXTTg==/com.godzilab.idlerpg-QazFZTRUuhLVpsoMpLOu_A==/split_config.mdpi.apk
/data/app/~~E9VgB-8yLOlyAsDdCZXTTg==/com.godzilab.idlerpg-QazFZTRUuhLVpsoMpLOu_A==/split_config.sv.apk
/data/app/~~E9VgB-8yLOlyAsDdCZXTTg==/com.godzilab.idlerpg-QazFZTRUuhLVpsoMpLOu_A==/split_config.x86_64.apk
```

Version evidence:

```text
app-version-name:2.0.822
app-version-code:200822
```

Package-private runtime paths observed:

```text
/data/user/0/com.godzilab.idlerpg/cache/app_resources_lib.jar
/data/user/0/com.godzilab.idlerpg/cache/google_api_resources_lib.jar
/data/user/0/com.godzilab.idlerpg/cache/remote_config_resources_lib.jar
/data/user/0/com.godzilab.idlerpg/files/didomi_config_cache_508c7b5f-2091-4bee-a232-186ac71f2cdb_CAJj2yK6_1.0.0.json
```

## ADB Status

ADB is installed and starts successfully:

```text
Android Debug Bridge version 1.0.41
Version 35.0.2-android-tools
```

Current device check:

```bash
adb devices -l
```

Result:

```text
List of devices attached
```

No devices were attached.

After the user stopped Google Play Games and `crosvm.exe`, `adb devices -l` was checked again and still showed no attached devices. This is expected with the VM stopped.

Known ADB-related ports from Play Games config/logs were tested, without brute forcing:

```bash
adb connect 127.0.0.1:6520
adb connect 127.0.0.1:38068
```

Results:

```text
failed to connect to '127.0.0.1:6520': Connection refused
failed to connect to '127.0.0.1:38068': Connection refused
```

No usable ADB endpoint was found:

- no `adb.exe` or `adbproxy.exe` found under `C:\Program Files\Google\Play Games`
- service config references `..\emulator\adb.exe` and `..\emulator\adbproxy.exe`, but those files are absent
- last recorded VM boot had `androidboot.kiwi.adbproxy.enabled=0`
- last recorded VM boot had `androidboot.kiwi.enable_devmode_sideloading=false`

## Limits

The package path is found, but the package files are not accessible as ordinary host files. They are expected to be inside `userdata.img`.

No unrelated Android package paths were exported.
