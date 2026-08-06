from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ..contracts import ParseContext, ParserDescriptor
from ..model import EntityRecord, ParseResult, SourceArtifact
from .common import location


def attribute_semantics(attributes: dict[str, str]) -> dict[str, dict]:
    result = {}
    for name, raw in attributes.items():
        try:
            value = float(raw) if "." in raw else int(raw)
        except ValueError:
            continue
        status, meaning, unit, display = "unresolved", None, "source_units", value
        if name in {"chance", "effectChance"}:
            status, meaning, unit, display = "strongly_supported", "probability", "percent", value * 100
        elif name in {"cooldown", "duration", "effectDuration", "time", "interval", "delay", "lifetime", "reloadTime"}:
            status, meaning, unit = "strongly_supported", "duration", "seconds"
        elif name == "count":
            status, meaning, unit = "source_defined", "count", "count"
        elif name in {"radius", "splashRad"}:
            status, meaning, unit = "source_defined", "distance", "source_distance_units"
        elif name == "hpPercent":
            status, meaning, unit, display = "strongly_supported", "health_percentage", "percent", value * 100
        result[name] = {"raw_value": raw, "value": value, "display_value": display, "status": status,
            "meaning": meaning, "unit": unit, "source_attribute": name}
    return result


class SkillsParser:
    descriptor = ParserDescriptor("cta.skills", "1.1.0", 2, priority=100)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        return Path(artifact.relative_path).name == "Skills.xml"

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        root = ET.fromstring(artifact.read_bytes())
        entities: list[EntityRecord] = []
        for ordinal, node in enumerate(root.findall("skill"), 1):
            key = (node.get("key") or "").strip()
            if not key:
                continue
            children = [{"kind": child.tag, "attributes": dict(child.attrib),
                "attribute_semantics": attribute_semantics(dict(child.attrib)),
                "text": (child.text or "").strip() or None} for child in node]
            entities.append(EntityRecord("skill", key, {"source_id": key, "canonical_name": node.get("name"),
                "type": node.get("type"), "attributes": dict(node.attrib), "components": children}, ordinal, location(artifact, key)))
        return ParseResult(entities=tuple(entities))
