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
| `cta.heroes` | 1.8.0 | 4 | 100 | `Heroes.csv` |
| `cta.characters` | 1.5.0 | 1 | 100 | `Persos.xml` |
| `cta.skills` | 1.1.0 | 2 | 100 | `Skills.xml` |
| `cta.localization.en` | 1.3.0 | 1 | 100 | `Persos_en.xml`, `Skills_en.xml`, `Config_en.xml`, `Items_en.xml` |
| `cta.hero_acquisition` | 1.4.0 | 2 | 100 | `Config.xml` |

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
- Vite proxies `/api`, health endpoints, and `/assets` to the local API. Production serves the compiled SPA, API, and versioned assets from one Fly origin.
- `GET /health`: `{ "status": "ok" }`.
- `/portraits/{id}.png`: served only when a configured local compact icon exists.

Hero responses expose raw progression plus semantic status, source-faithful stats plus `statSemantics`, unresolved spreadsheet values under `sourceCalculations`, passive semantic status, backward-compatible raw availability, nullable legacy availability evidence, and provenance-bearing acquisition. Skill DTOs expose original description templates, resolved parameters, unresolved placeholders, ordered raw components, and additive attribute semantics.

`docs/hero-api-contract.md` records the stable query and DTO shapes, compatibility rules, null behavior, and nested camelCase/snake_case boundary. Minimal-API metadata names every operation and declares success/404 response types. The singleton repository caches mapped heroes by immutable import ID and skills by import/hero, so list, filter, and detail requests no longer repeat the same database projection; a new import necessarily uses a new cache key.

### React frontend

The router shell provides roster and `/heroes/{id}` detail views. The roster has the 200 ms search debounce and class/element/rarity/mobility/acquisition/attribute filters. Non-playable records are omitted. Requests check `response.ok`; failures show retry actions; superseded requests are aborted and guarded against stale updates. Loading, empty, and error states are explicit.

The `/team-planner` route is a compact client-only team composition tool. `TeamPlannerPage` owns hero loading/filter UI; `useTeamPlanner` owns the independent ten-entry `(string | null)[]` slot state; `TeamSlotGrid`, `PlannerHeroLibrary`, `PlannerHeroCard`, and `TeamSummary` keep rendering responsibilities focused. Native portrait buttons toggle a hero from either the grouped available pool or selected slots, so pointer and keyboard behavior share one simple interaction with no drag-and-drop dependency. Available heroes can be grouped by player-facing job, element, or exact fourth-ability name/code while name, element, and job filters remain independent.

Persistence uses only stable IDs in `cta.team-planner.v1`. Restoration occurs after the collectible list loads and retains selection positions while removing malformed values, duplicates, and IDs absent from the selected latest import. Clear removes both state and storage. Reordering is intentionally not exposed in the compact UI. This deliberately remains distinct from API fetching and has no write endpoint.

Planner fourth abilities reuse the existing hero-summary `passive` projection; no planner endpoint or schema migration was added. The importer sources `code`, `target`, and `source_value` from `Heroes.csv` `SP4`, `SP4 Target`, and `SP4 Value`. Fourth-ability groups use only the generic ability name/code. Within each hero card and the selected-team ability section, `All` stays text, known elemental targets use authentic element icons, and other targets retain their exact source text. The compact card also exposes imported trait names (such as Anti-Stun or Stunner) and adds Flying only from the explicit mobility field. `name`, `description`, and `semantics` remain nullable/source-confidence-aware; unknown or incomplete records remain unresolved. The UI does not parse display prose or infer stacking/synergy.

Logical future extensions include saved named team collections or shareable representations, server persistence behind a separate write model, and richer passive grouping if future extraction provides explicit relationships. Do not add combat simulation, recommendations, or synergy claims without new reliable structured source semantics.

Cards use authentic locally extracted CTA portraits, job indicators, and element PNGs. `scripts/extract-cta-ui-icons.py` reads 15 neutral `HE_Job*`/`Elt_*` frames from the RGBA8888 `UI1` PVR v2 atlas. All ten jobs have distinct indicator frames; internal `Fighter` uses the fist-shaped `HE_JobFighter.png` Brawler indicator. The `Rs_HeJob_*` frames in `UIItems0` are awakening resources and are explicitly excluded. `scripts/extract-cta-hero-icons.py` uses pinned optional `texture2ddecoder==1.0.6` to read the two ETC1 `UIGuildMemberIcons` atlases and writes 125 ignored 162×162 portraits; all 116 playable heroes are covered, including the two case-normalized IDs. Both tools validate plist dimensions/frame bounds and write source-hash provenance manifests. Missing local UI icons fall back to accessible text, and missing portraits fall back to the full hero name. Detail uses “Raw BaseStars” because its player-facing meaning remains unresolved, “Supported evolution cap” for strongly supported `MaxStars`, and the independently source-defined rarity name. Report 20 records the evidence and rejected interpretations.

