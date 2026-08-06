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
| `cta.heroes` | 1.5.0 | 1 | 100 | `Heroes.csv` |
| `cta.characters` | 1.5.0 | 1 | 100 | `Persos.xml` |
| `cta.skills` | 1.0.0 | 1 | 100 | `Skills.xml` |
| `cta.localization.en` | 1.3.0 | 1 | 100 | `Persos_en.xml`, `Skills_en.xml`, `Config_en.xml`, `Items_en.xml` |
| `cta.hero_acquisition` | 1.3.1 | 1 | 100 | `Config.xml` |

Emitted entity namespaces are `hero`, `character`, `hero_variant`, `portrait`, `hero_classification`, `skill`, and `acquisition_source`. Relation namespaces are `hero_character`, `character_variant_of`, `character_skill`, `character_portrait`, `hero_variant_of`, and `hero_acquisition`. Localization namespaces are `hero`, `skill`, `ability`, `skill_description`, and `acquisition_source`, using locale `en` and `name`/`description` fields.

CTA validation emits `duplicate_hero_id` errors and warnings for `missing_localization_key`, `missing_portrait_reference`, `missing_compact_portrait_reference`, `invalid_compact_portrait_reference`, and `unresolved_skill_reference`. Generic validation additionally reports duplicate/empty entities and unresolved relation endpoints. Source path/record and raw hero CSV values remain persisted.

The internal `Heroes.csv` class `Fighter` is exposed as the player-facing job `Brawler`; `source_class` retains `Fighter`. The other supported player-facing jobs are Barbarian, Knight, Rogue, Lancer, Samurai, Ranger, Magician, Gunner, and Support. This mapping is supported by English class descriptions, artifact-library labels, and job-relic descriptions in the extracted sources.

Acquisition parsing covers chest groups, Arena/Arena 3v3/Crusade medal shops, and starter packs. Acquisition-source entities carry a normalized kind and display name. Senshi resolves both `Chest Halloween` and `Crusade Shop` from `Config.xml`.

Every hero balance row now receives an evidence-backed classification payload containing `kind`, `confidence`, `score`, `reason`, resolved `character_id`, acquisition sources, and individual weighted evidence entries. Strong variant/enemy/NPC rules take precedence; collectible status requires a minimum evidence score plus either a usable icon index or acquisition membership. Weak no-icon/no-acquisition rows are `uncertain`. `Werewolf` is the sole explicit manual `non_collectible` review result because current files retain strong but stale Halloween evidence despite user confirmation that it is absent from the visible roster.

Hero/character, character/skill, acquisition, validation, and audit joins are case-insensitive. Canonical target IDs are persisted in relations while original differently-cased IDs remain in relation payloads as `source_target_id` or `source_hero_id` with `case_normalized=true`.

### Read-only API

Configuration keys are `Database`, `GameId` (default `com.godzilab.idlerpg`), `HeroIconRoot`, `UiIconRoot`, and `WebOrigin`. Every SQLite connection uses `Mode=ReadOnly`. Latest-import selection is scoped to the configured game ID and selects only successful imports. Existing files under `UiIconRoot` are exposed read-only at `/ui-icons`; the default root is ignored `local/proprietary/ui-icons`.

Endpoints:

- `GET /api/heroes`: paginated collectible summaries; case-insensitive name/ID search; class, tribe, element, damage type, rarity, mobility, acquisition, and attribute filters. Non-playable records cannot be opted in.
- `GET /api/heroes/filters`: collectible-only class, tribe, element, damage-type, rarity, mobility, acquisition, and attribute metadata.
- `GET /api/heroes/{id}`: hero summary plus ordered visible skills.
- `GET /api/heroes/{id}/skills`: ordered visible skills.
- `GET /health`: `{ "status": "ok" }`.
- `/portraits/{id}.png`: served only when a configured local compact icon exists.

Hero responses expose identity and fallback name, class, tribe, element, damage type, sex, mobility, classification/variant owner, traits and formatted descriptions, stats, passive, progression, availability, acquisition sources, canonical name, raw values, optional portrait URL, and resolved skills/components. Localization falls back to canonical names/IDs and inline or `skill_description` records.

### React frontend

The router shell provides roster and `/heroes/{id}` detail views. The roster has the 200 ms search debounce and class/element/rarity/mobility/acquisition/attribute filters. Non-playable records are omitted. Requests check `response.ok`; failures show retry actions; superseded requests are aborted and guarded against stale updates. Loading, empty, and error states are explicit.

Cards use authentic locally extracted CTA portraits, job indicators, and element PNGs. `scripts/extract-cta-ui-icons.py` reads 15 neutral `HE_Job*`/`Elt_*` frames from the RGBA8888 `UI1` PVR v2 atlas. All ten jobs have distinct indicator frames; internal `Fighter` uses the fist-shaped `HE_JobFighter.png` Brawler indicator. The `Rs_HeJob_*` frames in `UIItems0` are awakening resources and are explicitly excluded. `scripts/extract-cta-hero-icons.py` uses pinned optional `texture2ddecoder==1.0.6` to read the two ETC1 `UIGuildMemberIcons` atlases and writes 125 ignored 162×162 portraits; all 116 playable heroes are covered, including the two case-normalized IDs. Both tools validate plist dimensions/frame bounds and write source-hash provenance manifests. Missing local UI icons fall back to accessible text, and missing portraits fall back to the full hero name. Detail labels call the progression fields “Source base stars” and “Source max stars”: among the current 116 collectible records, raw `BaseStars` is 1 for 26, 2 for 1, 3 for 87, and blank for 2; raw `MaxStars` is 8 for all 116. The distribution proves base is not always 1, but the precise player-facing meaning of these design fields remains unconfirmed.

