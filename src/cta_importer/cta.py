from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .contracts import ParseContext, ParserDescriptor
from .model import (
    Diagnostic,
    EntityRecord,
    ImportDataset,
    LocalizationRecord,
    ParseResult,
    RelationRecord,
    Severity,
    SourceArtifact,
    SourceLocation,
)


def _location(artifact: SourceArtifact, record: str) -> SourceLocation:
    return SourceLocation(path=artifact.relative_path, record=record)


def _scalar(value: str | None):
    if value is None or not value.strip():
        return None
    value = value.strip()
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def _flag(value: str | None) -> bool | None:
    if value is None or not value.strip():
        return None
    return value.strip().lower() in {"1", "x", "true", "yes"}


_PASSIVE_LABELS = {
    "Atk": "ATK", "AtkSpeed": "ATK per second", "AOEDmg": "AoE damage",
    "CriticalDamage": "critical damage", "Def": "DEF", "HP": "HP",
    "Resist": "resistance chance", "Speed": "speed", "Main3": "ATK/HP/DEF",
    "FreezeExplode": "damage from Freeze Explosion", "FreezeDuration": "Freeze duration",
    "BurnDmg": "Burn damage", "BurnDuration": "Burn duration", "PoisonDmg": "Poison damage",
    "NegativeEffectDuration": "negative-effect duration", "DecreaseElementalDamage": "elemental damage reduction",
}

_RARITY_NAMES = {1: "Common", 2: "Rare", 3: "Epic", 4: "Legendary"}


def _passive(code: str | None, target: str | None, value: str | None) -> dict:
    code, target = (code or "").strip() or None, (target or "").strip() or None
    amount = _scalar(value)
    result = {"code": code, "target": target, "source_value": amount, "name": None, "description": None}
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
            audience = ("All team" if target == "All" else f"{target} heroes") if direction == "Buff" else ("All enemies" if target == "All" else f"{target} enemies")
        result["description"] = f"{audience}: {'+' if direction == 'Buff' else '-'}{amount}% {label}"
    return result


