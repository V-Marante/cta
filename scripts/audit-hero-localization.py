#!/usr/bin/env python3
"""Audit displayed English localization and CTA markup tokens for playable heroes."""

from __future__ import annotations

import argparse, json, re, sqlite3
from collections import Counter, defaultdict
from pathlib import Path

KNOWN_ICONS = {"Elt_DA.png", "Elt_LI.png", "Elt_FI.png", "Elt_EA.png", "Elt_WA.png", "HE_Star.png"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("database", type=Path); parser.add_argument("output", type=Path); parser.add_argument("--game-id", default="com.godzilab.idlerpg")
    args = parser.parse_args(); db = sqlite3.connect(args.database)
    run = db.execute("SELECT id FROM import_runs WHERE status='succeeded' AND game_id=? ORDER BY finished_at DESC LIMIT 1", (args.game_id,)).fetchone()
    if not run: raise SystemExit("no successful import found")
    import_id = run[0]
    loc = {(ns, key.lower(), field): value for ns, key, field, value in db.execute("SELECT namespace,entity_key,field,value FROM localizations WHERE import_id=? AND locale='en'", (import_id,))}
    skills = {key.lower(): json.loads(payload) for key, payload in db.execute("SELECT entity_key,payload_json FROM entities WHERE import_id=? AND namespace='skill'", (import_id,))}
    relations = defaultdict(list)
    for hero, skill, payload in db.execute("SELECT source_key,target_key,payload_json FROM relations WHERE import_id=? AND relation='character_skill' ORDER BY source_key,ordinal", (import_id,)):
        if json.loads(payload).get("kind", "skill") == "skill": relations[hero.lower()].append(skill)
    token_counts = Counter(); unknown_icons = Counter(); missing = Counter(); rows = []
    def inspect(text: str) -> None:
        token_counts["emphasis"] += len(re.findall(r"\*[^*]+\*", text)); token_counts["line_break"] += text.count("\n")
        token_counts["printf_format"] += len(re.findall(r"%(?:\.\d+)?[sdf](?:%%)?", text))
        for icon in re.findall(r"\|([^|]+)\|", text):
            token_counts["icon"] += 1
            if icon not in KNOWN_ICONS: unknown_icons[icon] += 1
    heroes = [(key, json.loads(payload)) for key, payload in db.execute("SELECT h.entity_key,h.payload_json FROM entities h JOIN entities c ON c.import_id=h.import_id AND c.namespace='hero_classification' AND c.entity_key=h.entity_key WHERE h.import_id=? AND h.namespace='hero' AND json_extract(c.payload_json,'$.kind')='collectible' ORDER BY h.entity_key", (import_id,))]
    for hero, payload in heroes:
        gaps = []
        if ("hero", hero.lower(), "name") not in loc: gaps.append("hero name uses canonical fallback")
        for code in payload.get("traits", []):
            if text := loc.get(("ability", code.lower(), "description")): inspect(text)
        for skill_id in relations.get(hero.lower(), []):
            skill = skills.get(skill_id.lower(), {}); name = loc.get(("skill", skill_id.lower(), "name")) or skill.get("canonical_name")
            if not name: gaps.append(f"{skill_id}: missing name"); missing["skill_name"] += 1
            text = loc.get(("skill", skill_id.lower(), "description")); info = next((x.get("text") for x in skill.get("components", []) if x.get("kind") == "info"), None)
            if not text: text = loc.get(("skill_description", info[7:].lower(), "description")) if info and info.startswith("SkDesc_") else info
            if not text: gaps.append(f"{skill_id}: description unavailable"); missing["skill_description"] += 1; continue
            inspect(text)
        rows.append((hero, len(relations.get(hero.lower(), [])), "; ".join(gaps) or "None"))
    lines = ["# Hero localization and token audit", "", f"Import: `{import_id}`", f"Playable heroes: **{len(heroes)}**", f"Displayed skill relations: **{sum(x[1] for x in rows)}**", "", "## Token coverage", ""]
    lines += [f"- {key.replace('_', ' ')}: **{value}**" for key, value in sorted(token_counts.items())]
    lines += [f"- Unknown icon references: **{sum(unknown_icons.values())}**", f"- Missing displayed skill descriptions: **{missing['skill_description']}**", f"- Missing displayed skill names: **{missing['skill_name']}**", "", "Known icons render as accessible text; unknown icon and printf-format tokens remain visibly disclosed. Raw localization records and source locations are unchanged.", "", "## Per-hero gaps", "", "| Hero | Skills | Gaps |", "|---|---:|---|"]
    for hero, count, gaps in rows: lines.append(f"| `{hero}` | {count} | {gaps} |")
    lines += [""]
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote localization audit for {len(heroes)} playable heroes to {args.output}"); return 0

if __name__ == "__main__": raise SystemExit(main())
