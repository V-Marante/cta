from __future__ import annotations

import csv
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ..contracts import ParseContext, ParserDescriptor
from ..model import Diagnostic, EntityRecord, ParseResult, RelationRecord, Severity, SourceArtifact
from .common import flag, location, scalar

_PASSIVE_LABELS = {
    "Atk": "ATK", "AtkSpeed": "ATK per second", "AOEDmg": "AoE damage",
    "CriticalDamage": "critical damage", "Def": "DEF", "HP": "HP",
    "Resist": "resistance chance", "Speed": "speed", "Main3": "ATK/HP/DEF",
    "FreezeExplode": "damage from Freeze Explosion", "FreezeDuration": "Freeze duration",
    "BurnDmg": "Burn damage", "BurnDuration": "Burn duration", "PoisonDmg": "Poison damage",
    "NegativeEffectDuration": "negative-effect duration", "DecreaseElementalDamage": "elemental damage reduction",
}
_RARITY_NAMES = {1: "Common", 2: "Rare", 3: "Epic", 4: "Legendary"}
_JOB_NAMES = {"Fighter": "Brawler"}

_STAT_DEFINITIONS = {
    "attack": ("Atk", "ATK", "base_attack_damage", "points", "source_defined"),
    "health": ("HP", "HP", "damage_capacity", "points", "source_defined"),
    "defense": ("Def", "DEF", "incoming_damage_reduction_parameter", "source_units", "source_defined"),
    "attack_range": ("AtkRange", "Attack range", "attack_start_distance", "source_distance_units", "source_defined"),
    "attack_reload": ("AtkReload", "Attack interval", "base_attack_interval", "source_time_units", "strongly_supported"),
    "move_speed": ("MoveSpeed", "Move speed", "base_travel_speed", "source_speed_units", "source_defined"),
    "critical_chance": ("Ctk", "Critical rate", "critical_hit_chance", "percent", "source_defined"),
    "critical_damage": ("CtkDmg", "Critical damage", "extra_critical_hit_damage", "percent", "source_defined"),
    "resistance": ("Resistance", "Effect resistance", "status_effect_resist_chance", "percent", "source_defined"),
    "evade": ("Evade", "Dodge", "incoming_attack_evade_chance", "percent", "source_defined"),
    "power": ("POW", "Raw POW", None, "source_score", "unresolved"),
    "dps": ("DPS", "Derived base DPS", "rounded_attack_divided_by_interval", "damage_per_source_time_unit", "strongly_supported"),
}


def stat_semantics(row: dict[str, str | None]) -> dict:
    facts = {key: {"value": scalar(row.get(field)), "status": status, "source_field": field,
        "label": label, "meaning": meaning, "unit": unit} for key, (field, label, meaning, unit, status) in _STAT_DEFINITIONS.items()}
    for fact in facts.values():
        if fact["value"] is None:
            fact.update(status="unresolved", meaning=None)
    attack, interval, dps = (facts[key]["value"] for key in ("attack", "attack_reload", "dps"))
    if not isinstance(attack, (int, float)) or not isinstance(interval, (int, float)) or interval == 0 or not isinstance(dps, (int, float)) or math.floor(attack / interval + 0.5) != dps:
        facts["dps"].update(status="unresolved", meaning=None)
    return facts


def progression_semantics(base, maximum, rarity) -> dict:
    return {
        "base_stars": {"value": base, "status": "unresolved", "source_field": "BaseStars", "meaning": None},
        "max_stars": {"value": maximum, "status": "strongly_supported" if maximum == 8 else "unresolved",
            "source_field": "MaxStars", "meaning": "hero_evolution_cap" if maximum == 8 else None},
        "rarity": {"value": rarity, "status": "source_defined" if rarity in _RARITY_NAMES else "unresolved",
            "source_field": "Rarity", "meaning": "hero_rarity_tier" if rarity in _RARITY_NAMES else None,
            "name": _RARITY_NAMES.get(rarity)},
    }


