# Hero localization and token-rendering closure

This follow-up covers every displayed hero-library name and description for all 116 playable heroes in CTA 2.0.821.

## Missing-description investigation

`FairyKnightShieldSP2`, `TNTbomb`, `ThrowCardSP1`, and `WaterShoot` have names but no description in English or any of the other ten locale files. Their canonical `Skills.xml` records contain mechanics but no inline `info`; targeted native string inspection found resource/name references but no prose. A player-visible description would therefore be newly authored inference, so the application deliberately keeps **Description unavailable.** Raw mechanics remain inspectable.

## Placeholder closure

The four generic `{value}` placeholders are deliberately unresolved because the associated effect types use incompatible scales. The three conflicting `{duration}` placeholders represent base/leveled or effect/spec values; selecting one without player-level context would be misleading. They remain explicit `[unresolved: value]` or `[unresolved: duration]` text with an accompanying disclosure.

## Accessible token rendering

The frontend now tokenizes rather than deletes CTA markup:

- paired `*...*` becomes semantic emphasis;
- known `|Elt_*.png|` and `|HE_Star.png|` references become accessible text labels;
- newlines become line breaks;
- unresolved `{name}` placeholders remain visible;
- printf-style formats such as `%.1f` and `%s` remain visibly marked as unresolved rather than disappearing;
- unknown icon names remain humanized and labeled.

The raw localized strings and persisted source locations are unchanged. Rendering is a frontend projection only.

The real audit found 73 emphasis tokens, 17 known icon references, zero unknown icon references, zero printf-format tokens, and zero newlines in currently displayed descriptions. Synthetic tests cover all supported/fallback token forms.

```bash
PYTHONPATH=src python3 scripts/audit-hero-localization.py extracted/cta.sqlite extracted/hero-localization-audit.md --game-id com.godzilab.idlerpg
```

Generated output remains ignored.
