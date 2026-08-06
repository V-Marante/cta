# Structured Content Schema and Importer Design

> **Current design snapshot.** Counts describe BlueStacks `2.0.821`, reconfirmed as the latest version offered by the installed BlueStacks distribution on 2026-08-06, and must be revalidated after any future version refresh. See `reports/19-bluestacks-reconciliation.md`.

## Purpose and scope

This document is the technical design for importing every structured file under `samples/bluestacks/shared-data/cache/content/`. It describes formats, record shapes, identifiers, inferred relationships, cardinalities, validation rules, and implementation order. It intentionally contains no import code.

The directory contains 1,301 files. The structured corpus is 1,248 files:

| Format | Files | Treatment |
|---|---:|---|
| Custom animation text | 1,065 | One shared keyframe grammar |
| XML | 98 | 21 canonical files plus 7 localized families × 11 locales |
| Apple plist XML | 50 | Two compatible sprite-atlas schema variants |
| CSV | 35 | 13 canonical files plus 2 localized families × 11 locales |
| Total structured | 1,248 | Fully accounted for below |

The other 53 files are 50 compressed PVR textures, two PNG images, and `.DS_Store`; they are binary/supporting assets rather than structured records.

Supported locale suffixes are `de`, `en`, `es`, `fr`, `it`, `ja`, `ko`, `pt-BR`, `pt`, `ru`, and `zh`.

## Design principles

1. Preserve source values and provenance. Every imported row/node should retain source file, source key/path, and optional source ordinal.
2. Parse canonical gameplay data before localization and assets.
3. Treat inferred foreign keys as soft references initially. The source intentionally contains stale, case-mismatched, polymorphic, and editor-only values.
4. Normalize empty strings to null only after determining whether a field is positional.
5. Preserve unknown attributes and unnamed spreadsheet columns in a raw-property bag until their semantics are proven.
6. Do not flatten ordered child records. Animation keys, waves, rewards, parts, and effects depend on order.
7. Use composite keys where the source reuses IDs by context, notably `(class, key)` for Paragon nodes.

## Proposed importer-layer domains

The source naturally separates into these domains:

| Domain | Primary source | Estimated entities |
|---|---|---:|
| Heroes and combatants | `Heroes.csv`, `Persos.xml` | 148 balance heroes; 217 renderable characters |
| Skills and abilities | `Skills.xml`, `ArmorySkills.xml` | 427 combat skills; 42 armory skill definitions |
| Monster modules | `ModMonsters.xml`, `Modules.csv` | 132 runtime modules; 260 keyed design rows |
| Items and rewards | `Items.xml` | 349 canonical items |
| Artifacts | `Artifacts.csv`, `CrusadeArtifacts.csv` | 186 standard; 62 crusade |
| Runes | `Runes.csv`, `RuneSets.csv`, `HeroRuneSets.csv` | 39 keyed stats; 16 sets; 122 assignment/selectors |
| Dungeons | three dungeon XML files | 78 dungeon keys across normal/crusade/guild sources before deduplication |
| Goals | seven goal XML files | 289 source goal definitions before cross-file deduplication |
| Economy/progression | config, quest, level, paragon CSV/XML | Mixed scalar, tree, and matrix records |
| Localization | 77 XML + 22 CSV files | Locale-keyed overlays |
| Visual metadata | 50 plists, 1,065 animation text files, `Effects.xml` | 1,574 atlas frames; 1,065 timelines; 129 effects |

Counts are source-record counts, not promises of distinct user-visible objects. Deprecated, editor-only, NPC, template, and duplicate records are present.

## Identifier and relationship model

### Strong identifiers

| Entity | Identifier | Evidence |
|---|---|---|
| Hero balance row | `Heroes.Key` | 148/148 non-null and unique |
| Character definition | `Persos/character@key` | 217 distinct values |
| Skill | `Skills/skill@key` | 427 distinct values |
| Runtime module | `ModMonsters/module@key` | 132 distinct values |
| Item | `Items/item@key` | 349 distinct values |
| Artifact | `Artifacts.Key` | 186 nonblank, unique values |
| Crusade artifact | `CrusadeArtifacts.Key` | 62 nonblank, unique values |
| Quest business | `Quests.Key` | 30/30 unique |
| Rune/stat | `Runes.Key` | 39 keyed rows |
| Rune set | `RuneSets.Key` | 16 definition rows |
| Dungeon | `dungeon@key` | Unique within each dungeon source |
| Enemy template | `enemytemplate@key` | Unique within each dungeon source |
| Goal | `goal@key` | Unique within each goal source; namespace by source family |
| Guild quest | `guildquest@id` | 8 definitions |
| Paragon node | `(Class, Key)` | 171 rows; only 27 repeated node keys across 10 classes |
| Guild level | `GuildLevel` | 302 unique levels, 0–301 |
| Player level | `PlayerLevel` | 102 actual keyed rows plus four spreadsheet/meta rows |
| Atlas frame | `(plist file, frame key)` | 1,574 frames across 50 atlases |
| Animation | filename | 1,065 unique timeline files |

