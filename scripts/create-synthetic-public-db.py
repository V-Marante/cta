#!/usr/bin/env python3
"""Create a minimal synthetic database for container CI; contains no game data."""
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

destination = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/public/cta.sqlite")
destination.parent.mkdir(parents=True, exist_ok=True)
destination.unlink(missing_ok=True)
with sqlite3.connect(destination) as db:
    db.executescript("""
    CREATE TABLE release_info(id TEXT PRIMARY KEY, game_id TEXT NOT NULL, game_version TEXT NOT NULL, finished_at TEXT NOT NULL);
    CREATE TABLE catalog_entities(release_id TEXT NOT NULL, kind TEXT NOT NULL, entity_id TEXT NOT NULL, payload_json TEXT NOT NULL, PRIMARY KEY(release_id,kind,entity_id));
    CREATE TABLE catalog_text(release_id TEXT NOT NULL, kind TEXT NOT NULL, entity_id TEXT NOT NULL, locale TEXT NOT NULL, field TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(release_id,kind,entity_id,locale,field));
    CREATE TABLE catalog_relations(release_id TEXT NOT NULL, kind TEXT NOT NULL, source_id TEXT NOT NULL, target_id TEXT NOT NULL, ordinal INTEGER NOT NULL, payload_json TEXT NOT NULL, PRIMARY KEY(release_id,kind,source_id,target_id,ordinal));
    INSERT INTO release_info VALUES('synthetic','com.godzilab.idlerpg','synthetic','2026-01-01T00:00:00Z');
    INSERT INTO catalog_entities VALUES('synthetic','hero','SyntheticHero','{"canonical_name":"Synthetic Hero","class":"Ranger","tribe":"Synthetic","element":"Fire","damage_type":"Physical","sex":"n/a","mobility":"ground","traits":[],"stats":{},"stat_semantics":{},"source_calculations":{},"passive":{},"progression":{},"progression_semantics":{},"availability":{},"legacy_availability":{}}');
    INSERT INTO catalog_entities VALUES('synthetic','hero_classification','SyntheticHero','{"kind":"collectible","owner_id":null}');
    INSERT INTO catalog_entities VALUES('synthetic','portrait','SyntheticHero','{"frame_name":"synthetic.png"}');
    INSERT INTO catalog_text VALUES('synthetic','hero','SyntheticHero','en','name','Synthetic Hero');
    """)
print(destination)
digest = hashlib.sha256(destination.read_bytes()).hexdigest()
(destination.parent / "import-manifest.json").write_text(json.dumps({
    "dataVersion": "2026-01-01", "dataImportId": "synthetic",
    "gameVersion": "synthetic", "databaseHash": f"sha256:{digest}",
    "assetsVersion": "synthetic",
}, indent=2) + "\n")
