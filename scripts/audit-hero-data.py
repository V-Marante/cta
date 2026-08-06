#!/usr/bin/env python3
"""Generate a Markdown completeness audit for the latest imported hero dataset."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROFILE_FIELDS = {
    "class": "job",
    "element": "element",
    "damage_type": "damage type",
    "sex": "sex",
    "mobility": "ground/flying",
}
STAT_FIELDS = {
    "attack": "ATK",
    "health": "HP",
    "defense": "DEF",
    "dps": "DPS",
    "power": "power",
    "attack_range": "attack range",
    "attack_reload": "attack reload",
    "move_speed": "move speed",
    "critical_chance": "critical chance",
    "critical_damage": "critical damage",
    "resistance": "resistance",
    "evade": "evade",
}
PROGRESSION_FIELDS = {
    "rarity": "rarity",
    "base_stars": "base stars",
    "max_stars": "max stars",
}


def payloads(db: sqlite3.Connection, import_id: str, namespace: str) -> dict[str, dict]:
    return {
        key: json.loads(value)
        for key, value in db.execute(
            "SELECT entity_key, payload_json FROM entities WHERE import_id=? AND namespace=?",
            (import_id, namespace),
        )
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    db = sqlite3.connect(args.database)
    run = db.execute(
        "SELECT id, game_version, finished_at FROM import_runs "
        "WHERE status='succeeded' ORDER BY finished_at DESC LIMIT 1"
    ).fetchone()
    if run is None:
        raise SystemExit("no successful import found")
    import_id, game_version, finished_at = run

    heroes = payloads(db, import_id, "hero")
    classifications = payloads(db, import_id, "hero_classification")
    characters = payloads(db, import_id, "character")
    skills = payloads(db, import_id, "skill")
    collectible_ids = sorted(
        hero_id
        for hero_id in heroes
        if classifications.get(hero_id, {}).get("kind") == "collectible"
    )

    localized_hero_names = {
        key
        for (key,) in db.execute(
            "SELECT entity_key FROM localizations WHERE import_id=? AND namespace='hero' "
            "AND locale='en' AND field='name' AND trim(value)<>''",
            (import_id,),
        )
    }
    localized_skill_names = {
        key
        for (key,) in db.execute(
            "SELECT entity_key FROM localizations WHERE import_id=? AND namespace='skill' "
            "AND locale='en' AND field='name' AND trim(value)<>''",
            (import_id,),
        )
    }
    localized_skill_descriptions = {
        key
        for (key,) in db.execute(
            "SELECT entity_key FROM localizations WHERE import_id=? AND namespace='skill' "
            "AND locale='en' AND field='description' AND trim(value)<>''",
            (import_id,),
        )
    }
    skill_relations: dict[str, list[str]] = defaultdict(list)
    for source, target, relation_payload in db.execute(
        "SELECT source_key, target_key, payload_json FROM relations "
        "WHERE import_id=? AND relation='character_skill' ORDER BY source_key, ordinal",
        (import_id,),
    ):
        if json.loads(relation_payload).get("kind", "skill") == "skill":
            skill_relations[source].append(target)
    acquisitions = Counter(
        source
        for (source,) in db.execute(
            "SELECT source_key FROM relations WHERE import_id=? AND relation='hero_acquisition' "
            "AND coalesce(json_extract(payload_json, '$.current'), 1) <> 0",
            (import_id,),
        )
    )

    count_by_issue: Counter[str] = Counter()
    rows: list[tuple[str, str, str, str, str]] = []
    classification_review: list[str] = []
    complete_except_icon = 0
    for hero_id in collectible_ids:
        hero = heroes[hero_id]
        issues: list[str] = []
        for field, label in PROFILE_FIELDS.items():
            if hero.get(field) in (None, ""):
                issues.append(label)
                count_by_issue[f"Missing {label}"] += 1
        stats = hero.get("stats", {})
        missing_stats = [label for field, label in STAT_FIELDS.items() if stats.get(field) is None]
        if missing_stats:
            issues.append("stats: " + ", ".join(missing_stats))
            for label in missing_stats:
                count_by_issue[f"Missing stat: {label}"] += 1
        progression = hero.get("progression", {})
        missing_progression = [label for field, label in PROGRESSION_FIELDS.items() if progression.get(field) is None]
        if missing_progression:
            issues.append("progression: " + ", ".join(missing_progression))
            for label in missing_progression:
                count_by_issue[f"Missing progression: {label}"] += 1
        if hero_id not in localized_hero_names:
            issues.append("localized name (canonical fallback works)")
            count_by_issue["Missing localized hero name"] += 1
        if not hero.get("traits"):
            issues.append("traits/attributes")
            count_by_issue["No traits/attributes"] += 1
        if not hero.get("passive", {}).get("code"):
            issues.append("fourth passive")
            count_by_issue["Missing fourth passive"] += 1
        legacy_acquisition_count = sum(value is True for value in hero.get("availability", {}).values())
        acquisition_count = acquisitions[hero_id] or legacy_acquisition_count
        if acquisition_count == 0:
            issues.append("acquisition/availability")
            count_by_issue["Missing acquisition/availability"] += 1
            classification_review.append(hero_id)

        character = characters.get(hero_id)
        resolved = skill_relations.get(hero_id, [])
        if character is None:
            issues.append("character/model record")
            count_by_issue["Missing character/model record"] += 1
        if len(resolved) < 3:
            issues.append(f"spells ({len(resolved)}/3 resolved)")
            count_by_issue["Fewer than three resolved spells"] += 1
        missing_skill_names = [skill_id for skill_id in resolved if skill_id not in localized_skill_names and not skills.get(skill_id, {}).get("canonical_name")]
        if missing_skill_names:
            issues.append("spell names: " + ", ".join(missing_skill_names))
            count_by_issue["Missing spell name"] += len(missing_skill_names)
        missing_descriptions = []
        for skill_id in resolved:
            skill = skills.get(skill_id, {})
            inline = any(
                component.get("kind") == "info" and str(component.get("text") or "").strip()
                for component in skill.get("components", [])
            )
            if skill_id not in localized_skill_descriptions and not inline:
                missing_descriptions.append(skill_id)
        if missing_descriptions:
            issues.append("spell descriptions: " + ", ".join(missing_descriptions))
            count_by_issue["Missing spell description"] += len(missing_descriptions)

        if not issues:
            complete_except_icon += 1
        rows.append((
            hero.get("canonical_name") or hero_id,
            hero_id,
            str(len(resolved)),
            str(acquisition_count),
            "; ".join(issues) if issues else "None besides small icon",
        ))

    diagnostics = list(
        db.execute(
            "SELECT severity, code, count(*) FROM diagnostics WHERE import_id=? "
            "GROUP BY severity, code ORDER BY severity, code",
            (import_id,),
        )
    )
    warning_count = sum(count for severity, _, count in diagnostics if severity in {"warning", "error", "fatal"})
    lines = [
        "# Hero import completeness audit",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Latest import: `{import_id}` (game version `{game_version}`, finished `{finished_at}`)",
        "",
        "## Summary",
        "",
        f"- Collectible heroes audited: **{len(collectible_ids)}**",
        f"- Heroes complete except for a static small icon: **{complete_except_icon}**",
        f"- Heroes with one or more additional gaps: **{len(collectible_ids) - complete_except_icon}**",
        f"- Importer warning/error diagnostics: **{warning_count}**",
        f"- Imported static small hero icons: **0/{len(collectible_ids)}**. Suitable 162×162 `GMI_<element>_<index>` frames exist in the APK but are not yet extracted or connected to heroes.",
        f"- Classification review candidates: **{len(classification_review)}** records are marked collectible but have no acquisition or legacy availability source.",
        "",
        "Zero is treated as a present numeric value. Canonical source names are considered usable fallbacks but missing English localization is still reported. Skill descriptions embedded in skill components count as present.",
        "",
        "## Missing-data counts",
        "",
        "| Missing item | Heroes/fields affected |",
        "|---|---:|",
    ]
    lines.extend(f"| {issue} | {count} |" for issue, count in count_by_issue.most_common())
    lines.extend(["", "## Import diagnostics", "", "| Severity | Code | Count |", "|---|---|---:|"])
    lines.extend(f"| {severity} | `{code}` | {count} |" for severity, code, count in diagnostics)
    lines.extend([
        "",
        "## Classification review candidates",
        "",
        "These records are currently classified as collectible but have no normalized acquisition relation and no enabled legacy Dungeon/Shop/Event/Epic Chest flag. Several names resemble enemies or temporary units, so they should be verified before treating the 127-record set as the player roster.",
        "",
        ", ".join(f"`{hero_id}`" for hero_id in classification_review) or "None.",
    ])
    lines.extend([
        "",
        "## Per-hero gaps",
        "",
        "Every hero also lacks an imported static small icon; that repeated item is omitted from individual rows.",
        "",
        "| Hero | Raw ID | Resolved spells | Acquisition sources | Missing data |",
        "|---|---|---:|---:|---|",
    ])
    for name, hero_id, resolved_count, acquisition_count, issues in rows:
        safe = lambda value: value.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {safe(name)} | `{safe(hero_id)}` | {resolved_count} | {acquisition_count} | {safe(issues)} |")
    lines.extend(["", "## Scope notes", "", "- Only records currently classified as `collectible` are included; this classification itself is not assumed to be perfect.", "- Enemy, NPC, summoned, transformed, and cosmetic-variant records already recognized by the importer are excluded.", "- Acquisition counts use normalized relations first, then the API-compatible legacy Dungeon/Shop/Event/Epic Chest flags as fallback.", "- This report audits persisted normalized data, not values visible only in a live player account.", ""])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote audit for {len(collectible_ids)} heroes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