### High-confidence foreign keys

| Source field | Target | Evidence/coverage |
|---|---|---|
| `Heroes.Key` | `Persos.character@key` | 146 of 148 exact matches |
| `Persos/character/skill` text | `Skills.skill@key` | 338 of 339 distinct values; only `MokingFI` unresolved |
| `Persos/character/ability` text | `Skills.skill@key` | 9 of 9 |
| `Persos/character/module@name` | `ModMonsters.module@key` | 24 of 24 |
| `Persos/character@skinOwner` | `Heroes.Key` | 25 of 25 |
| `ModMonsters/module/weapon@skill` | `Skills.skill@key` | 27 of 27 |
| `ModMonsters/module/anim@skill` | `Skills.skill@key` | 11 of 11 |
| `ModMonsters/module/inherit` text | `ModMonsters.module@key` | 6 of 6 |
| Dungeon `enemytemplate/module@name` | `ModMonsters.module@key` | All observed values in all three dungeon families |
| `Dungeons/enemytemplate/skill` text | `Skills.skill@key` | 5 of 5 |
| Dungeon reward item text | `Items.item@key` | All observed normal/guild reward items |
| Goal `reward@item` | `Items.item@key` | All except `Medal_RobinHood`, likely a generated/legacy medal ID |
| `ArmorySets/set/item@keyItem` | `Items.item@key` | 40 of 45; five football-event keys are absent from canonical items |
| `Artifacts.GLibDep` | `Artifacts.Key` | 9 of 9 distinct dependency keys |
| `Paragon.DependencyKey` | Paragon node in same class | 13 of 13 distinct values |
| `HeroRuneSets.Set1..Set3` | `RuneSets.Key` | Every populated set value |
| `RuneSets.Family` | `Runes` family/stat vocabulary | 16 of 16 |
| Localization `Key`/`@key` | Canonical family key | Overlay relationship, with documented stale/extra keys |
| Plist `metadata.realTextureFileName` | sibling texture file | 50 of 50 resolve |

### Polymorphic and soft references

- Dungeon `wave@enemy` may point to an enemy template, a team template, a character/hero, or a runtime module. It must be resolved against a tagged union, not a single table.
- Dungeon `env`, level `env` text, and `envset/env` values form an environment namespace that sometimes overlaps dungeon/module keys but is not identical to either.
- Goal `subgoal@object`, `trigger@object`, `intro@owner`, and `post@owner` are polymorphic UI, item, character, quest, or subsystem identifiers.
- Effect names (`HeroIncreaseAtk`, `BuffHP`, and similar) are behavior identifiers shared across Heroes, Artifacts, Runes, Paragon, ArmorySkills, Skills, and native code. They should initially be imported as an effect-code vocabulary, not constrained to `Skills.skill@key`.
- Item `currency` points back into the item namespace for the three observed currency keys.
- Artifact `Event` and item `event` are event-code vocabulary. Some values overlap module names accidentally and should not be made module foreign keys.
- Sprite, icon, FX, animation, sound, and shader names are resource references. Many resolve by basename or atlas frame rather than by physical filename.

### Known identifier exceptions

- `Heroes.Key=DDSaberDancer` differs by case from `Persos.key=DDSaberdancer`.
- `Heroes.Key=Pumpking` differs by case from `Persos.key=PumpKing`.
- `Persos.xml` has 71 character keys not present in `Heroes.csv`; these include NPCs, pets, skins/variants, intro characters, enemies, and utility characters.
- Localization tables contain stale and forward-looking keys. They are overlays, not authoritative entity lists.
- All key joins should retain both exact and normalized-match diagnostics. Never silently rewrite canonical IDs.

## CSV schemas

### `Heroes.csv`

148 data rows, all populated and uniquely keyed. Canonical PK: `Key`.

Fields:

