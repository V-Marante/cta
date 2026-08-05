# Phase 8: APK Inspection

## Status

Not performed.

No APK or split APK files were copied into `samples/apk/`.

`aapt2` is now available for future inspection once APKs are copied.

## APKs Expected

Log-inferred package files:

- `base.apk`
- `split_config.mdpi.apk`
- `split_config.sv.apk`
- `split_config.x86_64.apk`

## Blocker

ADB was unavailable, and the image-copy branch stopped before copying `userdata.img`. Therefore there was no copied APK to inspect with:

```bash
unzip -l
aapt2 dump badging
apkanalyzer manifest print
```

## Next APK Inspection Step

After the APKs are copied, inspect archive listings first and look for:

- `AndroidManifest.xml`
- `classes*.dex`
- `resources.arsc`
- `lib/x86_64/*.so`
- `assets/`
- Unity, Unreal, Cocos2d-x, or native Android framework markers
