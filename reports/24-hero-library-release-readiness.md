# Hero-library release-readiness audit

Date: 2026-08-06  
Source version: BlueStacks CTA 2.0.821  
Scope: existing hero-library importer, read-only API, and React UI only

## Outcome

The slice is ready for local use with its known evidence limitations. Unified verification passes, the latest real import contains 116 collectible heroes (plus 16 enemy, 1 reviewed non-collectible, 2 NPC, 2 summoned-variant, 1 transformed-variant, and 10 uncertain records that remain private), both asset modes work, and no release-blocking API, accessibility, or local-performance defect remains.

## API contract and consistency

`docs/hero-api-contract.md` freezes the current endpoint, query, DTO, naming, null, and compatibility rules. Endpoint metadata now supplies stable operation names and declared success/404 response types. The JSON payload itself did not change except that health now uses a typed record with the identical `{ "status": "ok" }` body.

Top-level DTO members remain camelCase. Nested importer objects remain snake_case intentionally because they are source/provenance-bearing persisted shapes. Public endpoints continue to exclude every non-collectible classification; the obsolete `includeNonCollectible` parameter remains an ignored unknown parameter rather than reopening non-playable data.

## Accessibility and responsive audit

Code and automated interaction checks covered roster, detail, loading, empty, and error/retry states:

- native buttons, inputs, selects, details, and headings preserve keyboard semantics;
- the filter toolbar and roster are named regions, and search has a programmatic label;
- loading and empty results are status announcements; failures are alerts with a keyboard-operable retry;
- SPA route completion focuses the page `h1`, including the asynchronously loaded detail view;
- job/element icons retain accessible text names while decorative image pixels are hidden;
- portraits have hero-specific alt text; missing portraits expose “Portrait unavailable” and the full name;
- a high-visibility focus ring was added, and hover movement is removed under `prefers-reduced-motion`;
- the existing 650 px breakpoint stacks detail content, makes controls at least 44 px tall, and collapses the roster to one column at the 320 px supported minimum.

Static WCAG contrast calculations for recurring pairs were all above 4.5:1: muted roster text 6.98–8.71:1, muted detail labels 6.24:1, yellow accents 9.34:1, primary text 12.61:1, and the focus ring 15.70:1 against the darkest background. This is a code/static review, not a claim of external assistive-technology certification.

## Local performance

The real ignored 2.0.821 database was served in Production mode on loopback. Each endpoint was requested 31 times; figures below report the first request and median/95th percentile of the following 30 sequential requests on this development machine.

| Endpoint | Body | First | Warm median | Warm p95 |
|---|---:|---:|---:|---:|
| full roster (`pageSize=250`) | 587,305 B | 330.72 ms | 17.10 ms | 22.14 ms |
| filters | 2,177 B | 18.07 ms | 2.75 ms | 4.40 ms |
| Senshi detail | 10,728 B | 27.06 ms | 2.48 ms | 3.71 ms |
| Senshi skills | 5,275 B | 8.11 ms | 2.33 ms | 3.37 ms |
| health | 15 B | 3.75 ms | 2.37 ms | 3.70 ms |

Previously, every list/filter/detail request rebuilt the full mapped hero projection and its localization, passive, and acquisition maps. `HeroRepository` now caches that projection by immutable import ID and ordered skills by import/hero. A new import cannot reuse an old projection. The remaining full-roster cost is primarily serialization/transfer of a 587 KB evidence-rich response; it is acceptable for 116 local records, but server-side filtering/projection would be the next scalability step if the corpus or deployment model changes.

## Asset-mode smoke verification

Authentic mode used ignored `local/proprietary/` roots: Senshi detail returned 200/10,728 B, the Fire element icon returned 200/2,388 B, and the Senshi portrait returned 200/21,903 B.

Clean-checkout mode pointed both asset roots at absent temporary directories: Senshi detail still returned 200/10,709 B with `portraitUrl: null`; both static asset paths returned 404/0 B. Frontend component tests verify the full-name portrait fallback and accessible text job/element fallbacks. Production build succeeds without local proprietary files. No proprietary material is compiled into the frontend bundle.

## Known-data exception register

| Exception | Current handling | Evidence |
|---|---|---|
| Werewolf stale collectible evidence | explicit `non_collectible` manual review; never public | handoff and classification tests |
| 23 unresolved non-playable/legacy portrait rows; out-of-range CuddlesBerserk frame | excluded from playable library; accessible fallback remains | handoff, report 19 |
| `BaseStars` | raw, explicitly unresolved | report 20 |
| `MaxStars` | strongly supported evolution cap, qualified wording | report 20 |
| rarity | independent source-defined tier | report 20 |
| POW and factor-per-star/spreadsheet calculations | raw unresolved source scores, not gameplay totals | report 21 |
| internal physical units/formulas for some combat values | source labels preserved; no invented conversion | report 21 |
| seven unresolved displayed localization placeholders | visibly marked unresolved, template preserved | reports 22–23 |
| four missing English skill descriptions | “Description unavailable”; absence verified across locales/native strings | report 23 |
| legacy availability meaning/freshness | nullable `legacy_unverified` lane; never overrides explicit relations | report 20 |

## Verification

The final unified run passed 25/25 Python tests, 12/12 API tests, and 27/27 frontend tests; .NET built with zero warnings/errors, `npm ci` reported zero vulnerabilities, and the Vite production build succeeded. Generated benchmark and smoke bodies were written only under `/tmp`.

No Android interaction was needed. No extracted content, proprietary asset, database, generated audit, or benchmark output is part of this report or intended for staging.
