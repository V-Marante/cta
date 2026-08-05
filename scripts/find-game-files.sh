#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s --output-dir DIR [--source DIR ...]\n' "$0"
}

OUT=""
SOURCES=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir) OUT="$2"; shift 2 ;;
    --source) SOURCES+=("$2"); shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$OUT" ]]; then
  usage >&2
  exit 2
fi

if [[ ${#SOURCES[@]} -eq 0 ]]; then
  SOURCES=(
    "/mnt/c/Users/${USER:-}/AppData/Local/Google/Play Games"
    "/mnt/c/ProgramData/Google/Play Games"
    "/mnt/c/ProgramData/Google/Play Games Services"
    "/mnt/c/Program Files/Google/Play Games"
    "/mnt/c/Program Files/Google/Play Games Services"
  )
fi

mkdir -p "$OUT"
LOG="$OUT/find-game-files.log"
: > "$LOG"
for src in "${SOURCES[@]}"; do
  if [[ -d "$src" ]]; then
    find "$src" -xdev -type f \
      \( -iname '*crush*' -o -iname '*godzilab*' -o -iname '*idlerpg*' -o -iname '*.apk' -o -iname '*.db' -o -iname '*.json' -o -iname '*.xml' -o -iname '*.img' -o -iname '*.bundle' -o -iname '*.assets' -o -iname '*.pak' -o -iname '*.pb' \) \
      -print >> "$OUT/candidate-paths.txt" 2>> "$LOG"
  else
    printf 'missing source: %s\n' "$src" >> "$LOG"
  fi
done

sort -u "$OUT/candidate-paths.txt" -o "$OUT/candidate-paths.txt"
printf 'wrote %s and %s\n' "$OUT/candidate-paths.txt" "$LOG"