def passive(code: str | None, target: str | None, value: str | None) -> dict:
    code, target = (code or "").strip() or None, (target or "").strip() or None
    amount = scalar(value)
    result = {"code": code, "target": target, "source_value": amount, "name": None, "description": None,
        "semantics": {"status": "unresolved", "unit": None, "meaning": None, "target_kind": None}}
    if not code:
        return result
    direction = "Buff" if code.startswith("Buff") else "Debuff" if code.startswith("Debuff") else None
    suffix = code[len(direction):] if direction else code
    label = _PASSIVE_LABELS.get(suffix, re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", suffix))
    result["name"] = f"{direction} {label}" if direction else re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", code)
    if direction and target and amount is not None:
        if code == "BuffNegativeEffectDuration":
            audience = "All enemies" if target == "All" else f"{target} enemies"
        else:
            audience = (("All team" if target == "All" else f"{target} heroes") if direction == "Buff"
                        else ("All enemies" if target == "All" else f"{target} enemies"))
        result["description"] = f"{audience}: {'+' if direction == 'Buff' else '-'}{amount}% {label}"
        result["semantics"] = {"status": "strongly_supported", "unit": "percent", "meaning": "team_stat_modifier",
            "target_kind": "all" if target == "All" else "self" if target == "Self" else "hero_group"}
    return result


class HeroesParser:
    descriptor = ParserDescriptor("cta.heroes", "1.8.0", 4, priority=100)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        return Path(artifact.relative_path).name == "Heroes.csv"

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        entities: list[EntityRecord] = []
        relations: list[RelationRecord] = []
        diagnostics: list[Diagnostic] = []
        character_keys: dict[str, str] = {}
        character_path = context.source_root / "Persos.xml"
        if character_path.exists():
            character_keys = {(node.get("key") or "").lower(): (node.get("key") or "")
                for node in ET.parse(character_path).getroot().findall("character")}
        rows = csv.DictReader(artifact.read_text().splitlines())
        for ordinal, row in enumerate(rows, 1):
            key = (row.get("Key") or "").strip()
            if not key:
                diagnostics.append(Diagnostic(Severity.WARNING, "hero_without_id", "ignored hero row without Key", self.descriptor.parser_id, location(artifact, str(ordinal))))
                continue
            raw = {str(k): v for k, v in row.items() if k is not None}
            traits = [value.strip() for name in ("Ability1", "Ability2", "Ability3") if (value := row.get(name)) and value.strip()]
            source_class = (row.get("Class") or "").strip() or None
            payload = {
                "source_id": key, "canonical_name": (row.get("Name") or "").strip() or None,
                "class": _JOB_NAMES.get(source_class, source_class), "source_class": source_class,
                "tribe": (row.get("Tribe") or "").strip() or None,
                "sex": (row.get("Sex") or "").strip() or None, "damage_type": (row.get("Damage Type") or "").strip() or None,
                "element": (row.get("Elemental") or "").strip() or None,
                "mobility": "flying" if flag(row.get("Flying")) else "ground", "traits": traits,
                "passive": passive(row.get("SP4"), row.get("SP4 Target"), row.get("SP4 Value")),
                "progression": {"base_stars": scalar(row.get("BaseStars")), "max_stars": scalar(row.get("MaxStars")),
                    "rarity": scalar(row.get("Rarity")), "factor_per_star": scalar(row.get("Factor per Star")),
                    "rarity_name": _RARITY_NAMES.get(scalar(row.get("Rarity")))},
                "availability": {"dungeon": flag(row.get("Dungeon")), "shop": flag(row.get("Shop")),
                    "event": flag(row.get("Event")), "epic_chest": flag(row.get("ChestEpic"))},
                "progression_semantics": progression_semantics(scalar(row.get("BaseStars")), scalar(row.get("MaxStars")), scalar(row.get("Rarity"))),
                "legacy_availability": {name: {"value": flag(row.get(source)), "status": "legacy_unverified",
                    "source_field": source, "source_path": artifact.relative_path} for name, source in {
                        "dungeon": "Dungeon", "shop": "Shop", "event": "Event", "epic_chest": "ChestEpic"}.items()},
                "stats": {name: scalar(row.get(source)) for name, source in {
                    "attack": "Atk", "health": "HP", "defense": "Def", "attack_range": "AtkRange",
                    "attack_reload": "AtkReload", "move_speed": "MoveSpeed", "critical_chance": "Ctk",
                    "critical_damage": "CtkDmg", "resistance": "Resistance", "evade": "Evade",
                    "power": "POW", "dps": "DPS", "base_stars": "BaseStars", "max_stars": "MaxStars"}.items()},
                "stat_semantics": stat_semantics(row),
                "source_calculations": {name: {"value": scalar(row.get(source)), "status": "unresolved",
                    "source_field": source, "meaning": None} for name, source in {
                        "attack_with_stars": "Atk w/ stars", "health_with_stars": "HP w/ stars",
                        "power_per_stars": "POW / Stars", "factor_per_star": "Factor per Star"}.items()},
                "raw": raw,
            }
            source = location(artifact, key)
            entities.append(EntityRecord("hero", key, payload, ordinal, source))
            character_id = character_keys.get(key.lower(), key)
            relation_payload = ({"source_target_id": key, "case_normalized": True} if character_id != key else {})
            relations.append(RelationRecord("hero_character", "hero", key, "character", character_id,
                relation_payload, ordinal=ordinal, source=source))
        return ParseResult(tuple(entities), tuple(relations), diagnostics=tuple(diagnostics))
