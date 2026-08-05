#!/usr/bin/env python3
"""Hash files safely with size limits and CSV output."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(paths: list[str], recursive: bool):
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            yield path
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            for child in sorted(path.glob(pattern)):
                if child.is_file() and not child.is_symlink():
                    yield child


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Files or directories")
    parser.add_argument("--recursive", action="store_true", help="Recurse into directories")
    parser.add_argument("--max-size-mb", type=int, default=512, help="Skip hashing files larger than this")
    parser.add_argument("--output", default="-", help="CSV output path, or - for stdout")
    args = parser.parse_args()

    out = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
    with out:
        writer = csv.DictWriter(out, fieldnames=["path", "size", "sha256", "status", "error"])
        writer.writeheader()
        for path in iter_files(args.paths, args.recursive):
            try:
                size = path.stat().st_size
                if size > args.max_size_mb * 1024 * 1024:
                    writer.writerow({"path": str(path), "size": size, "sha256": "", "status": "skipped_size_limit", "error": ""})
                    continue
                writer.writerow({"path": str(path), "size": size, "sha256": sha256(path), "status": "ok", "error": ""})
            except OSError as exc:
                writer.writerow({"path": str(path), "size": "", "sha256": "", "status": "error", "error": str(exc)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
