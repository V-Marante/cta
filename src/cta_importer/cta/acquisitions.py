from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ..contracts import ParseContext, ParserDescriptor
from ..model import EntityRecord, ParseResult, RelationRecord, SourceArtifact
from .common import location, scalar


def acquisition_source(source_key: str) -> tuple[str, str] | None:
    if source_key.startswith("Chest"):
        return "chest", _source_name(source_key.removeprefix("Chest"))
    if source_key.endswith("_Shop_Medals"):
        return "shop", _source_name(source_key.removesuffix("_Medals"))
    if source_key.startswith("StarterPack_"):
        return "starter_pack", _source_name(source_key)
    return None


def _source_name(value: str) -> str:
    names = {
        "HLW": "Chest Halloween", "EAS": "Easter Chest", "LNY": "Lunar New Year Chest",
        "XMas": "Christmas Chest", "Arena_Shop": "Arena Shop", "Arena3vs3_Shop": "Arena 3v3 Shop",
        "Crusade_Shop": "Crusade Shop",
    }
    if value in names:
        return names[value]
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value).replace("_", " ").strip()


class HeroAcquisitionParser:
    descriptor = ParserDescriptor("cta.hero_acquisition", "1.4.0", 2, priority=100)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        return Path(artifact.relative_path).name == "Config.xml"

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        root = ET.fromstring(artifact.read_bytes())
        hero_path = context.source_root / "Heroes.csv"
        hero_ids = ({(row.get("Key") or "").strip() for row in csv.DictReader(hero_path.read_text(encoding="utf-8-sig").splitlines())}
                    if hero_path.exists() else set())
        heroes_by_lower = {key.lower(): key for key in hero_ids}
        entities: list[EntityRecord] = []
        relations: list[RelationRecord] = []
        for group_ordinal, group in enumerate(root.findall("./group")):
            source_key = (group.get("name") or "").strip()
            source = acquisition_source(source_key)
            if source is None:
                continue
            source_kind, source_name = source
            source_location = location(artifact, source_key)
            entities.append(EntityRecord("acquisition_source", source_key, {
                "source_id": source_key, "kind": source_kind, "name": source_name,
            }, group_ordinal, source_location))
            for ordinal, node in enumerate(group.findall("value")):
                item = (node.text or "").strip()
                if item.startswith("Medal_"):
                    source_hero_id, reference_style = item[6:], "medal"
                elif item.lower() in heroes_by_lower:
                    source_hero_id, reference_style = item, "hero"
                else:
                    continue
                hero_id = heroes_by_lower.get(source_hero_id.lower(), source_hero_id)
                payload = {"medal_id": item if reference_style == "medal" else f"Medal_{hero_id}",
                    "reference_style": reference_style, "count": scalar(node.get("x")), "weight": scalar(node.get("y")),
                    "current": source_key != "ChestHeroesPast", "evidence_type": "explicit_configuration",
                    "status": "historical" if source_key == "ChestHeroesPast" else "current",
                    "source_path": artifact.relative_path, "source_record": source_key}
                if hero_id != source_hero_id:
                    payload.update({"source_hero_id": source_hero_id, "case_normalized": True})
                relations.append(RelationRecord("hero_acquisition", "hero", hero_id, "acquisition_source", source_key,
                    payload, ordinal, source_location))
        return ParseResult(tuple(entities), tuple(relations))
