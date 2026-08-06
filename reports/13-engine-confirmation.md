# Phase 8: Engine Confirmation

> **Superseded.** The retained BlueStacks x86_64 split confirms a custom native GodzilabEngine. See `reports/19-bluestacks-reconciliation.md`.

## Result

Engine remains unresolved.

Confidence: low.

## Evidence Available

Confirmed from Android logs:

- Android package: `com.godzilab.idlerpg`
- installed version: `2.0.822`
- version code: `200822`
- ABI: `x86_64`
- APK path: `/data/app/.../base.apk`
- split APKs: `mdpi`, `sv`, `x86_64`
- runtime cache JARs under `/data/user/0/com.godzilab.idlerpg/cache`

## Evidence Not Yet Available

No copied APK means no direct inspection for:

- `libunity.so`
- `libil2cpp.so`
- `global-metadata.dat`
- `assets/bin/Data/`
- `libcocos2dcpp.so`
- `libUE4.so`
- `*.pak`
- `assets/` content

## Current Interpretation

The package uses standard Android package/split layout and ART optimization. The game engine cannot be established from logs alone.
