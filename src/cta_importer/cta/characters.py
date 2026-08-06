from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

from ..contracts import ParseContext, ParserDescriptor
from ..model import EntityRecord, ParseResult, RelationRecord, SourceArtifact
from .classification import classify_heroes
from .common import location, scalar


class CharactersParser:
    descriptor = ParserDescriptor("cta.characters", "1.3.0", 1, priority=100)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        return Path(artifact.relative_path).name == "Persos.xml"

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        root = ET.fromstring(artifact.read_bytes())
        entities: list[EntityRecord] = []
        relations: list[RelationRecord] = []
        hero_rows: dict[str, dict[str, str]] = {}
        hero_path = context.source_root / "Heroes.csv"
        if hero_path.exists():
            hero_rows = {(row.get("Key") or "").strip(): row for row in csv.DictReader(hero_path.read_text(encoding="utf-8-sig").splitlines())}
        characters_by_lower = {(node.get("key") or "").lower(): node for node in root.findall("character")}
        for ordinal, node in enumerate(root.findall("character"), 1):
            key = (node.get("key") or "").strip()
            if not key:
                continue
            source = location(artifact, key)
            visible_skills = [str(child.text).strip() for child in node.findall("skill") if child.text and child.text.strip()]
            internal_abilities = [str(child.text).strip() for child in node.findall("ability") if child.text and child.text.strip()]
            entities.append(EntityRecord("character", key, {"source_id": key, "attributes": dict(node.attrib),
                "skill_ids": visible_skills, "ability_ids": internal_abilities}, ordinal, source))
            skin_owner = (node.get("skinOwner") or "").strip()
            if skin_owner:
                entities.append(EntityRecord("hero_variant", key, {"source_id": key, "owner_id": skin_owner,
                    "kind": "cosmetic_variant", "name": node.get("name"), "asset_set": node.get("assets")}, ordinal, source))
                relations.append(RelationRecord("character_variant_of", "character", key, "hero", skin_owner,
                    {"kind": "cosmetic_variant"}, ordinal, source))
            for kind, identifiers in (("skill", visible_skills), ("ability", internal_abilities)):
                for skill_ordinal, skill_id in enumerate(identifiers):
                    relations.append(RelationRecord("character_skill", "character", key, "skill", skill_id,
                        {"kind": kind}, skill_ordinal, source))
            assets, icon_index = node.get("assets"), node.get("iconIdx")
            if assets or icon_index:
                entities.append(EntityRecord("portrait", key, {"source_id": key, "asset_set": assets,
                    "icon_index": scalar(icon_index), "reference": f"{assets or key}:{icon_index or 'default'}"}, ordinal, source))
                relations.append(RelationRecord("character_portrait", "character", key, "portrait", key, ordinal=ordinal, source=source))
        classified_entities, classified_relations = classify_heroes(hero_rows, characters_by_lower, artifact)
        return ParseResult(tuple((*entities, *classified_entities)), tuple((*relations, *classified_relations)))
