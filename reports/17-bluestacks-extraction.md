# BlueStacks Package and Game-Data Extraction

> **Current retained extraction baseline.** BlueStacks `2.0.821` was reconfirmed as the latest version offered by the installed BlueStacks distribution on 2026-08-06. See `reports/19-bluestacks-reconciliation.md` for the cross-distribution version caveat, gaps, and source precedence.

## Result

The extraction blocker is resolved. BlueStacks' Windows `HD-Adb.exe` exposed the installed package and allowed standard, non-root pulls of both APK files and shared runtime data.

Package facts:

- package: `com.godzilab.idlerpg`
- version: `2.0.821` (`versionCode=200821`)
- primary ABI: `x86_64`
- Android: 9
- selected ADB serial: `127.0.0.1:5555`

Copied APKs:

- `base.apk`
- `split_config.en.apk`
- `split_config.hdpi.apk`
- `split_config.x86_64.apk`

The APK hashes are recorded in `samples/bluestacks/logs/com.godzilab.idlerpg.apk-sha256.txt`.

## Engine Confirmation

The game does not use Unity. `split_config.x86_64.apk` contains a 20.9 MB `lib/x86_64/libMain.so`. Native strings and symbols identify:

- `GodzilabEngine`
- JNI entry points for `com.godzilab.idlerpg.Renderer`
- OpenGL ES 1/2 and EGL dependencies
- Spine animation runtime
- FMOD and FMOD Studio
- RapidXML
- Box2D symbols

The PVR textures, plist atlases, Spine JSON/atlas files, and native renderer are consistent with this custom C++ engine.

## Extracted Game Data

The accessible package shared-data directory contained about 58 MB across 1,300+ materialized content files. Important files under `samples/bluestacks/shared-data/cache/content/` include:

| File | Observed structure |
|---|---|
| `Heroes.csv` | 149 rows including header, 43 first-row columns |
| `Artifacts.csv` | 196 rows including header |
| `Runes.csv` | 44 rows including header |
| `RuneSets.csv` | 24 rows including header |
| `Modules.csv` | 326 rows including header |
| `Persos.xml` | `characters` root, 217 direct children |
| `Skills.xml` | `skills` root, 427 direct children |
| `Items.xml` | `items` root, 349 direct children |
| `Dungeons.xml` | `dungeons` root, 107 direct children |

Other extracted categories include achievements, armory data, quests, guild progression, player levels, paragon data, localized names/descriptions, sprite atlases, PVR textures, shaders, Spine animations, and FMOD banks.

## Patch Bundles

The following `.bin` files are ordinary ZIP-compatible archives despite their extension:

- `260330102436_data.bin`
- `260330102439_data_ui0_dl.bin`
- `260330102453_data_env0_dl.bin`
- `260330102513_data_monster_dl.bin`

Their names and member timestamps indicate the currently materialized download was assembled around 2026-03-30. The SHA-256 of the patch copy of `Heroes.csv` exactly matches the materialized cache copy:

`0421e0f25269cc370c2aa6b5e25bb6681189de6496e30751de930d8a3f7b0aba`

Downloaded image members use paths such as `Images/_dl/`; the runtime cache materializes many of these files in a flattened content directory.

## Validation

The WSL validation summary is in `reports/bluestacks-structured-summary.json`. All primary gameplay XML files inspected were parseable. One localized file, `Skills_ru.xml`, is malformed at line 329, column 226; this does not affect the canonical `Skills.xml` dataset.

## Conclusion

The most useful extraction source is now the BlueStacks shared runtime cache, not the APK or emulator disk image. The patch bundles preserve transport structure, while `cache/content/` provides the simplest directly usable view of the current game data and assets.