- Identity/classification: `Name`, `Key`, `Class`, `Tribe`, `Sex`, `Damage Type`, `Elemental`.
- Ability codes: `Ability1`, `Ability2`, `Ability3`.
- Base combat values: `Flying`, `Atk`, `HP`, `Def`, `AtkRange`, `AtkReload`, `MoveSpeed`, `Ctk`, `CtkDmg`, `Resistance`, `Evade`.
- Acquisition/progression: `BaseStars`, `MaxStars`, `Dungeon`, `Shop`, `Event`, `Rarity`, `ChestEpic`.
- Derived/editor values: `POW`, `DPS`, `Atk w/ stars`, `HP w/ stars`, `POW / Stars`.
- Fourth-skill/editor columns: `SP4`, `SP4 Target`, `SP4 Value`, `Skill actif`, `dev`, `new`, `icon`, unnamed columns 40–41, `Factor per Star`.

Types are mostly numeric after normalization. `Damage Type` contains trailing whitespace (`Magic `), and flags mix blank, `0`/`1`, and `x`. Enumerations observed: 10 classes, 11 tribes, two sexes, two normalized damage types, and six elements.

### `Artifacts.csv` and `CrusadeArtifacts.csv`

These share a broad 38-column prefix. `Artifacts.csv` has 195 physical rows but only 186 keyed entities; `CrusadeArtifacts.csv` has 67 physical rows and 62 keyed entities. Blank rows are separators/editor residue.

Shared logical fields:

- Identity: `Name`, `Key`, `Set`, `Sprite`, `Event`.
- Applicability: `Class`, `Tribe`, `Elemental1`, `Elemental2`, `Class2`.
- Effects: `Effect1`, `Effect2`, `EffectSet`, `EffectSetClass`, `EffectSetValue`.
- Progression/economy: `Stars`, `Rarity`, `Cost`, `CostRs`, `Cost2`, `CostRs2`, `Cost3`, `CostRs3`.
- Behavior/flags: `Deprecated`, `Research`, `Duration`, `ItemValue`, `ItemValue2`, `Multiplicative`.
- Guild library: `GLibCategory`, `GLibLevel`, `GLibDep`.
- Elemental research values: `RWA`, `RFI`, `REA`, `RLI`, `RDA`.

`Artifacts.csv` also has five trailing unnamed editor columns. Preserve them by ordinal (`source_column_39` through `source_column_43`) until semantics are established. The standard and crusade keyspaces should be separate entity subtypes, with a shared artifact model.

### `Artifacts_<locale>.csv`

Eleven files with identical `Key,Name` schema and 254 unique rows each. Across the union of standard and crusade canonical artifacts, every locale has 247 matches, seven stale/extra keys, and one canonical key missing. Use `(artifact_key, locale)` as the overlay key and allow orphan localization rows.

### `Quests.csv` and `Quests_<locale>.csv`

`Quests.csv` has 30 unique keyed business entities. Fields are `Name`, `Key`, `Time`, `Cost`, `CostExp`, `CostBig`, `Revenue0`, `RevenueExp`, `RPS`, `RevBig`, `Sprite`, `AutoCollect`, `AscendCount`, unnamed column 13, `Rev/Cost`, `# Quest Buy`, unnamed column 16, `# Quest BuyX`, and `MAX Lv Bonus`.

The unnamed columns are populated calculation/editor values and should be preserved but not treated as stable public schema without additional evidence.

Each locale file has `Key,Name` and 31 unique rows: all 30 canonical quest keys plus extra key `Research Lab`.

### `Runes.csv`

43 physical rows, 39 keyed rune/stat entities, and four blank/editor rows. Fields:

`Name`, `Key`, `Description`, `FamilyOnly`, `FamilyLikely`, `PrimChance`, `SecondaryChance`, `Element`, `EffectType`, `Effect1`, `ValueBase`, `ValueInc`, `Max at 6*`, `Sprite`, `SetNumRune`, `blank`, `PROD VALUES`, and two unnamed production columns.

Percent values are strings and must retain `%`. `ValueBase` can be scalar or encoded text. `Effect1` is an effect code, not necessarily a skill FK.

### `RuneSets.csv`

This file contains two adjacent tables in one CSV:

- Columns 0–6: 16 rune-set definitions keyed by `Key`, with `Family`, `MainStat`, and `Secondary1..Secondary4`.
- Columns 8–9: 23 family-to-stat vocabulary rows (`Families`, `Stats`), of which 15 have a stat value.

Column 7 is an intentional separator. Import these as two record types rather than one sparse row.

### `HeroRuneSets.csv`

This is a transposed/editor matrix, not a conventional table. It has 123 physical rows:

- Column 0 contains 122 selectors, mostly hero keys but also classes, elements, and named groups.
- Columns 2–5 contain 30 assignment rows: an assignment target plus `Set1`, `Set2`, `Set3`.
- Columns 1 and 6 are separators.

