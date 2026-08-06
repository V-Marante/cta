# BlueStacks extraction reconciliation

## Scope and authority

This report reconciles reports `01`–`16` with the retained BlueStacks extraction. The file and archive comparisons were produced from existing repository files. On 2026-08-06, the user separately performed the required read-only BlueStacks version check through Windows PowerShell and `HD-Adb.exe`.

For current work, use sources in this order:

1. the locally retained BlueStacks package and shared-data evidence;
2. `reports/17-bluestacks-extraction.md` for extraction provenance;
3. `reports/18-structured-schema-importer-design.md` for the structured corpus design;
4. reports `01`–`16` only as historical Google Play Games evidence.

The retained BlueStacks package is `com.godzilab.idlerpg` version `2.0.821` (`versionCode=200821`). On 2026-08-06, BlueStacks offered no update, the game launched successfully, `HD-Adb.exe devices` showed `127.0.0.1:5555` and `emulator-5554`, and `dumpsys package` reconfirmed version `2.0.821`, first installed and last updated on 2026-08-05 11:52:30. This is therefore the latest version currently obtainable through the installed BlueStacks distribution.

Google Play Games logs in the historical reports contain `2.0.822` (`versionCode=200822`) as a raw value. A 2026-08-06 public-source follow-up found that current Google Play metadata identifies 2.0.821/200821, matching BlueStacks exactly; no public listing or retained package corroborates 2.0.822 as a released build. Preserve the historical string, but do not treat it as a newer public version or evidence that this extraction is incomplete. See report 25.

## Reconciliation results

| Earlier limitation or conclusion | Current status | Evidence and consequence |
|---|---|---|
| Package identity unknown | Resolved by BlueStacks | Package is `com.godzilab.idlerpg`. |
| APK and split APKs inaccessible | Resolved by BlueStacks | `base.apk` plus English, hdpi, and x86_64 splits were pulled and hashed. |
| Engine unknown | Resolved by BlueStacks | The x86_64 split contains `libMain.so`; native strings identify GodzilabEngine, Spine, FMOD, RapidXML, and Box2D. This is a custom native C++ engine, not Unity. |
| No structured game data found | Resolved by BlueStacks | The shared cache contains heroes, characters, skills, items, localization, progression, atlases, animation timelines, and other gameplay sources. |
| Downloaded runtime content inaccessible | Resolved for shared storage | All 1,320 paths in the retained shared-file listing have corresponding local files: 1,301 materialized content files, four patch bundles, and 15 other cache/files entries. |
| Patch transport structure unknown | Resolved | Four `.bin` files are ZIP-compatible patch archives; the materialized `Heroes.csv` matches its patch member by SHA-256. |
| Google Play Games disk image required | Superseded | Do not retry the 80 GiB sparse-image copy. BlueStacks provides package-scoped ADB retrieval without mounting an emulator image. |
| Google Play Games platform databases/logs are primary sources | Irrelevant for game content | They remain provenance for the earlier installation only and should not drive importer or UI conclusions. |
| OBB/expansion content absent | Still unresolved | The retained logs contain no OBB listing or OBB reference. Absence was not established by a targeted BlueStacks directory check. |
| App-private databases/preferences/files captured | Still unresolved | `dumpsys` identifies `/data/user/0/com.godzilab.idlerpg`, but the retained extraction covers shared storage, not the private data directory. A non-debuggable production package may prevent a non-root pull. |
| All external-storage package paths captured | Partially resolved | `/sdcard/Android/data/com.godzilab.idlerpg` is completely represented relative to its retained listing. Other package-related external roots were not explicitly inventoried. |
| APK assets represented by `cache/content/` | False | The base APK contains 623 `assets/` entries. Only 115 top-level APK asset basenames overlap the materialized cache; many bundled UI atlases, shaders, fonts, and static images exist only in the APK snapshot. |
| Authentic UI/job/element icons unavailable | Resolved | The dependency-free local extractor reads five `Elt_*` frames and ten distinct neutral `HE_Job*` indicator frames from `UI1`, writing ignored PNGs and SHA-256 provenance under `local/proprietary/ui-icons/`. |
| Latest version obtainable through installed BlueStacks | Resolved on 2026-08-06 | BlueStacks offered no update; the launched package reported `2.0.821` (`versionCode=200821`) through `HD-Adb.exe`. |
| Why historical Google Play Games contained `2.0.822` | Still unresolved but non-blocking | Current public metadata contradicts it as the latest released version. Preserve it as unexplained raw historical evidence only. |
| Cache and APK represent one proven content version | Not proven | APK package version, patch filenames/member timestamps, and materialized cache must be recorded separately. Matching one `Heroes.csv` proves that file's materialization, not global version identity. |

## Report-by-report disposition

