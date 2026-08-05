#!/usr/bin/env python3
"""Create CSV/JSON metadata inventory for candidate game files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path

INTERESTING_EXTENSIONS = {
    ".apk", ".apks", ".xapk", ".zip", ".obb", ".db", ".sqlite", ".sqlite3",
    ".json", ".xml", ".csv", ".tsv", ".bytes", ".bin", ".dat", ".bundle",
    ".asset", ".assets", ".resource", ".resources", ".ress", ".manifest",
    ".catalog", ".hash", ".pack", ".pak", ".ucas", ".utoc", ".proto", ".pb",
    ".dll", ".so", ".dex", ".img", ".png", ".jpg", ".jpeg", ".ico",
}

KEYWORDS = (
    "google", "play games", "android", "emulator", "crosvm", "godzilab",
    "godzillab", "godzilab", "imperia", "stillfront", "crush", "idlerpg",
    "com.godzilab.idlerpg",
)


def safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return ""


def hex_head(path: Path, size: int) -> str:
    with path.open("rb") as handle:
        return handle.read(size).hex()


def sha256(path: Path, max_size: int) -> tuple[str, str]:
    size = path.stat().st_size
    if size > max_size:
        return "", "skipped_size_limit"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest(), "ok"


def classify(path: Path, header: bytes) -> str:
    if header.startswith(b"SQLite format 3\x00"):
        return "SQLite database"
    if header.startswith(b"PK\x03\x04"):
        return "ZIP-compatible archive"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG image"
    if header.startswith(b"\xff\xd8\xff"):
        return "JPEG image"
    if header.startswith(b"\x7fELF"):
        return "ELF shared object"
    if header.startswith(b"dex\n"):
        return "Android DEX"
    if header.startswith(b"UnityFS"):
        return "Unity AssetBundle"
    if header.startswith(b"MZ"):
        return "Windows PE executable/library"
    if header.startswith(b"\x3a\xff\x26\xed"):
        return "Android sparse image"
    mime = mimetypes.guess_type(path.name)[0]
    return mime or "unknown"


def reason(path: Path, root: Path, ftype: str) -> str:
    text = str(path).lower()
    reasons = []
    if path.suffix.lower() in INTERESTING_EXTENSIONS:
        reasons.append(f"interesting extension {path.suffix.lower() or '(none)'}")
    if any(k in text for k in KEYWORDS):
        reasons.append("game/platform keyword in path")
    if ftype != "unknown":
        reasons.append(f"signature/type: {ftype}")
    if safe_rel(path, root).startswith("userdata_"):
        reasons.append("runtime Android user-data tree")
    return "; ".join(reasons)


def iter_files(root: Path, max_depth: int | None):
    root = root.resolve()
    for current, dirs, files in os.walk(root, followlinks=False):
        cur = Path(current)
        if max_depth is not None:
            depth = len(cur.relative_to(root).parts)
            if depth >= max_depth:
                dirs[:] = []
        dirs[:] = sorted(d for d in dirs if not (cur / d).is_symlink())
        for name in sorted(files):
            path = cur / name
            if not path.is_symlink():
                yield path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", required=True, help="Source root to scan; repeatable")
    parser.add_argument("--output-dir", required=True, help="Directory for files.csv and files.json")
    parser.add_argument("--max-depth", type=int, default=None, help="Optional recursion depth limit")
    parser.add_argument("--max-hash-size-mb", type=int, default=512, help="Do not hash files larger than this")
    parser.add_argument("--header-bytes", type=int, default=64)
    parser.add_argument("--include-all", action="store_true", help="Include files even without interesting extension/signature/path")
    args = parser.parse_args()

    rows = []
    max_hash = args.max_hash_size_mb * 1024 * 1024
    for raw_root in args.source:
        root = Path(raw_root)
        if not root.exists():
            rows.append({"source_root": raw_root, "path": raw_root, "status": "missing"})
            continue
        for path in iter_files(root, args.max_depth):
            try:
                stat = path.stat()
                header = path.open("rb").read(args.header_bytes)
                ftype = classify(path, header)
                interesting = path.suffix.lower() in INTERESTING_EXTENSIONS or any(k in str(path).lower() for k in KEYWORDS) or ftype != "unknown"
                if not interesting and not args.include_all:
                    continue
                digest, hash_status = sha256(path, max_hash)
                rows.append({
                    "source_root": str(root),
                    "path": str(path),
                    "relative_path": safe_rel(path, root),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(getattr(stat, "st_ctime", 0), timezone.utc).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    "sha256": digest,
                    "hash_status": hash_status,
                    "mime_or_type": ftype,
                    "header_hex": header.hex(),
                    "relevance": reason(path, root, ftype),
                    "status": "ok",
                })
            except OSError as exc:
                rows.append({"source_root": str(root), "path": str(path), "status": "error", "error": str(exc)})

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with (outdir / "files.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (outdir / "files.json").write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    print(f"inventory_rows={len(rows)} output_dir={outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
