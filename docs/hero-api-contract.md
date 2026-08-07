# Hero API contract

Current contract: CTA hero-library API, 2026-08-07. The API is read-only and exposes all classified source records by default. Use `classification=collectible` for the confirmed playable roster used by team-building tools.

## Endpoints

| Method and path | Success body | Other result |
|---|---|---|
| `GET /health` | `{ "status": "ok" }` | — |
| `GET /api/heroes` | `HeroPage` | — |
| `GET /api/heroes/filters` | `HeroFilters` | — |
| `GET /api/heroes/{id}` | `HeroDetail` | `404` |
| `GET /api/heroes/{id}/skills` | `Skill[]` | `404` |

The list accepts `search`, `class`, `tribe`, `element`, `damageType`, `rarity`, `mobility`, `acquisition`, `attribute`, `classification`, `page`, and `pageSize`. Text matching is case-insensitive. `classification` matches values such as `collectible`, `uncertain`, `enemy`, `npc`, and variant classifications. The default is all classifications. `page` is clamped to at least 1 and `pageSize` to 1–250. The obsolete `includeNonCollectible` parameter has no effect.

## Response shapes

`HeroPage` is `{ items: Hero[], total: integer, page: integer, pageSize: integer }`. `HeroDetail` is `{ hero: Hero, skills: Skill[] }`.

`Hero` contains:

| Field | Shape and contract |
|---|---|
| `id`, `name` | non-null strings |
| `class`, `tribe`, `element`, `damageType`, `sex`, `mobility` | nullable strings |
| `traits` | `{ code, name, description? }[]` |
| `portraitUrl` | local relative URL or null; never an extracted filesystem path |
| `stats` | source-faithful scalar object |
| `statSemantics` | facts keyed by stat; each carries `value`, `label`, `unit`, `status`, `meaning`, and `source_field` |
| `sourceCalculations` | unresolved source calculation facts; not gameplay totals |
| `passive` | source-faithful passive object plus additive semantic fields when supported |
| `progression` | raw `base_stars`, `max_stars`, `rarity`, `rarity_name`, and `factor_per_star` |
| `progressionSemantics` | qualified facts for progression fields; unresolved meanings remain explicit |
| `availability` | backward-compatible nullable raw flag values |
| `legacyAvailability` | provenance-bearing nullable `legacy_unverified` facts |
| `acquisition` | explicit current/historical configuration relations with evidence and provenance |
| `classification` | source classification (`collectible`, `uncertain`, `enemy`, `npc`, or variant) |
| `classificationConfidence`, `classificationScore`, `classificationReason` | evidence summary; score is an internal tally, not a probability |
| `variantOf`, `canonicalName` | nullable source identity fields |
| `raw` | original `Heroes.csv` values |

`Skill` contains `id`, `name`, nullable `description`, nullable `descriptionTemplate`, `descriptionParameters`, `unresolvedPlaceholders`, nullable `type`, ordered `components`, and `raw`. Components preserve source attributes and may contain additive `attribute_semantics` facts.

`HeroFilters` contains string arrays `classes`, `tribes`, `elements`, `damageTypes`, `rarities`, `mobilities`, `acquisitions`, and `classifications`, plus `attributes: { value, label }[]`. Values describe all source records in the selected import.

## Compatibility and evidence rules

Top-level DTO properties use ASP.NET Core camelCase. Nested imported semantic/source objects deliberately retain their persisted snake_case keys; changing them would break provenance and existing consumers. Additive evidence objects do not replace `raw`, `availability`, progression, component attributes, or description templates.

Explicit current acquisition is the presentation authority. Historical explicit relations and nullable legacy flags remain separate and never silently override it. A null is not false. `BaseStars`, POW, factor-per-star, and documented localization placeholders retain qualified unresolved status. See reports 20–24 for the evidence and known exceptions.

The application caches mapped heroes per immutable import ID and skills per import/hero pair. A new successful import has a new ID and therefore cannot reuse the prior projection.
