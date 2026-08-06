# Hero skill and passive semantics audit

This follow-up covers 348 displayed skill relations and fourth-passive fields for all 116 playable heroes in CTA 2.0.821.

Established rules:

- `chance`/`effectChance` probability fractions and `hpPercent` health fractions convert to percentages.
- Cooldown, duration, effect duration, time, interval, delay, lifetime, and reload time use seconds.
- Count is integral; radius values retain internal source-distance units.
- Generic value, effect value, boost, and effect-specific parameters are not globally converted.
- Zero is preserved and displayed.
- Ordered components and original string attributes remain unchanged beside additive `attribute_semantics`.

The API returns the original `descriptionTemplate`, context-resolved `descriptionParameters`, and `unresolvedPlaceholders`. Conflicting duration candidates remain unresolved. The frontend renders unresolved tokens explicitly.

The generated audit found four unresolved `{value}` occurrences, three `{duration}` occurrences with conflicting candidates, and four displayed skills without English/inline descriptions: `FairyKnightShieldSP2`, `TNTbomb`, `ThrowCardSP1`, and `WaterShoot`.

Recognized `Buff*`/`Debuff*` passives with targets and values are strongly supported percentage modifiers. Sixteen playable heroes have no fourth-passive code. Nonstandard codes such as `Frenzy` remain unresolved with raw values intact.

```bash
PYTHONPATH=src python3 scripts/audit-hero-skills.py extracted/cta.sqlite extracted/hero-skill-audit.md --game-id com.godzilab.idlerpg
```

Generated audit output remains ignored.
