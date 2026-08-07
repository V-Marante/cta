# Importer Architecture

## Objective

`cta_importer` is a game-agnostic ingestion kernel. Game formats live in parser plugins; the kernel owns discovery, deterministic version identity, parser dispatch, validation, diagnostics, migrations, transactions, and persistence.

Adding support for a new game version must require only a new or updated parser plugin. Core tables and orchestration do not encode Heroes, Skills, XML, CSV, or Crush Them All concepts.

## Package boundaries

| Module | Responsibility |
|---|---|
| `model` | Immutable transport records and diagnostics |
| `contracts` | Parser, validator, and version-resolver protocols |
| `registry` | Plugin registration, entry-point loading, deterministic parser selection |
| `discovery` | Recursive artifact discovery and SHA-256 manifests |
| `validation` | Core integrity checks and severity policy |
| `engine` | Import lifecycle and orchestration |
| `persistence` | SQLite connection policy, migrations, repositories, transactions |
| `migrations` | Ordered, checksummed SQL schema changes |
| `cli` | Operational entry points only |

Dependencies point inward: plugins depend on contracts/model; the core never imports plugins.

## Parser contract

A parser supplies a `ParserDescriptor`:

- globally unique `parser_id`;
- independently deployable `parser_version`;
- integer `output_schema_version` for its persisted record contract;
- selection `priority`.

`accepts(context, artifact)` may inspect path, media type, fingerprint, game ID, game version, build, or content version. This is the version compatibility boundary. A changed format can be supported by registering a higher-priority parser with a new ID/version, without changing the engine.

`parse(context, artifact)` returns only generic records:

- `EntityRecord(namespace, key, payload)`;
- `RelationRecord(relation, source, target, payload, ordinal)`;
- `LocalizationRecord(namespace, key, locale, field, value)`;
- structured diagnostics.

Parsers must be deterministic and side-effect free. They do not open database transactions, create tables, or depend on records emitted by invocation order. Cross-artifact joins are expressed as relations and checked during whole-dataset validation.

Parser packages are discoverable through the `cta_importer.parsers` Python entry-point group. Unit tests may register parser instances directly.

## Version model

An import version contains:

- `game_id`;
- public game `version`;
- optional `build`;
- optional `content_version`;
- arbitrary JSON metadata.

Version metadata may be supplied explicitly or by a game-specific `VersionResolver`. Import identity combines all version fields, a deterministic digest of every source relative path/size/SHA-256, and a digest of the active parser descriptors.

Consequences:

- identical inputs and parser versions reuse the successful prior import;
- changed content creates a new immutable import;
- changed parser/output schema creates a new import even if files are unchanged;
- identical bytes labeled as different game builds remain separate imports;
- failed/rejected imports never suppress a later retry.

## Dispatch rules

Every artifact is offered to all registered parsers using version-aware `accepts`. Highest priority wins. Equal-priority matches are fatal ambiguity diagnostics. Unmatched artifacts are informational by default or errors under strict `require_all_artifacts` mode.

This makes format ownership explicit and avoids dependence on registration order.

## Validation model

Validation has two layers:

1. Core validation checks generic invariants: non-empty identity, duplicate `(namespace,key)`, and unresolved relation endpoints.
2. Plugin validators check game/version-specific invariants against the complete immutable `ImportDataset`.

Diagnostics have stable code, severity, message, parser ID, source path/line/column/record, and JSON details. Severity policy is request-controlled (`fail_on`); production defaults to rejecting on `error` or `fatal`.

Warnings and informational diagnostics are committed alongside successful datasets. Rejected/failed runs persist their artifact manifest and diagnostics but no entities, relations, or localizations.

## Transaction lifecycle

1. Discover and hash source files outside a write transaction.
2. Resolve version and parser-set identity.
3. Reuse an identical successful import if present.
4. Persist a short `running` lifecycle row.
5. Parse all artifacts without holding a database write lock.
6. Validate the complete in-memory dataset.
7. On rejection, atomically persist manifest + diagnostics and mark `rejected`/`failed`.
8. On success, use one `BEGIN IMMEDIATE` transaction for artifacts, parser executions, entities, relations, localizations, diagnostics, and the terminal `succeeded` state.
9. Any persistence exception rolls back every dataset row. A separate transaction records the failed run and diagnostic.