Hero cards and details preserve missing-name data supplied by the API, missing-description text, and full-name missing-portrait placeholders. Detail shows profile fields, acquisition, attributes, stats, skills, mechanics, raw source mechanics, and passive information.

## Repository and data boundaries

Committed code and documentation may include migrations, parsers, validation, API/frontend source, and minimal synthetic tests. `samples/`, `assets/`, and `extracted/` are read-only local inputs and are ignored. Every copied, decoded, converted, or application-ready proprietary asset belongs under ignored `local/proprietary/`; authentic local material is preferred over approximations, while clean-checkout behavior must retain fallbacks. Never commit proprietary assets, extracted content, generated SQLite databases, generated reports, logs, or frontend build output. Do not weaken `.gitignore`.

BlueStacks APKs and its shared runtime cache are the authoritative extraction sources. Reports `01`–`16` are historical Google Play Games investigation records and do not define current blockers. Start report review with `reports/README.md` and `reports/19-bluestacks-reconciliation.md`. On 2026-08-06, the user confirmed BlueStacks offered no update and the launched package still reported `2.0.821` (`versionCode=200821`) through Windows `HD-Adb.exe`; this is the latest version currently obtainable through the installed BlueStacks distribution. Historical Google Play Games logs observed `2.0.822`, which remains cross-distribution provenance rather than the repository source version.

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

Python tests cover atomic/idempotent imports, version identity, validation rejection, parser exceptions, rollback on persistence failure, the complete synthetic CTA hero slice and provenance, stable parser versions, duplicate hero rejection, case-normalized references, evidence payloads, all classification rules, `Werewolf`, and all ten known no-icon/no-acquisition IDs.

HTTP API tests cover no import, game-scoped latest selection, ignoring other games, exclusion of every non-playable classification from list/detail/skills, case-insensitive search, class/element/rarity/mobility/acquisition/attribute filters, pagination boundaries, missing detail, detail skills and localization fallback, collectible-only filter metadata, health, and read-only connection configuration.

Frontend tests cover hero cards, authentic URLs for every job/element icon, missing-icon text fallback, loading, empty results, request failure/retry, filter requests, stale-request exclusion, missing portrait fallback, navigation, and detail rendering. API tests also verify that a synthetic local UI icon is served and cannot be written through HTTP. Python tests cover RGBA8888/RGBA4444 decoding, trimmed-frame placement, PNG output, and atlas-bounds rejection without committing proprietary fixtures.

## Known limitations and technical debt

- Classification is deterministic and evidence-backed but still uses weighted thresholds. Native roster/dex flags could supersede those weights if recovered. `Werewolf` remains an explicit manual exception because the available files contradict current player-visible behavior.
- Compact GMI portrait mapping/extraction is implemented and covers every current playable hero. The 23 unresolved source rows are non-playable/legacy/variant records; `CuddlesBerserk` requests out-of-range `GMI_EA_033` while the retained atlas ends at Earth index 32.
- Acquisition relations from chest groups and legacy availability flags are presented together by the API fallback without explicit provenance in the DTO.
- English localization is partial. Canonical/ID and unavailable-description fallbacks are intentional.
- `BaseStars` and `MaxStars` are preserved source design fields; their distribution is known, but their exact player-facing semantics have not been independently verified.
- Query projection loads the selected import's hero slice and filters in memory. This is simple and adequate for current data size, but is not a scalable query plan.
- The API requires an existing migrated database at startup; an empty hero page means a valid database with no successful configured-game import, not a missing file.
- Only English overlays and the hero-library domain are implemented. Artifacts, runes, team building, auth, and deployment remain out of scope.

## Next recommended milestone: hero progression semantics audit

Establish the player-facing meaning of the remaining ambiguous hero progression and availability fields without adding another game domain. Focus on `BaseStars`, `MaxStars`, rarity, legacy availability flags, and overlapping current/historical acquisition sources.

Acceptance criteria:

1. Every displayed progression/availability field has a source-backed definition or is explicitly labeled as an unresolved raw design field.
2. `BaseStars` and `MaxStars` are traced through configuration, localization, and targeted native/UI references; conclusions distinguish direct evidence from inference.
3. Rarity and acquisition precedence are documented for current versus historical sources, with Senshi and at least one shop-, starter-pack-, and chest-only hero as regression cases.
4. The importer preserves raw values and provenance; any normalized semantic field is additive and versioned.
5. Synthetic tests cover each established rule and ambiguity fallback without embedding extracted content.
6. API/frontend wording reflects only proven semantics and preserves clean-checkout behavior.
7. The audit reports all 116 playable heroes and identifies unresolved exceptions rather than guessing.
8. Unified verification passes and no extracted, generated, proprietary, database, or report output is staged.