The displayed header is misleading (`Empty,Empty,Key,...`). Preserve row position. Model each populated cell region separately as selector membership and rune-set recommendation records. Do not enforce column 0 solely as a hero FK.

### `Paragon.csv`

171 rows. Composite PK: `(Class, Key)`. There are 10 class trees, three tree types, and 27 reusable node keys.

Fields: `Name`, `Key`, `Class`, `Tree`, `DependencyKey`, `LibraryLevel`, `EffectType`, `EffectKey`, `BaseValue`, `IncValue`, `MaxLevels`, `Sprite`, `Column`, and one empty trailing column.

`DependencyKey` is a self-FK within the same class. `BaseValue` and `IncValue` may be numbers or underscore-delimited element vectors such as `0.7_0.7_1.2_1.2`; store both raw value and parsed vector. `EffectKey` is either a stat behavior code or a skill/ability key.

### `GuildLevel.csv`

302 rows keyed by `GuildLevel`. Core fields: `XPPerGL`, `XPPerGLRounded`, `XPAcc`, `Mul-2`, `Days to Lv`, and `Days / Orb`. `Avg XP / day`, `Max Research`, and `Total Cost` are populated only on row 0 and appear to be spreadsheet parameters. The final column is empty.

### `PlayerLevel.csv`

106 physical rows, approximately 102 actual levels. Fields: `PlayerLevel`, `PrismPerPL`, `PrismPerPLRounded`, `PrismAcc`, `Mul-2`, `Stage Reached`, unnamed column 6, `Item1`, `Count1`, and an empty trailing column. Several final/meta rows lack a level and must be classified before enforcing the PK. `Item1` is a reward/item code and should be a soft item FK.

### `Modules.csv`

325 physical rows; 260 rows have unique `Key` values. This is legacy/design balance data distinct from the 132 runtime modules in `ModMonsters.xml`.

Fields by role:

- Identity: unnamed display-name column 0, `Key`, `From`.
- Combat: `Damage`, `ReloadTime`, `Da/s`, `HP`, `RepairTime`, `Crew`, `HP Max`, `DamScore`, `ReloadScore`, `AtkScore`, `HPScore`, `AtkAdjust`, `Pwr`.
- Classification: `Tier`, `Family`, `Strength`, `Weak`, `Source`.
- Economy: `OldCost`, `Cost`, `CostRare`, `WPI`, `WNV`, `WDD`, `Res Value`, `Pwr/Cost`, `CostCrea`, `CostCreaRare`.
- Unlocks: `UnlockDungeon`, `UnlockDifficulty`, `UnlockLvl`.
- Labels/behavior: `Name-en`, `Name-fr`, `type`, `Skill`, `skill info`, `Special`.
- Separator/editor columns: 3, 10, and 23.

Cost fields use semicolon-delimited mini-records. Import XML runtime modules first and retain this CSV as a related design/balance table; do not merge records solely by similar names.

### `CrusadeTeams.csv`

121 physical rows; column `Keys` has 120 unique populated selectors. `Team1..Team12` form a sparse matrix; `Team13..Team15` and `Last` are empty. Cells mix hero IDs with headings such as `Water 1`, `Difficulty: 4`, or `Group 1`. Parse it as ordered matrix sections, then resolve hero-looking cells softly against Hero/Character IDs.

### `GuildQuests.csv`

1,403 rows in a block-oriented matrix, not a flat table. Each block begins with:

1. `QuestId,<quest-code>`
2. `Difficulty,<0|1|2>`
3. a `Tier` reward header and tier rows terminated by `End`
4. one or more `Leaderboard,From,To,<reward columns...>` sections, each terminated by `End`

Reward column names are item/currency IDs such as `GuildCoin`, `GuildXP`, `RuneDust`, `ChestRune`, and `Arena3vs3Coin`; many match `Items.item@key`. The importer should emit quest-difficulty blocks, tier thresholds/rewards, and leaderboard range/reward records while preserving source order.

## XML schemas

### Goal-family XML

The goal engine uses seven canonical files with related but distinct schemas:

| File | Root | Primary records | Main child records |
|---|---|---:|---|
| `Achievements.xml` | `goals` | 19 `goal` | `subgoal`, `count`, 95 `reward` |
| `Bootcamp.xml` | `goals` | 15 `goal` | `subgoal`, `count`, 49 `reward` |
| `DailyChallenges.xml` | `goals` | 28 `goal` | `subgoal`, `count`, `object`, 28 `reward` |
| `Goals.xml` | `goals` | 48 `goal` | `intro`, `unlock`, `subgoal`, `post`, `trigger`, `reward` |
| `StageGoals.xml` | `goals` | 41 `goal` | `subgoal`, 122 `reward`, `unlock` |
| `Success.xml` | `goals` | 88 `goal` | `subgoal`, `count`, `badge` |
| `Tutorial.xml` | `goals` | 50 `goal` | Same general workflow schema as `Goals.xml` |

