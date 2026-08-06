# Hero progression semantics audit

This current follow-up covers CTA 2.0.821 without rewriting historical reports.

| Concept | Conclusion | Evidence grade |
|---|---|---|
| `BaseStars` | Unresolved raw design field; not safely called initial rarity, unlock rank, or awarded stars. | Unresolved |
| `MaxStars` | Hero evolution cap. All 116 playable records contain 8; English and targeted native content refer to 8-star hero evolution. | Strongly supported |
| `Rarity` | Independent source-defined tier: 1 Common, 2 Rare, 3 Epic, 4 Legendary. | Source-defined, English-corroborated |
| Legacy flags | Nullable historical/unverified availability indicators. | Raw evidence |
| Config membership | Explicit chest, shop, or starter-pack acquisition with exact group provenance. `ChestHeroesPast` is historical. | Direct structured evidence |

Starter-pack text grants Luka 3 stars, Kasumi 4, and Hikari 5, while their `BaseStars` values are 2, 3, and 3. Senshi combines `BaseStars=1` with tier 3 (Epic). These contradictions reject both “awarded stars” and rarity-proxy interpretations. No localization or targeted native reference proves another stable player-facing meaning, so the UI says **Raw BaseStars**.

Rarity is never derived from stars, acquisition, or artwork. English offers corroborate Luka (`Rarity=2`, Rare) and Kasumi/Hikari (`Rarity=3`, Epic); Legendary Chest data/text corroborate tier 4.

Current explicit sources are presented first. Historical explicit sources and nullable legacy flags remain visible separately and never create or override relations. Regression cases are Senshi (Halloween Chest and Crusade Shop), Luka (shop/starter pack/chest), Angelica (chest-only), Blossom (current Legendary Chest plus historical chest and legacy overlap), and Kasumi (shop/starter pack/chest overlap).

Reproduce with:

```bash
PYTHONPATH=src python3 -m cta_importer import samples/bluestacks/shared-data/cache/content extracted/cta.sqlite --game-id com.godzilab.idlerpg --version 2.0.821
PYTHONPATH=src python3 scripts/audit-hero-semantics.py extracted/cta.sqlite extracted/hero-semantics-audit.md --game-id com.godzilab.idlerpg
```

The generated report stays ignored. The verified run audited 116 playable heroes; a second identical import reused the new import.
