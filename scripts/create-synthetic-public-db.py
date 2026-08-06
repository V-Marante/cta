#!/usr/bin/env python3
"""Create a minimal synthetic database for container CI; contains no game data."""
import sqlite3
import sys
from pathlib import Path

destination = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/public/cta.sqlite")
destination.parent.mkdir(parents=True, exist_ok=True)
destination.unlink(missing_ok=True)
with sqlite3.connect(destination) as db:
    db.executescript("""
    CREATE TABLE import_runs(id TEXT PRIMARY KEY, game_id TEXT, status TEXT, finished_at TEXT);
    CREATE TABLE entities(import_id TEXT, namespace TEXT, entity_key TEXT, payload_json TEXT);
    CREATE TABLE localizations(import_id TEXT, namespace TEXT, entity_key TEXT, locale TEXT, field TEXT, value TEXT);
    CREATE TABLE relations(import_id TEXT, relation TEXT, source_key TEXT, target_key TEXT, ordinal INTEGER, payload_json TEXT, source_path TEXT, source_record TEXT);
    INSERT INTO import_runs VALUES('synthetic','com.godzilab.idlerpg','succeeded','2026-01-01T00:00:00Z');
    INSERT INTO entities VALUES('synthetic','hero','SyntheticHero','{"canonical_name":"Synthetic Hero","class":"Ranger","tribe":"Synthetic","element":"Fire","damage_type":"Physical","sex":"n/a","mobility":"ground","traits":[],"stats":{},"stat_semantics":{},"source_calculations":{},"passive":{},"progression":{},"progression_semantics":{},"availability":{},"legacy_availability":{},"raw":{}}');
    INSERT INTO entities VALUES('synthetic','hero_classification','SyntheticHero','{"kind":"collectible","owner_id":null}');
    INSERT INTO localizations VALUES('synthetic','hero','SyntheticHero','en','name','Synthetic Hero');
    """)
print(destination)
