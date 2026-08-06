# Project handoff

Last verified: 2026-08-06

## Current state

The hero-library vertical slice is implemented and stabilized across the importer, read-only API, and React frontend. The earlier handoff was obsolete: it reported no CTA parsers and five core tests, while the repository already had five CTA parsers, hero classification and validation, acquisition/localization joins, a hero HTTP API, and roster/detail views.

The generic importer kernel remains responsible for discovery, deterministic import identity, parser selection, validation orchestration, transactions, migrations, and generic persistence. CTA concepts remain in the focused `src/cta_importer/cta/` package.

## Implemented capabilities

### CTA importer

The public `cta_parsers()` registration function returns these descriptors unchanged:

| Parser | Version | Schema | Priority | Accepted source |
|---|---:|---:|---:|---|
| `cta.heroes` | 1.3.0 | 1 | 100 | `Heroes.csv` |
| `cta.characters` | 1.3.0 | 1 | 100 | `Persos.xml` |
| `cta.skills` | 1.0.0 | 1 | 100 | `Skills.xml` |
| `cta.localization.en` | 1.3.0 | 1 | 100 | `Persos_en.xml`, `Skills_en.xml`, `Config_en.xml`, `Items_en.xml` |
| `cta.hero_acquisition` | 1.1.0 | 1 | 100 | `Config.xml` |

Emitted entity namespaces are `hero`, `character`, `hero_variant`, `portrait`, `hero_classification`, `skill`, and `acquisition_source`. Relation namespaces are `hero_character`, `character_variant_of`, `character_skill`, `character_portrait`, `hero_variant_of`, and `hero_acquisition`. Localization namespaces are `hero`, `skill`, `ability`, `skill_description`, and `acquisition_source`, using locale `en` and `name`/`description` fields.

CTA validation emits `duplicate_hero_id` errors and warnings for `missing_localization_key`, `missing_portrait_reference`, and `unresolved_skill_reference`. Generic validation additionally reports duplicate/empty entities and unresolved relation endpoints. Source path/record and raw hero CSV values remain persisted.

### Read-only API

Configuration keys are `Database`, `GameId` (default `com.godzilab.idlerpg`), `HeroIconRoot`, and `WebOrigin`. Every SQLite connection uses `Mode=ReadOnly`. Latest-import selection is scoped to the configured game ID and selects only successful imports.

Endpoints:

- `GET /api/heroes`: paginated summaries; collectible-only by default; case-insensitive name/ID search; class, tribe, element, damage type, rarity, mobility, acquisition, attribute, and classification filters; `includeNonCollectible=true` opt-in.
- `GET /api/heroes/filters`: class, tribe, element, damage-type, rarity, mobility, acquisition, attribute, and classification metadata.
- `GET /api/heroes/{id}`: hero summary plus ordered visible skills.
- `GET /api/heroes/{id}/skills`: ordered visible skills.
- `GET /health`: `{ "status": "ok" }`.
- `/portraits/{id}.png`: served only when a configured local compact icon exists.

Hero responses expose identity and fallback name, class, tribe, element, damage type, sex, mobility, classification/variant owner, traits and formatted descriptions, stats, passive, progression, availability, acquisition sources, canonical name, raw values, optional portrait URL, and resolved skills/components. Localization falls back to canonical names/IDs and inline or `skill_description` records.

### React frontend

The router shell provides roster and `/heroes/{id}` detail views. The roster has the 200 ms search debounce, class/element/rarity/mobility/acquisition/attribute filters, and the variants/NPC toggle. Requests check `response.ok`; failures show retry actions; superseded requests are aborted and guarded against stale updates. Loading, empty, and error states are explicit.

Hero cards and details preserve missing-name data supplied by the API, missing-description text, and full-name missing-portrait placeholders. Detail shows profile fields, acquisition, attributes, stats, skills, mechanics, raw source mechanics, and passive information.

## Repository and data boundaries

Committed code and documentation may include migrations, parsers, validation, API/frontend source, and minimal synthetic tests. `samples/`, `assets/`, and `extracted/` are read-only local inputs and are ignored. Never commit proprietary assets, extracted content, generated SQLite databases, generated reports, logs, or frontend build output. Do not weaken `.gitignore`.

