#!/usr/bin/env python3
"""Stream printable strings from files and search game-data terms."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

TERMS = [
    "hero", "character", "unit", "item", "weapon", "armor", "skill", "ability",
    "damage", "health", "rarity", "level", "upgrade", "enemy", "stage", "quest",
    "reward", "currency", "shop", "description", "localization", "language",
    "hero_id", "item_id", "unit_id", "display_name", "description_key",
    "rarity_id", "base_damage", "max_level", "http://", "https://",
]


def strings_from_file(path: Path, min_len: int, chunk_size: int = 1024 * 1024):
    pattern = re.compile(rb"[ -~]{%d,}" % min_len)
    tail = b""
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            data = tail + chunk
            matches = list(pattern.finditer(data))
            cutoff = max(0, len(data) - min_len)
            for match in matches:
                if match.end() <= cutoff:
                    yield match.group().decode("utf-8", "replace")
            tail = data[-min_len:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-len", type=int, default=5)
    parser.add_argument("--limit-per-file", type=int, default=200)
    args = parser.parse_args()

    term_lc = [term.lower() for term in TERMS]
    with Path(args.output).open("w", encoding="utf-8") as out:
        for raw in args.files:
            path = Path(raw)
            written = 0
            try:
                for value in strings_from_file(path, args.min_len):
                    lower = value.lower()
                    if any(term in lower for term in term_lc):
                        out.write(f"{path}\t{value[:500]}\n")
                        written += 1
                        if written >= args.limit_per_file:
                            break
            except OSError as exc:
                out.write(f"{path}\tERROR: {exc}\n")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
