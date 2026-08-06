from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ..contracts import ParseContext, ParserDescriptor
from ..model import EntityRecord, ParseResult, SourceArtifact
from .common import location


class SkillsParser:
    descriptor = ParserDescriptor("cta.skills", "1.0.0", 1, priority=100)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        return Path(artifact.relative_path).name == "Skills.xml"

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        root = ET.fromstring(artifact.read_bytes())
        entities: list[EntityRecord] = []
        for ordinal, node in enumerate(root.findall("skill"), 1):
            key = (node.get("key") or "").strip()
            if not key:
                continue
            children = [{"kind": child.tag, "attributes": dict(child.attrib), "text": (child.text or "").strip() or None} for child in node]
            entities.append(EntityRecord("skill", key, {"source_id": key, "canonical_name": node.get("name"),
                "type": node.get("type"), "attributes": dict(node.attrib), "components": children}, ordinal, location(artifact, key)))
        return ParseResult(entities=tuple(entities))
