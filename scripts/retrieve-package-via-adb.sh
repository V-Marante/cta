#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/retrieve-package-via-adb.sh --package com.godzilab.idlerpg --output-dir samples

Standard, non-root ADB retrieval:
  - records adb devices, getprop, pm path, and dumpsys package
  - pulls APK/split APK files returned by pm path
  - lists package-scoped shared storage
  - does not recurse through app-private /data directories
USAGE
}

PACKAGE=""
OUT="samples"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --package) PACKAGE="$2"; shift 2 ;;
    --output-dir) OUT="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$PACKAGE" ]]; then
  usage >&2
  exit 2
fi

mkdir -p "$OUT/apk" "$OUT/runtime" "logs"

adb devices -l | tee "logs/adb-devices.txt"
adb shell getprop > "logs/adb-getprop.txt"
adb shell pm path "$PACKAGE" | tee "logs/${PACKAGE}.pm-path.txt"
adb shell dumpsys package "$PACKAGE" > "logs/${PACKAGE}.dumpsys-package.txt"

while IFS= read -r line; do
  [[ "$line" == package:* ]] || continue
  remote="${line#package:}"
  adb pull "$remote" "$OUT/apk/"
done < "logs/${PACKAGE}.pm-path.txt"

adb shell ls -la "/sdcard/Android/data/$PACKAGE" > "logs/${PACKAGE}.sdcard-android-data.txt" 2>&1 || true
adb shell ls -la "/sdcard/Android/obb/$PACKAGE" > "logs/${PACKAGE}.sdcard-android-obb.txt" 2>&1 || true

sha256sum "$OUT"/apk/*.apk > "logs/${PACKAGE}.apk-sha256.txt" 2>/dev/null || true
echo "Done. APKs, if accessible, are in $OUT/apk/."
