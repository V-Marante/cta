from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

from ..contracts import ParseContext, ParserDescriptor
from ..model import EntityRecord, ParseResult, RelationRecord, SourceArtifact
from .common import location, scalar


class HeroAcquisitionParser:
    descriptor = ParserDescriptor("cta.hero_acquisition", "1.1.0", 1, priority=100)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        return Path(artifact.relative_path).name == "Config.xml"

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        root = ET.fromstring(artifact.read_bytes())
        hero_path = context.source_root / "Heroes.csv"
        hero_ids = ({(row.get("Key") or "").strip() for row in csv.DictReader(hero_path.read_text(encoding="utf-8-sig").splitlines())}
                    if hero_path.exists() else set())
        entities: list[EntityRecord] = []
        relations: list[RelationRecord] = []
        for group_ordinal, group in enumerate(root.findall("./group")):
            source_key = (group.get("name") or "").strip()
            if not source_key.startswith("Chest"):
                continue
            source = location(artifact, source_key)
            entities.append(EntityRecord("acquisition_source", source_key, {"source_id": source_key, "kind": "chest"}, group_ordinal, source))
            for ordinal, node in enumerate(group.findall("value")):
                item = (node.text or "").strip()
                if item.startswith("Medal_"):
                    hero_id, reference_style = item[6:], "medal"
                elif item in hero_ids:
                    hero_id, reference_style = item, "hero"
                else:
                    continue
                relations.append(RelationRecord("hero_acquisition", "hero", hero_id, "acquisition_source", source_key,
                    {"medal_id": item if reference_style == "medal" else f"Medal_{hero_id}", "reference_style": reference_style,
                     "count": scalar(node.get("x")), "weight": scalar(node.get("y")), "current": source_key != "ChestHeroesPast"},
                    ordinal, source))
        return ParseResult(tuple(entities), tuple(relations))