class HeroesParser:
    descriptor = ParserDescriptor("cta.heroes", "1.3.0", 1, priority=100)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        return Path(artifact.relative_path).name == "Heroes.csv"

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        entities: list[EntityRecord] = []
        relations: list[RelationRecord] = []
        diagnostics: list[Diagnostic] = []
        rows = csv.DictReader(artifact.read_text().splitlines())
        for ordinal, row in enumerate(rows, 1):
            key = (row.get("Key") or "").strip()
            if not key:
                diagnostics.append(Diagnostic(Severity.WARNING, "hero_without_id", "ignored hero row without Key", self.descriptor.parser_id, _location(artifact, str(ordinal))))
                continue
            raw = {str(k): v for k, v in row.items() if k is not None}
            traits = [value.strip() for name in ("Ability1", "Ability2", "Ability3") if (value := row.get(name)) and value.strip()]
            payload = {
                "source_id": key,
                "canonical_name": (row.get("Name") or "").strip() or None,
                "class": (row.get("Class") or "").strip() or None,
                "tribe": (row.get("Tribe") or "").strip() or None,
                "sex": (row.get("Sex") or "").strip() or None,
                "damage_type": (row.get("Damage Type") or "").strip() or None,
                "element": (row.get("Elemental") or "").strip() or None,
                "mobility": "flying" if _flag(row.get("Flying")) else "ground",
                "traits": traits,
                "passive": _passive(row.get("SP4"), row.get("SP4 Target"), row.get("SP4 Value")),
                "progression": {
                    "base_stars": _scalar(row.get("BaseStars")), "max_stars": _scalar(row.get("MaxStars")),
                    "rarity": _scalar(row.get("Rarity")), "factor_per_star": _scalar(row.get("Factor per Star")),
                    "rarity_name": _RARITY_NAMES.get(_scalar(row.get("Rarity"))),
                },
                "availability": {
                    "dungeon": _flag(row.get("Dungeon")), "shop": _flag(row.get("Shop")),
                    "event": _flag(row.get("Event")), "epic_chest": _flag(row.get("ChestEpic")),
                },
                "stats": {name: _scalar(row.get(source)) for name, source in {
                    "attack": "Atk", "health": "HP", "defense": "Def", "attack_range": "AtkRange",
                    "attack_reload": "AtkReload", "move_speed": "MoveSpeed", "critical_chance": "Ctk",
                    "critical_damage": "CtkDmg", "resistance": "Resistance", "evade": "Evade",
                    "power": "POW", "dps": "DPS", "base_stars": "BaseStars", "max_stars": "MaxStars",
                }.items()},
                "raw": raw,
            }
            loc = _location(artifact, key)
            entities.append(EntityRecord("hero", key, payload, ordinal, loc))
            relations.append(RelationRecord("hero_character", "hero", key, "character", key, ordinal=ordinal, source=loc))
        return ParseResult(tuple(entities), tuple(relations), diagnostics=tuple(diagnostics))


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
            loc = _location(artifact, key)
            visible_skills = [str(child.text).strip() for child in node.findall("skill") if child.text and child.text.strip()]
            internal_abilities = [str(child.text).strip() for child in node.findall("ability") if child.text and child.text.strip()]
            payload = {"source_id": key, "attributes": dict(node.attrib), "skill_ids": visible_skills, "ability_ids": internal_abilities}
            entities.append(EntityRecord("character", key, payload, ordinal, loc))
            skin_owner = (node.get("skinOwner") or "").strip()
            if skin_owner:
                entities.append(EntityRecord("hero_variant", key, {
                    "source_id": key, "owner_id": skin_owner, "kind": "cosmetic_variant",
                    "name": node.get("name"), "asset_set": node.get("assets"),
                }, ordinal, loc))
                relations.append(RelationRecord("character_variant_of", "character", key, "hero", skin_owner,
                    {"kind": "cosmetic_variant"}, ordinal, loc))
            for kind, identifiers in (("skill", visible_skills), ("ability", internal_abilities)):
                for skill_ordinal, skill_id in enumerate(identifiers):
                    relations.append(RelationRecord("character_skill", "character", key, "skill", skill_id, {"kind": kind}, skill_ordinal, loc))
            # In CTA the menu portrait is selected by the character's asset set and icon index.
            assets, icon_index = node.get("assets"), node.get("iconIdx")
            if assets or icon_index:
                portrait_key = key
                entities.append(EntityRecord("portrait", portrait_key, {
                    "source_id": portrait_key, "asset_set": assets, "icon_index": _scalar(icon_index),
                    "reference": f"{assets or key}:{icon_index or 'default'}",
                }, ordinal, loc))
                relations.append(RelationRecord("character_portrait", "character", key, "portrait", portrait_key, ordinal=ordinal, source=loc))
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
            loc = _location(artifact, hero_id)
            entities.append(EntityRecord("hero_classification", hero_id, {
                "source_id": hero_id, "kind": kind, "owner_id": owner, "reason": reason,
            }, ordinal, loc))
            if owner:
                relations.append(RelationRecord("hero_variant_of", "hero", hero_id, "hero", owner, {"kind": kind}, ordinal, loc))
        return ParseResult(tuple(entities), tuple(relations))


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
            entities.append(EntityRecord("skill", key, {
                "source_id": key, "canonical_name": node.get("name"), "type": node.get("type"),
                "attributes": dict(node.attrib), "components": children,
            }, ordinal, _location(artifact, key)))
        return ParseResult(entities=tuple(entities))