Common goal identity is `goal@key`, namespaced by source file. Goal attributes across the family include `owner`, `title`, `condition`, `pause`, `retroactive`, `tutorial`, `checkTutorialkey`, `achievement`, `bootcamp`, `day`, `daily`, `success`, `version`, `canComplete`, `isSpecial`, and `showWhenNotCompleted`.

Child schemas:

- `subgoal`: `type`, optional `object`, optional `num`.
- `reward`: `item`, `count`, optional `countIndex`; Stage/Guild dungeon reward items may instead be text nodes.
- `intro`/`post`: text plus `owner`, `anim`.
- `trigger`: `type`, `object`, `value`.
- `unlock`: target goal in text, optional `delay`.
- `count`, `object`, `badge`: scalar text.

Goals form a directed unlock graph. `Goals.xml` and `Tutorial.xml` overlap heavily and should remain separate source namespaces until a deliberate deduplication phase.

### Localized goal XML

`Goals_<locale>.xml` contains 36 `goal` overlays per locale. `Tutorial_<locale>.xml` contains 36 `goal` overlays per locale under root `tutorial`. Both use `goal@key` plus localized child text records. Localization covers only user-facing records, not every canonical goal.

### `Persos.xml`

Root `characters`; 217 `character` entities keyed by `@key`.

Character attributes include identity and render configuration: `assets`, `name`, `name-fr`, `sexe`, `element`, `element2`, `rare`, `event`, `offer`, `style`, `villain`, `skinOwner`, `iconIdx`, `mirror`, scale/offset fields, weapon/skin flags, and boat/flying options.

Ordered child collections:

- `part` (1,677): body-part name/index/color/variant and layering flags.
- `anim` (893): logical animation → resource name plus speed, loop, event timing, weapon bone, intro/outro, and camera-shake settings.
- `skill` (456): skill key text.
- `module` (24): runtime module key in `name`.
- `collectable` (22): chest/menu/medal settings.
- `ability` (10): skill/ability key text.
- `info` (154), `params` (one special record), `fx` (two records).

The balance-Hero → Character relation is nearly 1:1 but optional. Two case mismatches and 71 non-hero characters require separate entity types.

### `Persos_<locale>.xml`

Each of 11 files contains 211 character localization rows plus one root and one nested helper node. Schema is `characters/character@key` with localized text children/attributes. Against canonical characters, each locale has 186 exact matches, 25 stale/extra IDs, and 31 current character IDs without localized records.

### `Skills.xml`

Root `skills`; 427 `skill` entities keyed by `@key`.

Skill attributes: `type`, `name`, `name-fr`, targeting (`target`, `targetclass`, `targetelement`, `object`), classification (`active`, `category`, `isBuff`, `applyElement`), resource linkage (`module`, `sprite`, `weapon`), and numeric behavior (`cost`, `strength`, `radius`, `dmgair`).

Ordered child variants:

- `spec` (291): 38 optional scalar behavior attributes covering damage, scaling, timing, count, cooldown, shield, repair/reload, projectile ordering, and versions.
- `proj` (352): 38 optional projectile attributes covering bone/origin, trajectory/type, sprite/FX, speed/radius, status effect, lifetime, delays, and damage behavior.
- `hit` (256): `time`, optional `boost`, `splashRad`.
- `effect` (112): `type`, `chance`, `duration`, `value`, FX fields.
- `fx` (64): attachment, bone, delay/duration/lifetime, scale, hit FX, camera shake.
- `sprite` (159), `info` (334), `info-fr` (34): text resources/local descriptions.
- `postDamageSpec` (2): shield conversion/cap and FX settings.

Implement child records as tagged variants rather than one extremely sparse table.

### `Skills_<locale>.xml`

Each parseable locale contains 341 skill overlays. There are 338 exact canonical matches, three stale/extra IDs, and 89 canonical skills with no localization row. `Skills_ru.xml` is malformed at line 329, column 226; import policy should record the error, optionally recover individual records, and never fail the whole content import.

### `Items.xml`

Root `items`; 349 `item` entities keyed by `@key`.

The 46 optional item attributes cover:

