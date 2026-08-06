#!/usr/bin/env python3
"""Allow-list validation for the explicitly prepared public release directory."""
import argparse
import os
import re
import sqlite3
from pathlib import Path

ALLOWED_ROOT_FILES = {"cta.sqlite", "import-manifest.json", "asset-manifest.json"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".webp", ".avif"}
EXPECTED_TABLES = {"import_runs", "parser_executions", "artifacts", "entities", "relations", "localizations", "diagnostics", "sqlite_sequence"}
ALLOWED_COLUMNS = {
    "import_runs": {"id", "game_id", "game_version", "build", "content_version", "source_digest", "parser_set_digest", "source_root", "status", "started_at", "finished_at", "version_metadata_json", "error_message"},
    "parser_executions": {"import_id", "artifact_path", "parser_id", "parser_version", "output_schema_version", "status", "entity_count", "relation_count", "localization_count"},
    "artifacts": {"import_id", "relative_path", "byte_size", "sha256", "media_type", "parser_id"},
    "entities": {"import_id", "parser_id", "output_schema_version", "namespace", "entity_key", "ordinal", "payload_json", "source_path", "source_line", "source_column", "source_record"},
    "relations": {"id", "import_id", "parser_id", "output_schema_version", "relation", "source_namespace", "source_key", "target_namespace", "target_key", "ordinal", "payload_json", "source_path", "source_line", "source_column", "source_record"},
    "localizations": {"import_id", "parser_id", "output_schema_version", "namespace", "entity_key", "locale", "field", "value", "source_path", "source_line", "source_column", "source_record"},
    "diagnostics": {"id", "import_id", "severity", "code", "message", "parser_id", "source_path", "source_line", "source_column", "source_record", "details_json"},
}
REQUIRED_COLUMNS = {
    "import_runs": {"id", "game_id", "status", "finished_at"},
    "entities": {"import_id", "namespace", "entity_key", "payload_json"},
    "relations": {"import_id", "relation", "source_key", "target_key", "ordinal", "payload_json", "source_path", "source_record"},
    "localizations": {"import_id", "namespace", "entity_key", "locale", "field", "value"},
}
MAX_DATABASE = 250 * 1024 * 1024
MAX_IMAGE = 5 * 1024 * 1024
SENSITIVE = re.compile(r"(/home/|/Users/|[A-Za-z]:\\Users\\|BEGIN [A-Z ]*PRIVATE KEY|(?:token|password|secret)\s*[=:])", re.I)


def fail(message: str) -> None:
    raise SystemExit(f"public artifact validation failed: {message}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default="artifacts/public", type=Path)
    args = parser.parse_args()
    root = args.directory.resolve()
    if not root.is_dir():
        fail(f"expected directory does not exist: {root}")
    database = root / "cta.sqlite"
    if not database.is_file() or database.is_symlink():
        fail("cta.sqlite is missing or is a symlink")
    if database.stat().st_size > MAX_DATABASE:
        fail("cta.sqlite exceeds 250 MiB")
    for path in root.rglob("*"):
        if path.is_symlink():
            fail(f"symlink is not allowed: {path.relative_to(root)}")
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if len(relative.parts) == 1 and path.name not in ALLOWED_ROOT_FILES:
            fail(f"unexpected root file: {relative}")
        if len(relative.parts) > 1:
            if relative.parts[0] != "portraits" or path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
                fail(f"unexpected file: {relative}")
            if path.stat().st_size > MAX_IMAGE:
                fail(f"image exceeds 5 MiB: {relative}")
        if path.suffix.lower() in {".apk", ".ipa", ".zip", ".dll", ".exe", ".so", ".bundle", ".env"}:
            fail(f"forbidden file type: {relative}")
    uri = f"file:{database}?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        check = db.execute("PRAGMA quick_check").fetchone()[0]
        if check != "ok":
            fail(f"SQLite quick_check returned {check}")
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        unexpected = tables - EXPECTED_TABLES
        if unexpected:
            fail(f"unexpected SQLite tables: {sorted(unexpected)}")
        required = {"import_runs", "entities", "relations", "localizations"}
        if not required <= tables:
            fail(f"missing SQLite tables: {sorted(required - tables)}")
        for table in tables & ALLOWED_COLUMNS.keys():
            columns = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
            if columns - ALLOWED_COLUMNS[table]:
                fail(f"unexpected SQLite columns in {table}: {sorted(columns - ALLOWED_COLUMNS[table])}")
            if table in REQUIRED_COLUMNS and not REQUIRED_COLUMNS[table] <= columns:
                fail(f"missing SQLite columns in {table}: {sorted(REQUIRED_COLUMNS[table] - columns)}")
        for table in required:
            for row in db.execute(f"SELECT * FROM {table}"):
                if SENSITIVE.search(" ".join(str(value) for value in row if value is not None)):
                    fail(f"obvious local path or credential-like value in table {table}")
    print(f"public artifacts valid: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
