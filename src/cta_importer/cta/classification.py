from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from ..model import EntityRecord, RelationRecord, SourceArtifact
from .common import flag, location


@dataclass(frozen=True, slots=True)
class Evidence:
    code: str
    weight: int
    value: str | bool | int | None
    source: str

    def payload(self) -> dict:
        return {"code": self.code, "weight": self.weight, "value": self.value, "source": self.source}


# These are deliberately narrow, reviewable exceptions rather than a roster allow/deny list.
# The issue-confirmed rows are module-backed characters whose extracted hero portraits
# already exist but whose source data otherwise resembles an enemy.
_MANUALLY_VERIFIED_COLLECTIBLE = {
    "flybat": "issue-confirmed player-visible hero roster (2026-08-07)",
    "flybotda": "issue-confirmed player-visible hero roster (2026-08-07)",
    "flysprout": "issue-confirmed player-visible hero roster (2026-08-07)",
    "werewolf": "issue-confirmed player-visible hero roster (2026-08-07)",
    "tinydragonfi": "issue-confirmed player-visible hero roster (2026-08-07)",
    "flyeye": "issue-confirmed player-visible hero roster (2026-08-07)",
    "bluefish": "issue-confirmed player-visible hero roster (2026-08-07)",
}


def classify_heroes(
    hero_rows: dict[str, dict[str, str]],
    characters_by_lower: dict[str, ET.Element],
    acquisition_by_lower: dict[str, tuple[str, ...]],
    artifact: SourceArtifact,
):
    entities: list[EntityRecord] = []
    relations: list[RelationRecord] = []
    hero_ids_lower = {key.lower(): key for key in hero_rows}
    for ordinal, (hero_id, row) in enumerate(hero_rows.items()):
        node = characters_by_lower.get(hero_id.lower())
        owner: str | None = None
        evidence: list[Evidence] = []

        character_id = (node.get("key") or "").strip() if node is not None else None
        evidence.append(Evidence("character_record", 1 if node is not None else -3, character_id, "Persos.xml"))
        assets = (node.get("assets") or "").strip() if node is not None else ""
        icon_index = (node.get("iconIdx") or "").strip() if node is not None else ""
        evidence.append(Evidence("character_assets", 1 if assets else -1, assets or None, "Persos.xml@assets"))
        evidence.append(Evidence("icon_index", 2 if icon_index else -2, icon_index or None, "Persos.xml@iconIdx"))

        acquisition = acquisition_by_lower.get(hero_id.lower(), ())
        evidence.append(Evidence("acquisition_membership", 3 if acquisition else -2, len(acquisition), "Config.xml chest groups"))
        availability = [name for name in ("Dungeon", "Shop", "Event", "ChestEpic") if flag(row.get(name))]
        evidence.append(Evidence("availability_flags", 1 if availability else -1, len(availability), "Heroes.csv"))
        visible_skill_count = len(node.findall("skill")) if node is not None else 0
        evidence.append(Evidence("visible_skills", 1 if visible_skill_count >= 3 else 0, visible_skill_count, "Persos.xml"))

        traits = [row.get(name, "").strip() for name in ("Ability1", "Ability2", "Ability3") if row.get(name, "").strip()]
        evidence.append(Evidence("hero_traits", 1 if traits else 0, len(traits), "Heroes.csv"))

        kind: str | None = None
        reason: str | None = None
        if node is not None and node.get("skinOwner") and node.get("skinOwner", "").lower() in hero_ids_lower:
            kind, owner, reason = "cosmetic_variant", hero_ids_lower[node.get("skinOwner", "").lower()], "character skinOwner reference"
            evidence.append(Evidence("skin_owner", 10, owner, "Persos.xml@skinOwner"))
        else:
            for suffix, variant_kind in (("Clone", "summoned_variant"), ("Berserk", "transformed_variant"), ("Wall", "summoned_variant")):
                if hero_id.lower().endswith(suffix.lower()) and hero_id[:-len(suffix)].lower() in hero_ids_lower:
                    kind, owner, reason = variant_kind, hero_ids_lower[hero_id[:-len(suffix)].lower()], f"{suffix.lower()} identifier suffix"
                    evidence.append(Evidence("variant_suffix", 10, suffix, "Heroes.csv@Key"))
                    break

        if kind is None and node is not None and node.find("module") is not None and not assets:
            kind, reason = "enemy", "module-backed character without hero assets"
            evidence.append(Evidence("module_without_assets", -10, True, "Persos.xml"))

        manual_collectible_reason = _MANUALLY_VERIFIED_COLLECTIBLE.get(hero_id.lower())
        if manual_collectible_reason and kind in {None, "enemy"}:
            kind, reason = "collectible", manual_collectible_reason
            evidence.append(Evidence("manual_roster_verification", 10, True, "issue review"))

        no_activity = visible_skill_count == 0 and not traits and not availability and not acquisition
        if kind is None and no_activity:
            kind, reason = "npc", "no skills, traits, acquisition membership, or availability flags"

        score = sum(item.weight for item in evidence)
        if kind is None:
            if score >= 2 and (bool(icon_index) or bool(acquisition)):
                kind, reason = "collectible", "source evidence supports player-roster membership"
            else:
                kind, reason = "uncertain", "insufficient source evidence for collectible classification"
        confidence = "high" if kind in {"cosmetic_variant", "summoned_variant", "transformed_variant", "enemy", "non_collectible"} or score >= 5 else "medium" if score >= 2 else "low"

        source = location(artifact, hero_id)
        entities.append(EntityRecord("hero_classification", hero_id, {
            "source_id": hero_id, "character_id": character_id, "kind": kind, "owner_id": owner,
            "reason": reason, "confidence": confidence, "score": score,
            "evidence": [item.payload() for item in evidence], "acquisition_sources": list(acquisition),
        }, ordinal, source))
        if owner:
            relations.append(RelationRecord("hero_variant_of", "hero", hero_id, "hero", owner, {"kind": kind}, ordinal, source))
    return entities, relations
