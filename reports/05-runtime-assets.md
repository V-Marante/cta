# Phase 6: Runtime Assets

## Timeline

The user reported installation at 09:00 GMT+2 on 2026-08-05. Local evidence aligns with first-run activity shortly after that.

Observed timestamps:

- `installer_phenotype.db`: modified 2026-08-05 09:08:29 +0200
- Play Games install log: `install-26.7.341.4-20260805091246.log`
- `phenotype.db`: modified 2026-08-05 09:14:23 +0200
- cached game images: modified 2026-08-05 09:14:43 +0200
- user AVD `misc.img`: modified 2026-08-05 09:14:23 +0200
- user AVD `metadata.img`: modified 2026-08-05 09:15:16 +0200
- `Client.log` install/download lifecycle: approximately 09:14:36 through 09:15:58 +0200
- `Client.log` launch/run lifecycle: approximately 09:16:06 through 09:20:58 +0200
- user AVD `userdata.img`: modified 2026-08-05 09:35:11 +0200
- `store.db`: modified 2026-08-05 09:29:10 +0200

## Static vs Runtime

Likely static Google Play Games platform files:

- `C:\Program Files\Google\Play Games\current\...`
- `C:\Program Files\Google\Play Games Services\26.7.546.0\...`
- `C:\Program Files\Google\Play Games\current\emulator\avd\aggregate.img`

Likely runtime/user-specific files:

- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\store.db`
- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\Logs\...`
- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\image_cache\com.godzilab.idlerpg.*`
- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\userdata_<instance>.gz5\avd\userdata.img`

## Interpretation

The host-visible game-specific assets are only store/library artwork. The actual installed Android package and any content downloaded by the game during normal gameplay likely reside inside the user AVD image or Android app-private storage within that image.

No bulk extraction was performed.