There is no partially visible successful dataset.

## SQLite persistence

Operational settings:

- foreign keys enabled;
- WAL journaling;
- configurable busy timeout;
- `synchronous=NORMAL` for WAL durability/performance balance;
- explicit transaction ownership (`isolation_level=None`).

Core tables:

- `schema_migrations`: migration name, SHA-256 checksum, timestamp;
- `import_runs`: immutable version/source/parser identity and lifecycle;
- `artifacts`: complete source manifest and selected parser;
- `parser_executions`: parser/output schema version and output counts;
- `entities`: generic namespace/key/JSON payload records;
- `relations`: ordered typed edges with JSON payload;
- `localizations`: field-level locale overlays;
- `diagnostics`: queryable structured findings.

The generic JSON payload is deliberate. New game parser schemas do not require core migrations. Stable downstream projections or materialized views can be introduced separately without coupling ingestion to a specific game version.

## Migration policy

Migration filenames are ordered and immutable. Applied SQL checksums are verified at startup; modifying an applied migration is a hard failure. Future schema changes must add a new numbered migration.

Deployments should run `cta-import init-db <database>` before importing. Migration execution is exclusive and transactional.

## Plugin release policy

For a compatible parser bug fix:

- increment `parser_version`;
- keep `output_schema_version` if emitted record meaning is unchanged.

For an output contract change:

- increment both parser version and `output_schema_version`;
- keep old parser available if old game versions still need it;
- select by version/build/content metadata and artifact signature.

For a newly supported game release:

- add fixture samples and parser tests;
- extend an existing parser only if the format is genuinely compatible;
- otherwise register a version-specific parser with higher priority;
- never add version conditionals to the engine or persistence layer.

## Operational commands

From the repository without installation:

```bash
PYTHONPATH=src python3 -m cta_importer init-db extracted/imports.sqlite
PYTHONPATH=src python3 -m cta_importer list-parsers
```

The in-tree CTA parser package is registered by the CLI; external parser plugins can still use the entry-point contract:

```bash
PYTHONPATH=src python3 -m cta_importer import \
  samples/bluestacks/shared-data/cache/content \
  extracted/imports.sqlite \
  --game-id com.godzilab.idlerpg \
  --version 2.0.821 \
  --build 200821
```

CTA-specific concepts remain under `cta_importer.cta`; the generic kernel does not encode them.

Hero semantic normalization is additive within entity/relation JSON. Progression facts carry a semantic status and original field; explicit acquisition relations carry current/historical status and Config provenance; nullable legacy availability remains separate and never synthesizes an acquisition relation. This needs no relational migration because the generic persistence schema already stores versioned payloads and source locations.

Hero stat facts follow the same additive pattern. `stat_semantics` carries value, status, source field, label, meaning, and unit. Sparse spreadsheet/editor calculations remain separately preserved under `source_calculations`; they are not normalized into runtime combat values. DPS is marked supported only when its persisted value matches the established half-up `Atk / AtkReload` relation.

Skill components preserve ordered raw tags, attribute strings, and text. Additive `attribute_semantics` classifies only context-proven probabilities, durations, counts, health fractions, and internal radii. The API retains localization templates and reports resolved parameters plus unresolved placeholders; generic effect values receive no global conversion.

CTA localization markup is not rewritten in persistence. The frontend tokenizes the raw projected string into accessible emphasis, icon labels, line breaks, and explicit unresolved-format markers. This keeps storage/source provenance lossless and makes rendering behavior independently testable.

The read-only API is a downstream projection, not part of the importer kernel. Its public shape and naming boundary are documented in `docs/hero-api-contract.md`. Mapped heroes are cached by immutable import ID and ordered skills by import/hero; selecting a newer successful import therefore uses a distinct cache entry without weakening import immutability or transaction behavior. Filtering remains in memory because the current fixed public corpus is small.
