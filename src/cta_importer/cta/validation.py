from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..model import Diagnostic, ImportDataset, Severity


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