Hero cards and details preserve missing-name data supplied by the API, missing-description text, and full-name missing-portrait placeholders. Detail shows profile fields, acquisition, attributes, evidence-backed base combat values, skills, mechanics, raw source mechanics, and passive information. Percent facts render with `%`, including zero. Unresolved raw POW is disclosed separately; sparse star/editor calculations are retained by the API but not presented as gameplay totals. The old inaccurate “Masteries” heading is gone.

Release-readiness accessibility changes provide named filter/roster regions, a labeled search input, status announcements for loading/empty results, alert/retry semantics, route-title focus, visible focus indicators, and reduced-motion behavior. Static recurring color pairs exceed WCAG AA normal-text contrast. Responsive behavior supports the 320 px minimum and the existing mobile detail/control layout. Report 24 records the review boundaries and measurements.

The `/tier-list` route is a compact client-only portrait ranking tool over all collectible heroes. It starts with one `S` tier. Users can create up to 15 tiers, rename them, and reorder them with accessible up/down controls; a fixed unique positional palette assigns red to the first, blue to the second, and deterministic colors thereafter, with no color picker. Every hero tile uses a small portrait above a full-name box. The scrollable Available pool remains sticky near the viewport bottom for small-screen drag/drop. Heroes are placed and moved only by drag-and-drop; clicking a ranked portrait returns it directly to Available. Deleting a tier also returns its heroes to Available; reset returns to one empty S tier. Development mode exposes random fill across current tiers. Ranked tiers export to a lossless 1400 px PNG using the same portrait/name layout. The exporter attempts authentic images first and draws the full hero name in the portrait area—not initials—if an image cannot load. Tier definitions and assignments use validated version-2 browser `localStorage`; corrupt or older drafts fall back safely to the new default. The tool has no API write path.

## Repository and data boundaries

Committed code and documentation may include migrations, parsers, validation, API/frontend source, and minimal synthetic tests. `samples/`, `assets/`, and `extracted/` are read-only local inputs and are ignored. Every copied, decoded, converted, or application-ready proprietary asset belongs under ignored `local/proprietary/`; authentic local material is preferred over approximations, while clean-checkout behavior must retain fallbacks. Never commit proprietary assets, extracted content, generated SQLite databases, generated reports, logs, or frontend build output. Do not weaken `.gitignore`.

BlueStacks APKs and its shared runtime cache are the authoritative extraction sources. Reports `01`–`16` are historical Google Play Games investigation records and do not define current blockers. Start with `reports/README.md`, report 19, and the current source reconciliation in report 25. On 2026-08-06, the installed launched package and current public Google Play metadata agreed on `2.0.821` (`versionCode=200821`). Historical Google Play Games logs contain an uncorroborated `2.0.822` value; preserve it as raw history, not as evidence of a newer public release.

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
./scripts/prepare-public-release.sh extracted/cta.sqlite
Database=artifacts/public/cta.sqlite GameId=com.godzilab.idlerpg \
  dotnet run --project api/Cta.Api --urls http://localhost:5080