class EnglishLocalizationParser:
    descriptor = ParserDescriptor("cta.localization.en", "1.3.0", 1, priority=100)
    _pattern = re.compile(r"^(Persos|Skills)_en\.xml$", re.IGNORECASE)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        return bool(self._pattern.match(Path(artifact.relative_path).name)) or Path(artifact.relative_path).name in {"Config_en.xml", "Items_en.xml"}

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        root = ET.fromstring(artifact.read_bytes())
        if Path(artifact.relative_path).name == "Items_en.xml":
            records = []
            for node in root.findall("item"):
                key, name = (node.get("key") or "").strip(), (node.get("name") or "").strip()
                if key.startswith("Chest") and name:
                    records.append(LocalizationRecord("acquisition_source", key, "en", "name", name, _location(artifact, key)))
            return ParseResult(localizations=tuple(records))
        if Path(artifact.relative_path).name == "Config_en.xml":
            records: list[LocalizationRecord] = []
            for group_name, namespace in (("AbilityInfo", "ability"), ("SkDesc", "skill_description")):
                group = root.find(f"./group[@name='{group_name}']")
                if group is None:
                    continue
                for node in group.findall("value"):
                    key, value = (node.get("name") or "").strip(), (node.text or "").strip()
                    if key and value:
                        records.append(LocalizationRecord(namespace, key, "en", "description", value, _location(artifact, f"{group_name}/{key}")))
            for node in root.findall("./value"):
                key, value = (node.get("name") or "").strip(), (node.text or "").strip()
                if key.startswith("SkDesc_") and value:
                    records.append(LocalizationRecord("skill_description", key[7:], "en", "description", value, _location(artifact, key)))
            return ParseResult(localizations=tuple(records))
        namespace = "hero" if Path(artifact.relative_path).name.lower().startswith("persos_") else "skill"
        localizations: list[LocalizationRecord] = []
        for node in list(root):
            key = (node.get("key") or "").strip()
            if not key:
                continue
            loc = _location(artifact, key)
            name = (node.get("name") or "").strip()
            if name:
                localizations.append(LocalizationRecord(namespace, key, "en", "name", name, loc))
            info = node.find("info")
            if info is not None and info.text and info.text.strip():
                localizations.append(LocalizationRecord(namespace, key, "en", "description", info.text.strip(), loc))
        return ParseResult(localizations=tuple(localizations))


class HeroAcquisitionParser:
    descriptor = ParserDescriptor("cta.hero_acquisition", "1.1.0", 1, priority=100)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        return Path(artifact.relative_path).name == "Config.xml"

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        root = ET.fromstring(artifact.read_bytes())
        hero_path = context.source_root / "Heroes.csv"
        hero_ids = set()
        if hero_path.exists():
            hero_ids = {(row.get("Key") or "").strip() for row in csv.DictReader(hero_path.read_text(encoding="utf-8-sig").splitlines())}
        entities: list[EntityRecord] = []
        relations: list[RelationRecord] = []
        for group_ordinal, group in enumerate(root.findall("./group")):
            source_key = (group.get("name") or "").strip()
            if not source_key.startswith("Chest"):
                continue
            loc = _location(artifact, source_key)
            entities.append(EntityRecord("acquisition_source", source_key, {"source_id": source_key, "kind": "chest"}, group_ordinal, loc))
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
                     "count": _scalar(node.get("x")), "weight": _scalar(node.get("y")),
                     "current": source_key != "ChestHeroesPast"}, ordinal, loc))
        return ParseResult(tuple(entities), tuple(relations))


@dataclass(frozen=True, slots=True)
class HeroLibraryValidator:
    validator_id: str = "cta.hero_library"

    def validate(self, dataset: ImportDataset) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []
        heroes = [item for item in dataset.entities if item.namespace == "hero"]
        skills = {item.key for item in dataset.entities if item.namespace == "skill"}
        portraits = {item.key for item in dataset.entities if item.namespace == "portrait"}
        localized = {(item.namespace, item.key, item.field) for item in dataset.localizations if item.locale == "en"}
        for key, count in Counter(item.key for item in heroes).items():
            if count > 1:
                diagnostics.append(Diagnostic(Severity.ERROR, "duplicate_hero_id", f"duplicate hero ID {key} ({count} records)"))
        for hero in heroes:
            if ("hero", hero.key, "name") not in localized:
                diagnostics.append(Diagnostic(Severity.WARNING, "missing_localization_key", f"hero {hero.key} has no English name", location=hero.source))
            if hero.key not in portraits:
                diagnostics.append(Diagnostic(Severity.WARNING, "missing_portrait_reference", f"hero {hero.key} has no portrait reference", location=hero.source))
        for relation in dataset.relations:
            if relation.relation == "character_skill" and relation.target_key not in skills:
                diagnostics.append(Diagnostic(Severity.WARNING, "unresolved_skill_reference", f"skill reference does not resolve: {relation.target_key}", location=relation.source))
            elif relation.relation == "character_skill" and ("skill", relation.target_key, "name") not in localized:
                diagnostics.append(Diagnostic(Severity.WARNING, "missing_localization_key", f"skill {relation.target_key} has no English name", location=relation.source))
        return tuple(diagnostics)


def cta_parsers():
    return (HeroesParser(), CharactersParser(), SkillsParser(), EnglishLocalizationParser(), HeroAcquisitionParser())