- identity/display: `name`, `name-fr`, `icon`, `smallIcon`, `order`, `short`;
- economy: `cost`, `currency`, `price`, `flooz`, `gcoins`, `vipPts`;
- acquisition/visibility: `shop`, `event`, `platform`, `inventory`, `hidden`, `sold`, `chest`, `multiChest`, `dailyDraw`, registration/draw timing;
- behavior: `consumable`, `usable`, `openOnReceipt`, `rewardedOnServer`, `confirm`, `onlyBuy`, `bAskFacebook`, `video`, `treasurehunt`, `petFragment`, `minigame`;
- scaling/bundles: `multiItem`, `scaleReward`, `scaleBossRssWithLevel`, `bonusWithScore`, `stat`, `time`, `levelNeeded`.

Children: `info` (184), `info-fr` (129), and `source` (49), all text-bearing. Item bundles encoded in `multiItem` require a later mini-language pass; preserve raw form first.

### `Items_<locale>.xml`

Each locale has 278 overlay records. There are 274 exact canonical matches, four stale/extra keys, and 75 canonical items without localization. The four extras are `Energy600`, `LabyrinthCoin`, `PackFlooz7`, and `PackFlooz9`.

### Dungeon-family XML

Three files share a dungeon/enemy/wave model:

| File | Dungeon records | Enemy templates | Notable differences |
|---|---:|---:|---|
| `Dungeons.xml` | 32 | 36 | Env sets, teams, 191 levels, 283 waves, daily/persistent fields |
| `CrusadeDungeons.xml` | 29 | 29 | Requirements and one-level wave templates |
| `GuildDungeons.xml` | 17 | 17 | Guild descriptions and chance-based level/dungeon rewards |

Common structures:

- `enemytemplate@key`: attributes `name`, `element`/`element2`; child `params`, one or more `module@name`, optional skill text.
- `params`: `atk`, `hp`, `def`, `atkRange`, `resistance`, `speed`.
- `dungeon@key`: name, element, environment, icon/music, boss, level count and mode flags.
- `level`: level/index and scaling/repetition/stage attributes.
- `wave`: polymorphic `enemy`, plus count/stars/scaling/immunity.
- `req`: `class`, `locomotion`, `buff`, or `minUnitPrism`.
- `reward/item`: item code with count/chance.

`Dungeons.xml` additionally defines 20 `envset` records and 19 top-level `team` records containing 81 waves. Dungeon keys should be namespaced by mode unless global uniqueness is separately verified.

### `Dungeons_<locale>.xml`

Each locale contains 43 dungeon overlays. All 43 keys resolve into the union of canonical dungeon sources; 35 canonical dungeon records have no locale overlay.

### `ModMonsters.xml`

Root `modules`; 132 runtime `module` entities keyed by `@key`.

Module attributes: `name`, `name-fr`, `icon`, `type`, `price`, `menu`, and `showEnemyReload`.

Child variants and counts:

- `spec` 97: attack, reload, defense, speed, projectile, repair, weakpoint.
- `body` 117: dimensions, offsets, scale, Spine/render/flying settings.
- `anchor` 112; `anim` 327; `boneinfo` 53; `texture` 75; `fx` 19.
- `weapon` 37 with `skill` FK; `postfix` 43; `inherit` 16.
- Specialized `parentanim`, `heart`, `hit_vfx`, `weakness`, and `bodySprite` nodes.

This file is authoritative for runtime monster/module composition and joins directly from enemy templates.

### Armory XML

`ArmorySets.xml` has nine sets keyed by `set@key`, with `order`, 45 `item@keyItem` membership rows, and 36 named scalar `value` children.

`ArmorySkills.xml` has 42 `skill` records with `key`, `descKey`, `order`, `powerBase`, and `type`. Its `key` is a behavior-code namespace; only some values coincide with combat skill IDs. `descKey` mostly maps to Paragon-like localization keys.

### Config XML

`Config.xml` is a hierarchical key/value tree:

- 1,903 top-level `value` nodes.
- 198 top-level `group` nodes.
- Nested to three group levels.
- 1,921 nested `value` nodes across group depths.
- `value` uses `name`, optional vector coordinates `x`, `y`, `z`, and text value.

The stable identifier is full group path plus `value@name`, not name alone. Values are polymorphic strings: booleans, integers, floating point, dates, colors, IDs, lists, and encoded templates. Import a lossless configuration tree first; add typed projections only per known path.

`ConfigDev.xml` is the same scalar model with four top-level values. `ConfigEnv.xml` is a separate hierarchical environment tree with five top-level values, 401 nested groups, and 1,537 nested values. It contains environment/composition data and should not be merged blindly with gameplay config.

Each `Config_<locale>.xml` has 509 top-level values plus five groups and 208 grouped values (717 value records total). Localization uses full path plus `value@name`; it is not keyed with `@key`.

