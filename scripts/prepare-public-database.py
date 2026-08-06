#!/usr/bin/env python3
"""Create a sanitized public SQLite copy without local extraction provenance."""
import argparse
import shutil
import sqlite3
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(f"source database does not exist: {args.source}")
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    if args.destination.exists():
        args.destination.unlink()
    shutil.copyfile(args.source, args.destination)
    with sqlite3.connect(args.destination) as db:
        db.execute("PRAGMA foreign_keys=ON")
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"import_runs", "entities", "relations", "localizations"}
        if not required <= tables:
            raise SystemExit(f"database schema is missing: {sorted(required - tables)}")
        db.execute("UPDATE import_runs SET source_root='[redacted]', error_message=NULL")
        for table in ("entities", "relations", "localizations"):
            db.execute(f"UPDATE {table} SET source_path=NULL, source_record=NULL")
        if "artifacts" in tables:
            db.execute("DELETE FROM artifacts")
        if "parser_executions" in tables:
            db.execute("UPDATE parser_executions SET artifact_path='[redacted]' || rowid")
        if "diagnostics" in tables:
            db.execute("DELETE FROM diagnostics")
        db.execute("VACUUM")
    args.destination.chmod(0o444)
    print(f"sanitized public database: {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
