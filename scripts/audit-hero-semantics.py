#!/usr/bin/env python3
"""Audit progression and acquisition semantics for every playable CTA hero."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--game-id", default="com.godzilab.idlerpg")
    args = parser.parse_args()
    db = sqlite3.connect(args.database)
    run = db.execute("SELECT id FROM import_runs WHERE status='succeeded' AND game_id=? ORDER BY finished_at DESC LIMIT 1", (args.game_id,)).fetchone()
    if not run:
        raise SystemExit("no successful import found")
    import_id = run[0]
    acquisitions: dict[str, list[dict]] = {}
    for hero, source, payload, path, record in db.execute(
        "SELECT source_key,target_key,payload_json,source_path,source_record FROM relations WHERE import_id=? AND relation='hero_acquisition' ORDER BY source_key,target_key,ordinal", (import_id,)
    ):
        item = json.loads(payload); item.update(id=source, persisted_source_path=path, persisted_source_record=record)
        acquisitions.setdefault(hero, []).append(item)
    rows = []
    for hero, payload in db.execute(
        "SELECT h.entity_key,h.payload_json FROM entities h JOIN entities c ON c.import_id=h.import_id AND c.namespace='hero_classification' AND c.entity_key=h.entity_key WHERE h.import_id=? AND h.namespace='hero' AND json_extract(c.payload_json,'$.kind')='collectible' ORDER BY h.entity_key", (import_id,)
    ):
        data = json.loads(payload); semantics = data.get("progression_semantics", {}); legacy = data.get("legacy_availability", {})
        explicit = acquisitions.get(hero, [])
        current = [x["id"] for x in explicit if x.get("current", True)]
        historical = [x["id"] for x in explicit if not x.get("current", True)]
        enabled_legacy = [x.get("source_field", key) for key, x in legacy.items() if x.get("value") is True]
        conflict = bool(explicit and enabled_legacy) or bool(current and historical)
        rows.append((hero, semantics, current, historical, enabled_legacy, conflict))
    lines = ["# Hero progression and availability semantics audit", "", f"Import: `{import_id}`", f"Playable heroes: **{len(rows)}**", "", "Status vocabulary: `source_defined`, `strongly_supported`, `unresolved`, and `legacy_unverified`.", "", "| Hero | BaseStars | Base status | MaxStars | Max status | Rarity | Rarity status | Explicit current | Explicit historical | Enabled legacy flags | Overlap/conflict |", "|---|---:|---|---:|---|---|---|---|---|---|---|"]
    for hero, semantics, current, historical, legacy, conflict in rows:
        base, maximum, rarity = (semantics.get(key, {}) for key in ("base_stars", "max_stars", "rarity"))
        cell = lambda values: ", ".join(f"`{x}`" for x in values) or "—"
        lines.append(f"| `{hero}` | {base.get('value', '—')} | `{base.get('status', 'missing')}` | {maximum.get('value', '—')} | `{maximum.get('status', 'missing')}` | {rarity.get('name') or rarity.get('value', '—')} | `{rarity.get('status', 'missing')}` | {cell(current)} | {cell(historical)} | {cell(legacy)} | {'yes' if conflict else 'no'} |")
    unresolved = [hero for hero, semantics, *_ in rows if any(f.get("status") == "unresolved" for f in semantics.values())]
    lines += ["", "## Unresolved exceptions", "", f"Heroes retaining at least one unresolved progression fact: **{len(unresolved)}**.", "", ", ".join(f"`{x}`" for x in unresolved) or "None.", "", "## Provenance", "", "- Progression and legacy fields: `Heroes.csv`, with raw rows retained in each hero payload.", "- Explicit acquisition: `Config.xml` group/value membership; relation payloads and persisted source locations identify the exact group.", "- Explicit configuration is presented first. Historical explicit sources and legacy flags remain visible but never replace or synthesize current sources.", ""]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote semantics audit for {len(rows)} playable heroes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