### `GuildQuests.xml`

Root `guildquests` carries 12 global scalar attributes including activity flags, cooldowns, retry limits, ranks, timers, and update frequencies.

Children:

- `difficulties/difficulty` ×3 with `activationFee`, `durationInDays`, `guildFee`.
- `guildquest` ×8 keyed by `@id`, with `category`, `type`, and cooldown fields.
- `ascendsettings` containing three `minascendpercentage` and three `minascendstage` values.

The eight IDs join to block IDs in `GuildQuests.csv`; the XML defines behavior while CSV defines reward schedules.

### `Effects.xml`

Root `EFFECTS`; 129 `EFFECT` entities keyed by `@NAME`, plus one `SHAPES` catalog containing 59 `IMAGE` records keyed/indexed by `@INDEX` and `@URL`.

Each effect contains:

- Effect-level attributes controlling type, length, uniformity, emission, geometry, handles, traversal, spawn direction, and end behavior.
- One `ANIMATION_PROPERTIES` record with size, frame, loop, export, color, transparency, seed, offset, and grid fields.
- Effect curves: `AMOUNT`, `LIFE`, `SIZEX`, `SIZEY`, `VELOCITY`, `WEIGHT`, `SPIN`, `ALPHA`, `EMISSIONANGLE`, `EMISSIONRANGE`, `AREA_WIDTH`, `AREA_HEIGHT`, `ANGLE`, `STRETCH`, and optional `GLOBAL_ZOOM`; curve points use `FRAME` and `VALUE`.
- 268 `PARTICLE` records. Particle attributes describe sprite/name, frame, blend/layer, animation, relative/angle behavior, repetition, and emission behavior.
- Particle curves for base values, variations, over-time alpha/velocity/weight/scale/spin/RGB/direction/framerate/global velocity/stretch/splatter/emission. Some curve nodes contain `CURVE` children with left/right control-point coordinates.

Model effect, emitter/particle, curve, curve-point, and shape as separate ordered records. Do not map every optional curve name to columns in one table.

## Sprite atlas plists

All 50 plist files parse successfully and reference an existing sibling texture. Together they define 1,574 frame records, ranging from 1 to 458 frames per atlas.

Two schema variants occur:

1. 29 files use TexturePacker/Cocos-style fields: `frame`, `offset`, `rotated`, `sourceColorRect`, `sourceSize`.
2. 21 files use polygon-capable fields: `aliases`, `spriteOffset`, `spriteSize`, `spriteSourceSize`, `textureRect`, `textureRotated`, `triangles`, `vertices`, `verticesUV`.

Top-level keys are `frames` and `metadata`. Metadata includes format and the backing texture filename, with optional size/pixel-format/premultiplied-alpha details. Normalize both variants to atlas, frame, rectangle, source size/offset, rotation, aliases, and optional mesh geometry; preserve original coordinate strings.

## Animation text descriptors

All 1,065 `.txt` files conform to the same custom timeline grammar. Every file has:

1. composition name on the first line;
2. `Duration: <integer> frames`;
3. `Frame Rate: <number> fps`;
4. `Parent List` entries of `<node> Parent <parent|null>` terminated by `End Parent List`;
5. repeated node/property blocks followed by keyframe rows.

Observed properties are `Anchor Point`, `Position`, `X Position`, `Y Position`, `Scale`, `Rotation`, and `Opacity`. Keyframe rows are positional numeric tuples beginning with a frame number; negative pre-roll frames occur. Durations range from 0 to 599 frames. Frame rates are 12, 24, approximately 29.97, 30, or 45 fps. Parent lists contain 2–54 nodes. There are 113 distinct composition names reused across filenames.

Recommended normalized model:

- animation asset: filename, composition, duration, frame rate;
- animation node: ordered node name and optional parent;
- property track: node + property kind;
- keyframe: ordered frame number plus raw numeric vector.

Node names often point to atlas frame names, but resolution is by sprite basename and may be many-to-many. Treat it as a soft asset reference.

## Localization strategy

Localization files are incomplete overlays and sometimes contain stale records. Never use them to create or delete canonical entities.

| Family | Records per locale | Exact canonical coverage | Known issue |
|---|---:|---:|---|
| Artifacts CSV | 254 | 247 union matches | 7 extras, 1 canonical missing |
| Quests CSV | 31 | 30 matches | extra `Research Lab` |
| Config XML | 717 values | Path-based, not key-based | Must join by full group/value path |
| Dungeons XML | 43 | 43 union matches | 35 canonical dungeon keys unlocalized |
| Goals XML | 36 | 36 matches | 12 `Goals.xml` keys unlocalized |
| Items XML | 278 | 274 matches | 4 extras, 75 canonical missing |
| Persos XML | 211 | 186 matches | 25 extras, 31 canonical missing |
| Skills XML | 341 | 338 matches | 3 extras, 89 canonical missing; Russian malformed |
| Tutorial XML | 36 | 36 matches | 14 canonical tutorial keys unlocalized |

