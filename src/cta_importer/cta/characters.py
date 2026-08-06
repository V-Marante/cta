from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

from ..contracts import ParseContext, ParserDescriptor
from ..model import EntityRecord, ParseResult, RelationRecord, SourceArtifact
from .acquisitions import acquisition_source
from .classification import classify_heroes
from .common import location, scalar
from .portraits import portrait_reference


class CharactersParser:
    descriptor = ParserDescriptor("cta.characters", "1.5.0", 1, priority=100)

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
        hero_rows_by_lower = {key.lower(): row for key, row in hero_rows.items()}
        characters_by_lower = {(node.get("key") or "").lower(): node for node in root.findall("character")}
        acquisition_by_lower: dict[str, list[str]] = {}
        hero_ids_lower = {key.lower() for key in hero_rows}
        config_path = context.source_root / "Config.xml"
        if config_path.exists():
            config = ET.parse(config_path).getroot()
            for group in config.findall("./group"):
                source_key = (group.get("name") or "").strip()
                if acquisition_source(source_key) is None:
                    continue
                for value in group.findall("value"):
                    item = (value.text or "").strip()
                    hero_id = item[6:] if item.startswith("Medal_") else item
                    if hero_id.lower() in hero_ids_lower:
                        acquisition_by_lower.setdefault(hero_id.lower(), []).append(source_key)
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
            skill_keys = _skill_keys_by_lower(context.source_root)
            for kind, identifiers in (("skill", visible_skills), ("ability", internal_abilities)):
                for skill_ordinal, skill_id in enumerate(identifiers):
                    resolved_id = skill_keys.get(skill_id.lower(), skill_id)
                    payload = {"kind": kind}
                    if resolved_id != skill_id:
                        payload.update({"source_target_id": skill_id, "case_normalized": True})
                    relations.append(RelationRecord("character_skill", "character", key, "skill", resolved_id,
                        payload, skill_ordinal, source))
            assets, icon_index = node.get("assets"), node.get("iconIdx")
            hero_row = hero_rows_by_lower.get(key.lower(), {})
            compact = portrait_reference(hero_row.get("Elemental"), icon_index)
            if assets or icon_index:
                payload = {"source_id": key, "asset_set": assets, "element": hero_row.get("Elemental"),
                    "icon_index": scalar(icon_index), "reference": f"{assets or key}:{icon_index or 'default'}"}
                if compact is not None:
                    payload.update({"element_code": compact.element_code, "frame_name": compact.frame_name,
                        "atlas": compact.atlas_name, "plist_entry": compact.plist_entry, "texture_entry": compact.texture_entry})
                entities.append(EntityRecord("portrait", key, payload, ordinal, source))
                relations.append(RelationRecord("character_portrait", "character", key, "portrait", key, ordinal=ordinal, source=source))
        classified_entities, classified_relations = classify_heroes(
            hero_rows, characters_by_lower, {key: tuple(value) for key, value in acquisition_by_lower.items()}, artifact
        )
        return ParseResult(tuple((*entities, *classified_entities)), tuple((*relations, *classified_relations)))


def _skill_keys_by_lower(source_root: Path) -> dict[str, str]:
    path = source_root / "Skills.xml"
    if not path.exists():
        return {}
    return {(node.get("key") or "").lower(): (node.get("key") or "") for node in ET.parse(path).getroot().findall("skill")}
