# Phase 3: Engine Detection

> **Superseded.** BlueStacks APK inspection confirmed a custom native GodzilabEngine; the engine is no longer unresolved. See `reports/19-bluestacks-reconciliation.md`.

## Result

Likely game engine: unresolved from host-visible game files.

Confidence: low for the game itself; high that Google Play Games is using Android virtualization through `crosvm`.

## Evidence

Confirmed platform/runtime indicators:

- `C:\Program Files\Google\Play Games\current\emulator\crosvm.exe`
- `C:\Program Files\Google\Play Games\current\emulator\avd\aggregate.img`
- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\userdata_<instance>.gz5\avd\userdata.img`
- `C:\Users\<windows-user>\AppData\Local\Google\Play Games\Logs\AndroidSerial.log`
- `store.db` table `UserDataState` contains user data set ID `bdhfv2nx.gz5` and AVD serial `043383d722e244e2997b24a312d415fa`

Host-visible Play Games Services indicators:

- `flutter_windows.dll`
- `overlay.assets`
- `windows.assets`
- `liboverlay.so`
- `libwindows.so`

These belong to Google Play Games Services, not necessarily the game.

## Unity Indicators

No host-visible game-specific Unity files were found in this phase:

- no `UnityPlayer.dll` for the Android app
- no `globalgamemanagers`
- no `resources.assets` tied to `com.godzilab.idlerpg`
- no `sharedassets*.assets`
- no `global-metadata.dat`
- no `libil2cpp.so`
- no `Assembly-CSharp.dll`

Because the package APK/splits are likely inside the Android user-data image or Play Games package store, Unity cannot yet be confirmed or denied.

## Unreal Indicators

No game-specific `*.pak`, `*.utoc`, `*.ucas`, `UE4`, or `UE5` indicators were found as ordinary host-visible files.

## Native Android Indicators

Confirmed Android package identity: `com.godzilab.idlerpg`.

Unresolved until APK/splits are located:

- `AndroidManifest.xml`
- `classes.dex`
- `resources.arsc`
- `lib/*/*.so`
- `assets/`
- `res/`

## Next Engine Step

Perform read-only package-path discovery inside the Google Play Games Android environment or image. Once the APK/split APKs are copied to `samples/`, inspect archive contents first and look for Unity/IL2CPP/Mono, Unreal, Cocos2d-x, or native Android markers.
