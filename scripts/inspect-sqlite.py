#!/usr/bin/env python3
"""Inspect copied SQLite databases without dumping full contents."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def inspect_db(path: Path, sample_rows: int) -> dict:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cur = con.cursor()
    result = {"path": str(path), "integrity_check": cur.execute("pragma integrity_check").fetchone()[0], "objects": []}
    objects = cur.execute(
        "select type, name, sql from sqlite_master where type in ('table','view','index') order by type, name"
    ).fetchall()
    for typ, name, sql in objects:
        item = {"type": typ, "name": name, "sql": sql}
        if typ == "table":
            try:
                item["row_count"] = cur.execute(f'select count(*) from "{name}"').fetchone()[0]
                cols = [row[1] for row in cur.execute(f'pragma table_info("{name}")').fetchall()]
                item["columns"] = cols
                rows = cur.execute(f'select * from "{name}" limit ?', (sample_rows,)).fetchall()
                safe_rows = []
                for row in rows:
                    safe_rows.append([
                        f"<blob {len(value)} bytes>" if isinstance(value, bytes) else value
                        for value in row
                    ])
                item["sample_rows"] = safe_rows
            except sqlite3.Error as exc:
                item["error"] = str(exc)
        result["objects"].append(item)
    con.close()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("databases", nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--sample-rows", type=int, default=10)
    args = parser.parse_args()

    report = [inspect_db(Path(db), args.sample_rows) for db in args.databases]
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
