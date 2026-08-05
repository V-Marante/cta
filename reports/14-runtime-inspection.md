# Phase 9: Runtime Inspection

## Status

Limited to log-derived runtime path discovery.

No package-scoped runtime files were copied into `samples/runtime/`.

## Runtime Files Identified

Potentially useful package-private files from logs:

| Path | Likely role | Initial priority |
|---|---|---|
| `/data/user/0/com.godzilab.idlerpg/files/didomi_config_cache_508c7b5f-2091-4bee-a232-186ac71f2cdb_CAJj2yK6_1.0.0.json` | JSON config/cache, likely consent SDK rather than game content | C |
| `/data/user/0/com.godzilab.idlerpg/cache/app_resources_lib.jar` | dynamically generated or cached resource JAR | B |
| `/data/user/0/com.godzilab.idlerpg/cache/google_api_resources_lib.jar` | Google API resource JAR | C |
| `/data/user/0/com.godzilab.idlerpg/cache/remote_config_resources_lib.jar` | remote config resource JAR | B |

ART optimization files under `oat/x86_64` were also observed, but these are not primary content sources.

## No Inspection Performed

Because the files were not copied, no SQLite checks, JSON validation, archive listing, or strings scan was performed on runtime files.
