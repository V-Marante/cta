#!/usr/bin/env python3
"""Project the latest collectible catalogue into a minimal public SQLite DB."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

REMOVED_JSON_KEYS = {
    "raw", "source_path", "source_record", "source_line", "source_column",
    "artifact_path", "source_root",
}

SCHEMA = """
PRAGMA journal_mode=DELETE;
PRAGMA foreign_keys=ON;
CREATE TABLE release_info (
    id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    game_version TEXT NOT NULL,
    finished_at TEXT NOT NULL
);
CREATE TABLE catalog_entities (
    release_id TEXT NOT NULL REFERENCES release_info(id),
    kind TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
    PRIMARY KEY (release_id, kind, entity_id)
);
CREATE TABLE catalog_text (
    release_id TEXT NOT NULL REFERENCES release_info(id),
    kind TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    locale TEXT NOT NULL,
    field TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (release_id, kind, entity_id, locale, field)
);
CREATE TABLE catalog_relations (
    release_id TEXT NOT NULL REFERENCES release_info(id),
    kind TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
    PRIMARY KEY (release_id, kind, source_id, target_id, ordinal)
);
CREATE INDEX ix_catalog_entities_release_kind ON catalog_entities(release_id, kind);
CREATE INDEX ix_catalog_text_lookup ON catalog_text(release_id, kind, locale, field);
CREATE INDEX ix_catalog_relations_source ON catalog_relations(release_id, kind, source_id);
"""


def clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: clean_json(item) for key, item in value.items() if key not in REMOVED_JSON_KEYS}
    if isinstance(value, list):
        return [clean_json(item) for item in value]
    return value


def cleaned(payload: str, *, empty: bool = False) -> str:
    if empty:
        return "{}"
    return json.dumps(clean_json(json.loads(payload)), separators=(",", ":"), ensure_ascii=False)


def placeholders_for_skills(rows: list[tuple[str, str]]) -> set[str]:
    references: set[str] = set()
    for _, payload in rows:
        value = json.loads(payload)
        for component in value.get("components", []):
            text = component.get("text")
            if isinstance(text, str) and text.startswith("SkDesc_"):
                references.add(text[7:])
    return references


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--game-id", default="com.godzilab.idlerpg")
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error(f"source database does not exist: {args.source}")
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    for generated in (args.destination, Path(f"{args.destination}-shm"), Path(f"{args.destination}-wal")):
        if generated.exists():
            generated.unlink()

    source_uri = f"{args.source.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(source_uri, uri=True) as source:
        source.row_factory = sqlite3.Row
        release = source.execute(
            """SELECT id,game_id,game_version,finished_at FROM import_runs
               WHERE status='succeeded' AND game_id=? ORDER BY finished_at DESC LIMIT 1""",
            (args.game_id,),
        ).fetchone()
        if release is None:
            raise SystemExit(f"no successful import exists for game id {args.game_id!r}")
        release_id = release["id"]

        classifications = {
            row["entity_key"]: row["payload_json"]
            for row in source.execute(
                "SELECT entity_key,payload_json FROM entities WHERE import_id=? AND namespace='hero_classification'",
                (release_id,),
            )
        }
        hero_ids = set(classifications)
        if not hero_ids:
            raise SystemExit("latest import contains no classified heroes")

        relation_rows = list(source.execute(
            """SELECT relation,source_key,target_key,ordinal,payload_json FROM relations
               WHERE import_id=? AND relation IN ('character_skill','hero_acquisition')""",
            (release_id,),
        ))
        selected_relations = [row for row in relation_rows if row["source_key"] in hero_ids]
        skill_ids = {row["target_key"] for row in selected_relations if row["relation"] == "character_skill"}
        acquisition_ids = {row["target_key"] for row in selected_relations if row["relation"] == "hero_acquisition"}

        entity_rows: list[tuple[str, str, str]] = []
        for row in source.execute(
            """SELECT namespace,entity_key,payload_json FROM entities WHERE import_id=?
               AND namespace IN ('hero','hero_classification','portrait','skill','acquisition_source')""",
            (release_id,),
        ):
            kind, entity_id = row["namespace"], row["entity_key"]
            include = (
                (kind in {"hero", "hero_classification", "portrait"} and entity_id in hero_ids)
                or (kind == "skill" and entity_id in skill_ids)
                or (kind == "acquisition_source" and entity_id in acquisition_ids)
            )
            if include:
                entity_rows.append((kind, entity_id, cleaned(row["payload_json"], empty=kind == "portrait")))

        selected_skills = [(entity_id, payload) for kind, entity_id, payload in entity_rows if kind == "skill"]
        skill_description_ids = placeholders_for_skills(selected_skills)
        hero_traits: set[str] = set()
        for kind, _, payload in entity_rows:
            if kind == "hero":
                traits = json.loads(payload).get("traits", [])
                hero_traits.update(value for value in traits if isinstance(value, str))

        text_rows: list[tuple[str, str, str, str, str]] = []
        for row in source.execute(
            """SELECT namespace,entity_key,locale,field,value FROM localizations
               WHERE import_id=? AND locale='en'""",
            (release_id,),
        ):
            kind, entity_id, field = row["namespace"], row["entity_key"], row["field"]
            include = (
                (kind == "hero" and entity_id in hero_ids and field == "name")
                or (kind == "skill" and entity_id in skill_ids and field in {"name", "description"})
                or (kind == "skill_description" and entity_id in skill_description_ids and field == "description")
                or (kind == "ability" and entity_id in hero_traits and field == "description")
                or (kind == "acquisition_source" and entity_id in acquisition_ids and field == "name")
            )
            if include:
                text_rows.append((kind, entity_id, row["locale"], field, row["value"]))

        with sqlite3.connect(args.destination) as destination:
            destination.executescript(SCHEMA)
            destination.execute(
                "INSERT INTO release_info VALUES(?,?,?,?)",
                (release["id"], release["game_id"], release["game_version"], release["finished_at"]),
            )
            destination.executemany(
                "INSERT INTO catalog_entities VALUES(?,?,?,?)",
                ((release_id, *row) for row in entity_rows),
            )
            destination.executemany(
                "INSERT INTO catalog_text VALUES(?,?,?,?,?,?)",
                ((release_id, *row) for row in text_rows),
            )
            destination.executemany(
                "INSERT INTO catalog_relations VALUES(?,?,?,?,?,?)",
                ((release_id, row["relation"], row["source_key"], row["target_key"], row["ordinal"], cleaned(row["payload_json"])) for row in selected_relations),
            )
            destination.commit()
            destination.execute("VACUUM")

    args.destination.chmod(0o444)
    print(json.dumps({
        "public_database": str(args.destination), "release_id": release_id,
        "heroes": len(hero_ids), "entities": len(entity_rows),
        "relations": len(selected_relations), "text_entries": len(text_rows),
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
