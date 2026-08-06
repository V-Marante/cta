# Phase 9: Content Candidates

> **Superseded.** The APK and shared-cache candidates were obtained through BlueStacks. See `reports/19-bluestacks-reconciliation.md` for the remaining narrow gaps.

## Candidate Summary

| Priority | Candidate | Basis | Confidence | Notes |
|---|---|---|---|---|
| A | `/data/app/.../com.godzilab.idlerpg.../base.apk` | Log-confirmed APK path | High for engine detection | Must be copied before inspection |
| A | `/data/app/.../split_config.x86_64.apk` | Log-confirmed split APK path | High for native library/engine detection | Likely contains ABI-specific libraries |
| B | `/data/user/0/com.godzilab.idlerpg/cache/remote_config_resources_lib.jar` | Log-confirmed runtime cache JAR | Medium | May contain remote config resources, not necessarily game balance data |
| B | `/data/user/0/com.godzilab.idlerpg/cache/app_resources_lib.jar` | Log-confirmed runtime cache JAR | Medium | May contain app resources or generated resources |
| C | `/data/user/0/com.godzilab.idlerpg/files/didomi_config_cache_...json` | Log-confirmed JSON path | Low for game content | Likely consent/privacy SDK config |
| D | `/data/user/0/com.godzilab.idlerpg/cache/oat/x86_64/*.odex|*.vdex` | ART optimization artifacts | Low | Support files, not original game data |

## No Confirmed Game-Data Records Yet

No heroes, items, abilities, stats, localization tables, stages, rewards, or asset catalogs were directly extracted in this phase.

The strongest next evidence will come from APK archive contents and any package-scoped small runtime files.
