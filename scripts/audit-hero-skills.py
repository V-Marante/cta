#!/usr/bin/env python3
"""Audit displayed skills, passives, semantic attributes, and localization placeholders."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path); parser.add_argument("output", type=Path)
    parser.add_argument("--game-id", default="com.godzilab.idlerpg")
    args = parser.parse_args(); db = sqlite3.connect(args.database)
    run = db.execute("SELECT id FROM import_runs WHERE status='succeeded' AND game_id=? ORDER BY finished_at DESC LIMIT 1", (args.game_id,)).fetchone()
    if not run: raise SystemExit("no successful import found")
    import_id = run[0]
    entities = {key.lower(): json.loads(payload) for key, payload in db.execute("SELECT entity_key,payload_json FROM entities WHERE import_id=? AND namespace='skill'", (import_id,))}
    localizations = {(ns, key.lower(), field): value for ns, key, field, value in db.execute("SELECT namespace,entity_key,field,value FROM localizations WHERE import_id=? AND locale='en'", (import_id,))}
    relations = defaultdict(list)
    for hero, skill, payload in db.execute("SELECT source_key,target_key,payload_json FROM relations WHERE import_id=? AND relation='character_skill' ORDER BY source_key,ordinal", (import_id,)):
        if json.loads(payload).get("kind", "skill") == "skill": relations[hero.lower()].append(skill)
    heroes = []
    for hero, payload in db.execute("SELECT h.entity_key,h.payload_json FROM entities h JOIN entities c ON c.import_id=h.import_id AND c.namespace='hero_classification' AND c.entity_key=h.entity_key WHERE h.import_id=? AND h.namespace='hero' AND json_extract(c.payload_json,'$.kind')='collectible' ORDER BY h.entity_key", (import_id,)):
        heroes.append((hero, json.loads(payload)))
    placeholder_counts = Counter(); semantic_counts = Counter(); rows = []; total_skills = 0
    missing_descriptions = 0
    for hero, hero_payload in heroes:
        skill_rows = []
        for skill_id in relations.get(hero.lower(), []):
            skill = entities.get(skill_id.lower()); total_skills += 1
            if not skill: skill_rows.append(f"`{skill_id}` missing entity"); continue
            description = localizations.get(("skill", skill_id.lower(), "description"))
            if not description:
                info = next((part.get("text") for part in skill.get("components", []) if part.get("kind") == "info"), None)
                description = localizations.get(("skill_description", info[7:].lower(), "description")) if info and info.startswith("SkDesc_") else info
            if not description: missing_descriptions += 1
            placeholders = sorted(set(re.findall(r"\{([A-Za-z][A-Za-z0-9]*)\}", description or "")))
            components = skill.get("components", [])
            def attrs(kind, name): return [part.get("attributes", {}).get(name) for part in components if part.get("kind") == kind and part.get("attributes", {}).get(name) is not None]
            duration_candidates = set(attrs("effect", "duration") + attrs("spec", "time") + attrs("spec", "effectDuration"))
            effect_value = next(iter(attrs("spec", "effectValue")), None)
            resolvable = {"element"}
            if len(duration_candidates) == 1: resolvable.add("duration")
            if attrs("effect", "duration"): resolvable.add("durationEffect")
            if attrs("spec", "chance"): resolvable.add("chance")
            if attrs("spec", "hpPercent"): resolvable.add("hpPercent")
            if any(part.get("attributes", {}).get("type") == "healthRegen" and part.get("attributes", {}).get("value") is not None for part in components): resolvable.add("healthRegen")
            if any(part.get("attributes", {}).get("type") == "dodge" and part.get("attributes", {}).get("value") is not None for part in components): resolvable.add("dodge")
            if attrs("spec", "count"): resolvable.add("numProjectiles")
            if any(part.get("kind") == "hit" for part in components): resolvable.add("hits")
            if any(part.get("kind") == "effect" and part.get("attributes", {}).get("type") not in (None, "random") for part in components): resolvable.add("effect")
            try:
                if effect_value is not None and 0 <= float(effect_value) <= 1: resolvable.add("effectValue")
            except ValueError: pass
            unresolved = [item for item in placeholders if item not in resolvable]
            placeholder_counts.update(unresolved)
            for component in skill.get("components", []):
                for fact in component.get("attribute_semantics", {}).values(): semantic_counts[fact.get("status", "missing")] += 1
            skill_rows.append(f"`{skill_id}`" + (f" unresolved: {', '.join(unresolved)}" if unresolved else ""))
        passive = hero_payload.get("passive", {}); passive_status = passive.get("semantics", {}).get("status", "missing")
        rows.append((hero, len(skill_rows), passive.get("code"), passive_status, "; ".join(skill_rows) or "—"))
    lines = ["# Hero skill and passive semantics audit", "", f"Import: `{import_id}`", f"Playable heroes: **{len(heroes)}**", f"Displayed skill relations: **{total_skills}**", f"Displayed skills without a description: **{missing_descriptions}**", "", "## Semantic attribute facts", ""]
    lines += [f"- `{status}`: **{count}**" for status, count in sorted(semantic_counts.items())]
    lines += ["", "## Unresolved localization placeholders", ""]
    lines += [f"- `{{{name}}}`: **{count}** occurrences" for name, count in placeholder_counts.most_common()] or ["None."]
    lines += ["", "## Per-hero trace", "", "| Hero | Skills | Passive | Passive status | Skill trace/unresolved placeholders |", "|---|---:|---|---|---|"]
    for hero, count, passive, status, trace in rows: lines.append(f"| `{hero}` | {count} | `{passive or 'none'}` | `{status}` | {trace} |")
    lines += ["", "## Interpretation boundary", "", "- Raw ordered components and original attribute strings remain persisted.", "- Chance fractions and HP fractions are converted to percentages only in their named semantic contexts.", "- Durations/cooldowns are seconds; zero remains a displayed value.", "- Generic effect `value`, boosts, radii, and other internal parameters remain raw unless a concrete context proves their unit.", "- Unknown placeholders are reported and displayed explicitly rather than silently removed.", ""]
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote skill/passive audit for {len(heroes)} playable heroes and {total_skills} displayed skills to {args.output}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