| Report | Disposition |
|---|---|
| `01-identifiers` | Historical. Package ID remains correct; Google Play Games roots and unresolved APK access are not current guidance. |
| `02-file-inventory` | Historical. Inventory describes Google Play Games platform storage, not the current game corpus. |
| `03-engine-detection` | Superseded. Engine is now confirmed as custom native GodzilabEngine. |
| `04-initial-inspection` | Historical. Platform SQLite/string results are provenance only. |
| `05-runtime-assets` | Superseded. BlueStacks shared storage exposed the materialized runtime cache. |
| `06-prioritized-sources` | Superseded. BlueStacks APKs and shared cache replace the Google Play Games disk image as primary sources. |
| `07-final-summary` | Superseded. Its stopping point was the end of the Google Play Games phase, not the project. |
| `08-windows-access` | Historical environment note. It does not describe BlueStacks `HD-Adb.exe` access. |
| `09-image-copy` | Obsolete. Do not retry the sparse Google Play Games image copy. |
| `10-image-format` | Obsolete. Disk-image format analysis is no longer a prerequisite. |
| `11-package-location` | Historical. Package layout evidence was useful, but its version and split set are from Google Play Games. |
| `12-apk-inspection` | Superseded. BlueStacks APK inspection was completed. |
| `13-engine-confirmation` | Superseded. The engine is confirmed. |
| `14-runtime-inspection` | Partially superseded. Shared runtime data is captured; app-private storage remains unresolved. |
| `15-content-candidates` | Superseded. APK and shared-cache candidates were obtained; private low-value SDK caches remain non-priority. |
| `16-next-extraction-plan` | Superseded. Its recommendation against BlueStacks is contradicted by the successful extraction. |
| `17-bluestacks-extraction` | Current baseline for retained extraction facts. |
| `18-structured-schema-importer-design` | Current design snapshot; counts are version-specific. |

## Concrete local gaps

### APK-only assets

The runtime-cache pull is complete relative to its retained listing, but it is not a complete asset corpus. The base APK includes atlas pairs absent from `cache/content/`, notably:

- `UI0.plist` / `UI0.pvrgz` and `UI1.plist` / `UI1.pvrgz`;
- `UIGuildLibraryIcons.plist` / `UIGuildLibraryIcons.pvrgz`;
- `UIHeroPres*.plist` / `UIHeroPres*.pvrgz`;
- `UIGuildMemberIcons*.plist` / `UIGuildMemberIcons*.pvrgz`;
- character atlases such as `C01_0`, `C02`, `C03`, `C04`, and `C05`;
- bundled shaders, fonts, and static PNG/JPEG images.

Authentic element frames are `Elt_DA.png`, `Elt_EA.png`, `Elt_FI.png`, `Elt_LI.png`, and `Elt_WA.png`. Authentic neutral job indicators are `HE_JobBarbarian.png`, `HE_JobFighter.png`, `HE_JobGunner.png`, `HE_JobKnight.png`, `HE_JobLancer.png`, `HE_JobMagician.png`, `HE_JobRanger.png`, `HE_JobRogue.png`, `HE_JobSamurai.png`, and `HE_JobSupport.png`. Native symbols `GetSpriteNameForJob`, `SpriteNameFromClass`, and `UIUnitCard::RenderClassInfo`, plus the complete `IN`/`OUT`/`Selected` frame families, support their job-indicator role. `HE_JobFighter` is presented as Brawler because `Fighter` is the internal source class. The five `Rs_HeJob_*` frames are awakening relic resources defined by `Items.xml`; they must not be used as job indicators.

Decoded or copied application-ready assets belong under ignored `local/proprietary/`. APKs and extracted sources remain read-only inputs. Run `python3 scripts/extract-cta-ui-icons.py samples/bluestacks/apk/base.apk local/proprietary/ui-icons` to reproduce the current UI icons.

### Version reconciliation

Before replacing the retained corpus, record and compare:

- `dumpsys package` version name/code;
- APK split list and SHA-256 hashes;
- `cache/content/` file inventory and hashes;
- patch bundle names, hashes, member lists, and timestamps;
- hashes for canonical sources such as `Heroes.csv`, `Persos.xml`, `Skills.xml`, `Items.xml`, and `Config_en.xml`.

Do not infer that patch filename timestamps equal the APK release or extraction time.

## Targeted BlueStacks follow-up

No follow-up is required to use the existing hero importer. The following are the only remaining retrieval questions worth asking of BlueStacks:

1. Does `/sdcard/Android/obb/com.godzilab.idlerpg` exist and contain files?
2. Are there package-scoped files outside the already listed `/sdcard/Android/data/com.godzilab.idlerpg` tree?
3. Does the production package permit any read-only listing of app-private databases, shared preferences, manifests, or caches?

If a refresh is requested, commands must be generated for Windows PowerShell using BlueStacks' `HD-Adb.exe`, then executed by the user. Do not use Linux ADB. App-private access failure should be recorded as an expected platform boundary, not worked around by modifying or rooting the app.

## Current conclusion

BlueStacks `2.0.821` APKs and shared runtime cache are the repository's authoritative extraction sources. Installed-package and current public Google Play evidence agree on 2.0.821/200821. Report 25 additionally reconciles all four APK hashes, all 1,320 shared files, all four patch bundles, canonical hero sources, current parser identities, every audit, and 116/116 local portraits with no drift. Reports `01`–`16` preserve investigation history but no longer define current blockers or next steps. A new pull is needed only when the installed version or retained source hashes change.