npm run dev --prefix web/cta-web
```

The setup/import/API commands above were successfully exercised in this repository's existing local workflow; the verification script was executed after stabilization. A clean checkout does not contain the local extracted source or database needed for import/API runtime commands.

## Test coverage

Python tests cover atomic/idempotent imports, version identity, validation rejection, parser exceptions, rollback on persistence failure, the complete synthetic CTA hero slice and provenance, stable parser versions, duplicate hero rejection, case-normalized references, evidence payloads, all classification rules, `Werewolf`, all ten known no-icon/no-acquisition IDs, and synthetic APK/listing/patch/canonical-source reconciliation.

HTTP API tests cover no import, game-scoped latest selection, ignoring other games, cache rollover to a newly selected import, exclusion of every non-playable classification from list/detail/skills, case-insensitive search, class/element/rarity/mobility/acquisition/attribute filters, pagination boundaries, missing detail, detail skills and localization fallback, collectible-only filter metadata, health, and read-only connection configuration.

Frontend tests cover hero cards, authentic URLs for every job/element icon, missing-icon text fallback, loading and announced empty results, named filter/roster/search controls, request failure/retry, filter requests, stale-request exclusion, missing portrait fallback, navigation, detail rendering, detail-title focus, tier-list routing, one-tier default, compact portrait/name cards and Available pool, drag/drop portrait placement, click-to-Available removal, deterministic unique colors, rename/persistence, tier reordering, delete-to-Available behavior, development random fill, export wiring, and real PNG canvas/full-name fallback output. API tests also verify that a synthetic local UI icon is served and cannot be written through HTTP. Python tests cover RGBA8888/RGBA4444 decoding, trimmed-frame placement, PNG output, and atlas-bounds rejection without committing proprietary fixtures.

## Known limitations and technical debt

- Classification is deterministic and evidence-backed but still uses weighted thresholds. Native roster/dex flags could supersede those weights if recovered. `Werewolf` remains an explicit manual exception because the available files contradict current player-visible behavior.
- Compact GMI portrait mapping/extraction is implemented and covers every current playable hero. The 23 unresolved source rows are non-playable/legacy/variant records; `CuddlesBerserk` requests out-of-range `GMI_EA_033` while the retained atlas ends at Earth index 32.
- Explicit acquisition and nullable legacy availability are separate API evidence lanes. The remaining limitation is that legacy flag meanings/freshness are not proven.
- English localization is partial. Canonical/ID and unavailable-description fallbacks are intentional.
- `BaseStars` remains an explicitly unresolved raw design field. `MaxStars` is strongly supported as the evolution cap, and `Rarity` is a source-defined independent tier. See report 20.
- `POW` and the star/spreadsheet calculation columns remain intentionally unresolved raw scores. Defense/range/reload/speed meanings are established, but their underlying internal physical units and formulas are not invented. See report 21.
- Seven displayed localization placeholders remain intentionally unresolved, and four displayed skills have no available English/inline description. See report 22.
- All eleven locale files and targeted native strings were checked for those four skills; none supplies prose. The frontend preserves CTA emphasis, icon, newline, placeholder, and numeric-format tokens accessibly without changing stored localization. See report 23.
- Query filtering and the evidence-rich 587 KB full-roster serialization remain in memory. Per-import projection caching makes this fast at 116 heroes (17.1 ms warm median locally), but it is not a large-corpus or remote-network query plan. See report 24.
- The API requires an existing migrated database at startup; an empty hero page means a valid database with no successful configured-game import, not a missing file.
- Tier-list drafts are intentionally local to one browser profile. PNG export is local; there is no account sync, editable share link, or server persistence.
- Only English overlays and the hero-library domain are implemented. Artifacts, runes, team building, auth, and deployment remain out of scope.

## Current maintenance trigger: conditional hero-library source refresh

The 2026-08-06 controlled same-version reconciliation is complete. All APK hashes, 1,320 shared files, four patch bundles, six canonical sources, current parser executions, five hero audits, and 116/116 local portraits reconcile without drift. Do not start another speculative semantic pass. Repeat the procedure only when BlueStacks offers a version newer than 2.0.821, a retained source hash changes, or a concrete player-visible discrepancy identifies a targeted question.

Acceptance criteria:

1. If the installed package changed, the user confirms it through Windows PowerShell and BlueStacks `HD-Adb.exe`; no Linux ADB is used.
2. APK/split, patch-manifest, and materialized-cache hashes and inventories are compared with 2.0.821 before replacing any local corpus.
3. A changed source or parser identity produces a new import ID; an unchanged identity may deterministically reuse the prior successful import. All hero audits cover the complete playable roster.
4. Added, removed, or changed heroes, jobs, elements, skills, acquisition relations, localization, classifications, and icon mappings are reviewed explicitly; manual exceptions are revalidated rather than copied blindly.
5. The API contract remains compatible or any deliberate change is documented and tested; performance remains reasonable at the new fixed corpus size.
6. Both clean-checkout and refreshed authentic-asset smoke modes pass `./scripts/verify.sh` and targeted HTTP/UI checks.
7. Only human-written code, tests, migrations, and documentation are eligible for staging; no APK, extraction, proprietary asset, database, generated audit, or smoke output is staged.
# Deployment handoff

Production uses one immutable Fly.io image containing the API, compiled frontend, versioned assets, and purpose-built read-only SQLite catalogue. Production inputs remain local and CI uses generated synthetic inputs. See `docs/deployment.md`.
