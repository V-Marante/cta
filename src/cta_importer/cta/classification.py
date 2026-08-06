from __future__ import annotations

import xml.etree.ElementTree as ET

from ..model import EntityRecord, RelationRecord, SourceArtifact
from .common import location


def classify_heroes(hero_rows: dict[str, dict[str, str]], characters_by_lower: dict[str, ET.Element], artifact: SourceArtifact):
    entities: list[EntityRecord] = []
    relations: list[RelationRecord] = []
    hero_ids_lower = {key.lower(): key for key in hero_rows}
    for ordinal, (hero_id, row) in enumerate(hero_rows.items()):
        node = characters_by_lower.get(hero_id.lower())
        kind, owner, reason = "collectible", None, "canonical hero balance record"
        if node is not None and node.get("skinOwner") and node.get("skinOwner", "").lower() in hero_ids_lower:
            kind, owner, reason = "cosmetic_variant", hero_ids_lower[node.get("skinOwner", "").lower()], "character skinOwner reference"
        else:
            for suffix, variant_kind in (("Clone", "summoned_variant"), ("Berserk", "transformed_variant"), ("Wall", "summoned_variant")):
                if hero_id.endswith(suffix) and hero_id[:-len(suffix)].lower() in hero_ids_lower:
                    kind, owner, reason = variant_kind, hero_ids_lower[hero_id[:-len(suffix)].lower()], f"{suffix.lower()} identifier suffix"
                    break
        if kind == "collectible" and node is not None and node.find("module") is not None and not node.get("assets"):
            kind, reason = "enemy", "module-backed character without hero assets"
        visible = node.findall("skill") if node is not None else []
        traits = [row.get(name, "").strip() for name in ("Ability1", "Ability2", "Ability3") if row.get(name, "").strip()]
        flags = [row.get(name, "").strip() for name in ("Dungeon", "Shop", "Event", "ChestEpic")]
        if kind == "collectible" and not visible and not traits and not any(value not in {"", "0"} for value in flags):
            kind, reason = "npc", "no skills, traits, or acquisition flags"
        source = location(artifact, hero_id)
        entities.append(EntityRecord("hero_classification", hero_id, {"source_id": hero_id, "kind": kind,
            "owner_id": owner, "reason": reason}, ordinal, source))
        if owner:
            relations.append(RelationRecord("hero_variant_of", "hero", hero_id, "hero", owner, {"kind": kind}, ordinal, source))
    return entities, relations
