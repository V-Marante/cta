#!/usr/bin/env python3
"""Audit persisted stat semantics for every playable CTA hero."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
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
    rows = []
    statuses = Counter(); nulls = Counter(); zeros = Counter()
    for hero, payload, path, record in db.execute(
        "SELECT h.entity_key,h.payload_json,h.source_path,h.source_record FROM entities h JOIN entities c ON c.import_id=h.import_id AND c.namespace='hero_classification' AND c.entity_key=h.entity_key WHERE h.import_id=? AND h.namespace='hero' AND json_extract(c.payload_json,'$.kind')='collectible' ORDER BY h.entity_key", (import_id,)
    ):
        data = json.loads(payload); facts = data.get("stat_semantics", {}); calculations = data.get("source_calculations", {})
        exceptions = []
        for key, fact in facts.items():
            statuses[(key, fact.get("status", "missing"))] += 1
            if fact.get("value") is None: nulls[key] += 1
            elif fact.get("value") == 0: zeros[key] += 1
            if fact.get("status") == "unresolved": exceptions.append(key)
        for key, fact in calculations.items():
            if fact.get("value") is not None: exceptions.append(key)
        rows.append((hero, facts, calculations, path, record, exceptions))
    keys = sorted({key for _, facts, *_ in rows for key in facts})
    lines = ["# Hero stat semantics audit", "", f"Import: `{import_id}`", f"Playable heroes: **{len(rows)}**", "", "## Coverage", "", "| Fact | Source-defined | Strongly supported | Unresolved | Null | Zero |", "|---|---:|---:|---:|---:|---:|"]
    for key in keys:
        lines.append(f"| `{key}` | {statuses[key, 'source_defined']} | {statuses[key, 'strongly_supported']} | {statuses[key, 'unresolved']} | {nulls[key]} | {zeros[key]} |")
    lines += ["", "## Per-hero trace", "", "| Hero | ATK | HP | DEF | Interval | DPS | Crit rate | Crit damage | Resistance | Dodge | Raw POW | Populated unresolved calculations | Source |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for hero, facts, calculations, path, record, _ in rows:
        value = lambda key: facts.get(key, {}).get("value")
        unresolved = ", ".join(key for key, fact in calculations.items() if fact.get("value") is not None) or "—"
        lines.append(f"| `{hero}` | {value('attack')} | {value('health')} | {value('defense')} | {value('attack_reload')} | {value('dps')} | {value('critical_chance')} | {value('critical_damage')} | {value('resistance')} | {value('evade')} | {value('power')} | {unresolved} | `{path}:{record}` |")
    lines += ["", "## Interpretation boundary", "", "- Zero is a present source value; null is absence and is counted separately.", "- DPS is supported only where it equals rounded `Atk / AtkReload`; mismatches remain unresolved.", "- `POW`, `Atk w/ stars`, `HP w/ stars`, `POW / Stars`, and `Factor per Star` remain raw design/spreadsheet values, not current account totals.", "- Percent units are assigned only to chance/damage fields corroborated by player-facing English text and `%` formatting references.", ""]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote stat audit for {len(rows)} playable heroes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