The API is read-only. Tests create synthetic temporary SQLite files outside the repository. Frontend tests mock HTTP responses. This stabilization required no Android or BlueStacks interaction.

## Verified commands

From the repository root, the complete verification command is:

```bash
./scripts/verify.sh
```

Its aligned component commands are:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
dotnet restore api/Cta.Api.Tests/Cta.Api.Tests.csproj
dotnet build api/Cta.Api.Tests/Cta.Api.Tests.csproj --no-restore
dotnet test api/Cta.Api.Tests/Cta.Api.Tests.csproj --no-build --no-restore
npm ci --prefix web/cta-web
npm test --prefix web/cta-web
npm run build --prefix web/cta-web
```

Initialize and inspect parser registration:

```bash
PYTHONPATH=src python3 -m cta_importer init-db extracted/imports.sqlite
PYTHONPATH=src python3 -m cta_importer list-parsers
```

Import locally available content:

```bash
PYTHONPATH=src python3 -m cta_importer import \
  samples/bluestacks/shared-data/cache/content \
  extracted/cta.sqlite \
  --game-id com.godzilab.idlerpg \
  --version 2.0.821
```

Run the API and frontend:

```bash
Database=extracted/cta.sqlite GameId=com.godzilab.idlerpg \
  dotnet run --project api/Cta.Api --urls http://localhost:5080
npm run dev --prefix web/cta-web
```

The setup/import/API commands above were successfully exercised in this repository's existing local workflow; the verification script was executed after stabilization. A clean checkout does not contain the local extracted source or database needed for import/API runtime commands.

## Test coverage

Python tests cover atomic/idempotent imports, version identity, validation rejection, parser exceptions, rollback on persistence failure, the complete synthetic CTA hero slice and provenance, stable parser versions, and duplicate hero rejection.

HTTP API tests cover no import, game-scoped latest selection, ignoring other games, collectible defaults/non-collectible opt-in, case-insensitive search, class/element/rarity/mobility/acquisition/attribute filters, pagination boundaries, missing detail, detail skills and localization fallback, filter metadata, health, and read-only connection configuration.

Frontend tests cover hero cards, loading, empty results, request failure/retry, filter requests, stale-request exclusion, missing portrait fallback, navigation, and detail rendering.

## Known limitations and technical debt

- Classification is heuristic. `Heroes.csv` mixes collectible heroes, variants, enemies, NPCs, summons, and legacy units; evidence/reasons are persisted, but roster accuracy still needs stronger source-backed rules.
- Character/skill/localization identity joins retain known case-sensitivity gaps documented in the root `handoff.md` audit.
- Compact GMI portrait discovery is documented, but atlas decoding/mapping is not implemented; the UI intentionally uses name placeholders.
- Acquisition relations from chest groups and legacy availability flags are presented together by the API fallback without explicit provenance in the DTO.
- English localization is partial. Canonical/ID and unavailable-description fallbacks are intentional.
- Query projection loads the selected import's hero slice and filters in memory. This is simple and adequate for current data size, but is not a scalable query plan.
- The API requires an existing migrated database at startup; an empty hero page means a valid database with no successful configured-game import, not a missing file.
- Only English overlays and the hero-library domain are implemented. Artifacts, runes, team building, auth, and deployment remain out of scope.

## Next recommended milestone: source-backed roster classification

Improve classification accuracy before expanding into another game domain. This should use existing CTA sources/native evidence, retain raw IDs and provenance, and avoid a hand-maintained roster as the primary truth.

Acceptance criteria:

1. Classification rules combine documented positive/negative evidence (character assets/icon index, acquisition membership, availability flags, skin ownership, summon/transformation patterns, and module-backed enemy signals).
2. Every `Heroes.csv` record receives a deterministic classification, confidence/evidence payload, and source provenance.
3. Known case-only hero/character and skill references resolve without changing persisted raw identifiers.
4. `Werewolf` and all records lacking usable icon/acquisition evidence are explicitly covered by synthetic rule tests and a local ignored audit.
5. Default API results include only records supported as collectible; non-collectibles remain available only through the existing opt-in.
6. Classification/filter API tests and frontend toggle tests cover each classification category.
7. Parser descriptor versions are incremented only where emitted semantics change; output schema versions change only if the persisted contract changes.
8. All unified verification steps pass, and no extracted or generated data is staged.
