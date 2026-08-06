import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicDatabaseProjectionTests(unittest.TestCase):
    def test_projects_only_latest_collectible_catalogue_without_raw_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "private.sqlite"
            public = Path(directory) / "public.sqlite"
            with sqlite3.connect(source) as db:
                db.executescript("""
                CREATE TABLE import_runs(id TEXT,game_id TEXT,game_version TEXT,status TEXT,finished_at TEXT);
                CREATE TABLE entities(import_id TEXT,namespace TEXT,entity_key TEXT,payload_json TEXT);
                CREATE TABLE relations(import_id TEXT,relation TEXT,source_key TEXT,target_key TEXT,ordinal INTEGER,payload_json TEXT);
                CREATE TABLE localizations(import_id TEXT,namespace TEXT,entity_key TEXT,locale TEXT,field TEXT,value TEXT);
                INSERT INTO import_runs VALUES('old','game','1','succeeded','2025-01-01');
                INSERT INTO import_runs VALUES('current','game','2','succeeded','2026-01-01');
                INSERT INTO entities VALUES('current','hero','Public','{"canonical_name":"Public","traits":[],"raw":{"secret":"private"},"source_path":"/home/person/game.csv"}');
                INSERT INTO entities VALUES('current','hero_classification','Public','{"kind":"collectible","owner_id":null}');
                INSERT INTO entities VALUES('current','portrait','Public','{"source_path":"private.atlas"}');
                INSERT INTO entities VALUES('current','hero','Enemy','{"canonical_name":"Enemy","traits":[]}');
                INSERT INTO entities VALUES('current','hero_classification','Enemy','{"kind":"enemy","owner_id":null}');
                INSERT INTO entities VALUES('current','portrait','Enemy','{}');
                INSERT INTO entities VALUES('current','skill','Skill','{"canonical_name":"Skill","components":[],"attributes":{}}');
                INSERT INTO relations VALUES('current','character_skill','Public','Skill',0,'{"kind":"skill","source_record":"private"}');
                INSERT INTO localizations VALUES('current','hero','Public','en','name','Public Hero');
                INSERT INTO localizations VALUES('current','hero','Enemy','en','name','Enemy Hero');
                """)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/prepare-public-database.py"), str(source), str(public), "--game-id", "game"],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual("current", json.loads(result.stdout)["release_id"])
            with sqlite3.connect(f"file:{public}?mode=ro", uri=True) as db:
                self.assertEqual(
                    {"release_info", "catalog_entities", "catalog_text", "catalog_relations"},
                    {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")},
                )
                heroes = db.execute("SELECT entity_id,payload_json FROM catalog_entities WHERE kind='hero'").fetchall()
                self.assertEqual(["Public"], [row[0] for row in heroes])
                self.assertNotIn("raw", json.loads(heroes[0][1]))
                self.assertNotIn("source_path", json.loads(heroes[0][1]))
                relation = json.loads(db.execute("SELECT payload_json FROM catalog_relations").fetchone()[0])
                self.assertNotIn("source_record", relation)


if __name__ == "__main__":
    unittest.main()
