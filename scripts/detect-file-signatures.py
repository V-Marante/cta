#!/usr/bin/env python3
"""Detect common file signatures without loading whole files."""

from __future__ import annotations

import argparse
from pathlib import Path


SIGNATURES = [
    ("SQLite", b"SQLite format 3\x00"),
    ("ZIP/APK", b"PK\x03\x04"),
    ("ZIP empty", b"PK\x05\x06"),
    ("PNG", b"\x89PNG\r\n\x1a\n"),
    ("JPEG", b"\xff\xd8\xff"),
    ("GIF", b"GIF8"),
    ("ELF", b"\x7fELF"),
    ("DEX", b"dex\n"),
    ("UnityFS AssetBundle", b"UnityFS"),
    ("UnityWeb AssetBundle", b"UnityWeb"),
    ("UnityRaw AssetBundle", b"UnityRaw"),
    ("Unity serialized assets", b"\x00\x00\x00"),
    ("7z", b"7z\xbc\xaf\x27\x1c"),
    ("GZip", b"\x1f\x8b\x08"),
    ("XZ", b"\xfd7zXZ\x00"),
    ("RAR", b"Rar!\x1a\x07"),
    ("Android sparse image", b"\x3a\xff\x26\xed"),
    ("Windows PE", b"MZ"),
]


def classify(header: bytes) -> str:
    for name, sig in SIGNATURES:
        if header.startswith(sig):
            if name == "Unity serialized assets" and len(header) >= 20:
                return "Possible Unity serialized asset"
            return name
    if b"ustar" in header[257:265]:
        return "TAR"
    if header[:4] in {b"\x7fELF", b"UE4\x00", b"UE5\x00"}:
        return "Binary package"
    text = sum(1 for b in header if b in b"\t\r\n" or 32 <= b < 127)
    return "Text-like" if header and text / len(header) > 0.85 else "Unknown binary"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Files to inspect")
    parser.add_argument("--bytes", type=int, default=64, help="Header bytes to read")
    args = parser.parse_args()

    for item in args.paths:
        path = Path(item)
        try:
            header = path.read_bytes()[: args.bytes]
        except OSError as exc:
            print(f"{path}\tERROR\t{exc}")
            continue
        print(f"{path}\t{classify(header)}\t{header.hex()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
