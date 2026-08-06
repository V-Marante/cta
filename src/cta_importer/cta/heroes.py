from __future__ import annotations

import csv
import re
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


def passive(code: str | None, target: str | None, value: str | None) -> dict:
    code, target = (code or "").strip() or None, (target or "").strip() or None
    amount = scalar(value)
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
            audience = (("All team" if target == "All" else f"{target} heroes") if direction == "Buff"
                        else ("All enemies" if target == "All" else f"{target} enemies"))
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
                diagnostics.append(Diagnostic(Severity.WARNING, "hero_without_id", "ignored hero row without Key", self.descriptor.parser_id, location(artifact, str(ordinal))))
                continue
            raw = {str(k): v for k, v in row.items() if k is not None}
            traits = [value.strip() for name in ("Ability1", "Ability2", "Ability3") if (value := row.get(name)) and value.strip()]
            payload = {
                "source_id": key, "canonical_name": (row.get("Name") or "").strip() or None,
                "class": (row.get("Class") or "").strip() or None, "tribe": (row.get("Tribe") or "").strip() or None,
                "sex": (row.get("Sex") or "").strip() or None, "damage_type": (row.get("Damage Type") or "").strip() or None,
                "element": (row.get("Elemental") or "").strip() or None,
                "mobility": "flying" if flag(row.get("Flying")) else "ground", "traits": traits,
                "passive": passive(row.get("SP4"), row.get("SP4 Target"), row.get("SP4 Value")),
                "progression": {"base_stars": scalar(row.get("BaseStars")), "max_stars": scalar(row.get("MaxStars")),
                    "rarity": scalar(row.get("Rarity")), "factor_per_star": scalar(row.get("Factor per Star")),
                    "rarity_name": _RARITY_NAMES.get(scalar(row.get("Rarity")))},
                "availability": {"dungeon": flag(row.get("Dungeon")), "shop": flag(row.get("Shop")),
                    "event": flag(row.get("Event")), "epic_chest": flag(row.get("ChestEpic"))},
                "stats": {name: scalar(row.get(source)) for name, source in {
                    "attack": "Atk", "health": "HP", "defense": "Def", "attack_range": "AtkRange",
                    "attack_reload": "AtkReload", "move_speed": "MoveSpeed", "critical_chance": "Ctk",
                    "critical_damage": "CtkDmg", "resistance": "Resistance", "evade": "Evade",
                    "power": "POW", "dps": "DPS", "base_stars": "BaseStars", "max_stars": "MaxStars"}.items()},
                "raw": raw,
            }
            source = location(artifact, key)
            entities.append(EntityRecord("hero", key, payload, ordinal, source))
            relations.append(RelationRecord("hero_character", "hero", key, "character", key, ordinal=ordinal, source=source))
        return ParseResult(tuple(entities), tuple(relations), diagnostics=tuple(diagnostics))
