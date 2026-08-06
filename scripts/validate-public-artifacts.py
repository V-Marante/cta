#!/usr/bin/env python3
"""Allow-list validation for the explicitly prepared public release directory."""
import argparse
import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path

ALLOWED_ROOT_FILES = {"cta.sqlite", "import-manifest.json", "asset-manifest.json"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".webp", ".avif"}
EXPECTED_TABLES = {"release_info", "catalog_entities", "catalog_text", "catalog_relations"}
ALLOWED_COLUMNS = {
    "release_info": {"id", "game_id", "game_version", "finished_at"},
    "catalog_entities": {"release_id", "kind", "entity_id", "payload_json"},
    "catalog_text": {"release_id", "kind", "entity_id", "locale", "field", "value"},
    "catalog_relations": {"release_id", "kind", "source_id", "target_id", "ordinal", "payload_json"},
}
REQUIRED_COLUMNS = {
    table: columns for table, columns in ALLOWED_COLUMNS.items()
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
    manifest = root / "import-manifest.json"
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
        required = EXPECTED_TABLES
        if not required <= tables:
            fail(f"missing SQLite tables: {sorted(required - tables)}")
        for table in tables & ALLOWED_COLUMNS.keys():
            columns = {row[1] for row in db.execute(f"PRAGMA table_info({table})")}
            if columns - ALLOWED_COLUMNS[table]:
                fail(f"unexpected SQLite columns in {table}: {sorted(columns - ALLOWED_COLUMNS[table])}")
            if table in REQUIRED_COLUMNS and not REQUIRED_COLUMNS[table] <= columns:
                fail(f"missing SQLite columns in {table}: {sorted(REQUIRED_COLUMNS[table] - columns)}")
        if db.execute("SELECT count(*) FROM release_info").fetchone()[0] != 1:
            fail("public database must contain exactly one release")
        release_id, game_version = db.execute("SELECT id,game_version FROM release_info").fetchone()
        entity_kinds = {row[0] for row in db.execute("SELECT DISTINCT kind FROM catalog_entities")}
        allowed_entity_kinds = {"hero", "hero_classification", "portrait", "skill", "acquisition_source"}
        if entity_kinds - allowed_entity_kinds:
            fail(f"unexpected public entity kinds: {sorted(entity_kinds - allowed_entity_kinds)}")
        relation_kinds = {row[0] for row in db.execute("SELECT DISTINCT kind FROM catalog_relations")}
        if relation_kinds - {"character_skill", "hero_acquisition"}:
            fail(f"unexpected public relation kinds: {sorted(relation_kinds)}")
        non_collectible = db.execute("""SELECT count(*) FROM catalog_entities
            WHERE kind='hero_classification' AND json_extract(payload_json,'$.kind')!='collectible'""").fetchone()[0]
        if non_collectible:
            fail("public database contains non-collectible hero classifications")
        for table in required:
            for row in db.execute(f"SELECT * FROM {table}"):
                if SENSITIVE.search(" ".join(str(value) for value in row if value is not None)):
                    fail(f"obvious local path or credential-like value in table {table}")
    if manifest.is_file():
        try:
            metadata = json.loads(manifest.read_text())
        except (OSError, json.JSONDecodeError) as error:
            fail(f"invalid import-manifest.json: {error}")
        digest = f"sha256:{hashlib.sha256(database.read_bytes()).hexdigest()}"
        if metadata.get("databaseHash") != digest:
            fail("import manifest databaseHash does not match cta.sqlite")
        if metadata.get("dataImportId") != release_id or metadata.get("gameVersion") != game_version:
            fail("import manifest release metadata does not match release_info")
    print(f"public artifacts valid: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