Use fallback order: requested locale → `en` overlay → canonical inline `name`/`info` → key. Keep localization provenance and orphan rows for diagnostics.

## Validation and data-quality rules

### Hard failures

- Unreadable CSV/XML/plist or invalid encoding.
- Duplicate canonical PK within the same source namespace.
- Missing mandatory identity key on a row classified as an entity.
- Invalid ordered child ownership, such as a skill child outside a skill.

### Warnings

- Unresolved soft FK or case-only match.
- Orphan localization row or missing localized value.
- Unknown XML attribute/child tag.
- Ragged CSV row, unnamed populated column, spreadsheet formula residue, or separator row.
- Unknown effect code, item/currency ID, animation, sprite, FX, or environment name.
- Numeric field containing a nonnumeric sentinel such as `#N/A`.

### Known source anomaly

`Skills_ru.xml` is not well-formed at line 329, column 226. The importer should report this deterministically. Recovery, if later desired, should be an explicit tolerant-localization mode and must not alter canonical skill import.

## Recommended parser implementation order

### Phase 1 — Lossless primitives

1. Common source/provenance model and diagnostics.
2. Robust CSV reader preserving empty columns, row ordinals, and raw headers.
3. XML reader preserving order, text, all attributes, and full element path.
4. Shared scalar coercion helpers that always retain raw values.

These are prerequisites for every gameplay importer and establish consistent error handling.

### Phase 2 — Canonical registries

5. `Items.xml` — establishes reward/currency identifiers used broadly.
6. `Skills.xml` — establishes the skill/effect registry.
7. `ModMonsters.xml` — depends on skills and establishes runtime modules.
8. `Persos.xml` — depends on skills and modules; establishes characters.
9. `Heroes.csv` — links balance rows to characters and establishes classifications.

This order resolves the densest and most valuable dependency chain first.

### Phase 3 — Core gameplay relationships

10. Dungeon family: enemy templates → teams/envsets → dungeons → levels → waves → rewards.
11. Goal family: goal records → subgoals/triggers → rewards → unlock graph.
12. Artifacts and crusade artifacts, including dependencies and effect codes.
13. Runes → rune sets → hero/set recommendation matrix.
14. Armory skills → armory sets.
15. Paragon class trees and same-class dependencies.

### Phase 4 — Economy and specialized matrices

16. `Quests.csv` and quest localization.
17. `GuildLevel.csv` and `PlayerLevel.csv`.
18. `GuildQuests.xml`, then block parser for `GuildQuests.csv`.
19. `Config.xml`/`ConfigDev.xml` as a lossless tree, followed by known typed projections.
20. `ConfigEnv.xml` as a separate environment tree.
21. `Modules.csv` legacy/design data and `CrusadeTeams.csv` section matrix.

The matrix and configuration sources come later because they contain embedded mini-languages and editor residue.

### Phase 5 — Localization

22. Generic locale overlay layer.
23. CSV overlays for artifacts and quests.
24. XML overlays for config, dungeons, goals, items, characters, skills, and tutorials.
25. Fallback computation and orphan/missing coverage diagnostics.

### Phase 6 — Visual metadata

26. Plist atlas parser with both frame variants.
27. Animation timeline text parser.
28. `Effects.xml` effect/emitter/curve parser.
29. Soft resolution of sprites, atlas frames, textures, animations, FX, and sounds.

Visual parsing is independent enough to develop in parallel later, but it should not block the core gameplay importer.

## Recommended importer outputs

The importer layer should expose normalized entities plus source-faithful subordinate records:

- canonical entities with stable source IDs and namespaces;
- ordered child collections for XML/timelines;
- explicit join tables for hero skills/modules, dungeon waves/rewards, artifact effects, rune recommendations, and atlas frames;
- localization overlays keyed by `(entity namespace, entity key, locale, field)`;
- configuration entries keyed by full hierarchical path;
- unresolved-reference and data-quality diagnostics as first-class output;
- raw attribute/column bags for forward compatibility.

The initial importer should avoid calculated gameplay values, asset conversion, semantic merging of near-duplicate IDs, and database-specific constraints. Those belong in validation or downstream transformation layers after the lossless import is proven.
