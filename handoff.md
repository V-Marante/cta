# CTA hero-library handoff

Last updated: 2026-08-06

> Classification update: the source-backed roster milestone is complete. The latest local import now classifies 116 collectible, 16 enemy, 10 uncertain, 2 NPC, 2 summoned variants, 1 transformed variant, and 1 manually verified non-collectible (`Werewolf`). Case-only hero/character/skill/acquisition joins are resolved with raw identifiers retained. Counts and recommendations below describe the pre-milestone audit; `docs/handoff.md` is the canonical current handoff.

> Hero-data correction update: internal class `Fighter` is exposed as `Brawler`; medal acquisition includes Arena, Arena 3v3, and Crusade shops plus starter packs; Senshi resolves Halloween Chest and Crusade Shop. The public API/UI omit all non-playable classifications. Authentic distinct `HE_Job*` indicators and element icons are extracted reproducibly from `UI1` into ignored `local/proprietary/ui-icons/`; `Rs_HeJob_*` awakening resources are explicitly excluded. Visible text is the clean-checkout fallback. Star values remain labeled as raw source fields because their exact player-facing semantics are not proven.

## Purpose and current state

This repository now contains the first hero-library vertical slice: CTA-specific importers, normalized SQLite persistence with provenance, validation, a read-only ASP.NET Core API, a React/TypeScript roster/detail UI, synthetic importer tests, and local-development documentation.

The latest local successful import audited here is:

- Import ID: `242a5f85-898a-42e4-8850-2e85f50554de`
- Declared game version: `2.0.821`
- Source: `samples/bluestacks/shared-data/cache/content`
- Parsed inputs: `Heroes.csv`, `Persos.xml`, `Skills.xml`, `Persos_en.xml`, `Skills_en.xml`, `Config.xml`, `Config_en.xml`, and `Items_en.xml`
- Persisted: 1,215 entities, 923 relations, and 733 localizations
- Importer diagnostics: 1,293 informational unmatched artifacts and 104 warnings

The detailed generated audit is `generated/reports/hero-data-audit.md`. It is intentionally ignored by Git. Regenerate it with:

```bash
python3 scripts/audit-hero-data.py \
  extracted/cta.sqlite \
  generated/reports/hero-data-audit.md
```

Important repository rules remain in force: `samples/`, `assets/`, and `extracted/` are read-only local inputs. Put copied, decoded, converted, or application-ready proprietary assets under ignored `local/proprietary/`; prefer them in local builds, but never stage extracted content, generated databases, generated images, or generated reports.

## Executive finding

The database currently labels 127 `Heroes.csv` rows as collectible. That is not yet a trustworthy player-roster count. `Heroes.csv` mixes real heroes, old or unreleased heroes, enemies, temporary combat units, transformations, and summons. The current classifier starts by treating every balance row as collectible and only excludes a few recognizable patterns. Missing-data counts are therefore inflated by non-roster records.

For records that really are player heroes, the core balance import is substantially complete. Every currently classified collectible has class/job, element, sex, tribe, mobility, rarity, max stars, and all ordinary combat stats. The main remaining work is:

1. classify the real roster accurately;
2. extract and map the indexed compact icons;
3. make joins case-insensitive while retaining raw identifiers;
4. improve acquisition semantics;
5. decide how to represent source fields that are genuinely blank rather than inventing values;
6. parse or derive richer skill mechanics and display text.

## Compact hero icons: implemented

The desired small portrait does exist. Previous searches missed it because its frame name does not contain the hero ID.

The native x86_64 library is in `samples/bluestacks/apk/split_config.x86_64.apk` as `lib/x86_64/libMain.so`. It retains symbols including:

- `UnitDesc::GetIconName(int, String&)`
- `UnitDesc::GetIconName(String&) const`
- `UnitDesc::GetIconIdx() const`
- `UnitDesc::GetIconProfile(String&) const`
- `UnitDesc::RenderIcon(...)`

Disassembly of `UnitDesc::GetIconName` reveals the format string:

```text
GMI_{:s}_{:03d}.png
```

The inputs are the element code and `iconIdx` from `Persos.xml`. Element codes are:

| Element | Code |
|---|---|
| Dark | `DA` |
| Earth | `EA` |
| Fire | `FI` |
| Light | `LI` |
| Water | `WA` |

Example: Senshi is Dark with `iconIdx="30"`, so the correct frame is `GMI_DA_030.png`. It was decoded and visually verified as the desired compact Senshi portrait.

The frames live in:

- `assets/UIGuildMemberIcons0.plist` / `.pvrgz`: 144 frames
- `assets/UIGuildMemberIcons1.plist` / `.pvrgz`: 16 frames

They are 162×162. The PVR v2 textures use ETC1 (`flags & 0xff == 0x36`, four bits per pixel), not RGBA4444 and not PVRTC. `texture2ddecoder.decode_etc1` successfully decoded the atlas during investigation; it returns BGRA, so red and blue channels must be swapped before PNG output.

Current coverage is 116/116 playable heroes. Across all 148 `Heroes.csv` rows, 125 resolve to atlas frames and 23 non-playable/legacy/variant rows remain unresolved. Case-insensitive joins resolve `DDSaberDancer`/`DDSaberdancer` and `Pumpking`/`PumpKing`. `CuddlesBerserk` requests absent `GMI_EA_033`; the retained Earth atlas ends at 32. Do not fall back to `HP_<hero>` presentation art or `SK_<skill>` skill icons. If a compact frame cannot be resolved, the UI displays the hero name.

Recommended implementation:

- Portrait entities persist element code, raw `iconIdx`, computed GMI frame, atlas plist/texture, and source provenance.
- `scripts/extract-cta-hero-icons.py` extracts only resolvable GMI references into ignored `local/proprietary/hero-icons` with source hashes and unresolved rows in `provenance.json`.
- The API uses `HeroIconRoot` and returns a URL only when both a persisted portrait reference and canonical-ID PNG exist.
- Synthetic tests cover all five element codes, the second Water atlas, invalid indices, atlas bounds, and read-only API behavior. No game image is committed.

## Classification is the highest-impact correctness gap

Current classification counts are:

| Kind | Count |
|---|---:|
| collectible | 127 |
| enemy | 16 |
| NPC | 2 |
| summoned variant | 2 |
| transformed variant | 1 |

The default reason for collectible is merely “canonical hero balance record.” That is too permissive because `Heroes.csv` is a general unit-balance table.

Nine records marked collectible have neither a current normalized acquisition relation nor any enabled legacy Dungeon/Shop/Event/Epic Chest flag:

`GreenArcher`, `IceGolem`, `MummyGiant`, `Rolexo`, `SkeletonArcher`, `ViForky`, `ViLokt`, `ViRagnar`, `VuTNTbomb`.

Manual evidence from the user also says `Werewolf` is not a hero visible in the game, although its source row, icon, skills, and availability-like flags make it look collectible. Therefore absence of fields is useful negative evidence, but no single CSV flag is sufficient.

High-confidence signals to combine:

- valid `iconIdx` and resolvable GMI frame;
- membership in a current chest/medal group;
- availability flags, while recognizing these differ from player-facing acquisition;
- skin ownership and summon/transformation references;
- `Persos.xml` module-backed/no-assets patterns;
- native unit flags populated into `UnitDesc`;
- whether the native roster/dex routines include the unit.

Useful native symbols for deeper work include `UIUnitDexList::Fill(EChest)`, `UIUnitDex::Enable(bool, EChest)`, `UnitDesc::IsInvokable()`, `UnitDesc::CanBePickedInDungeons()`, `UnitDescManager::FillWithChestUnit(...)`, and `UnitDescManager::PickRandomHeroes(...)`. The binary is not fully stripped, making targeted reverse engineering feasible.

Do not hard-code a roster solely from current manual observations. Persist classification reason/evidence so uncertain, removed, or unreleased units can be reviewed.

## Exact missing-data audit

### Core identity and combat stats

Across all 127 currently classified collectibles:

- Missing class/job: 0
- Missing element: 0
- Missing sex: 0
- Missing tribe: 0
- Missing mobility: 0
- Missing rarity: 0
- Missing max stars: 0
- Missing ATK, HP, DEF, DPS, power, range, reload, move speed, critical chance, critical damage, resistance, or evade: 0
- Missing damage type: 6
- Missing base stars: 2
- Missing `factor_per_star`: 127

The six blank damage types are exactly:

`Blossom`, `ViForky`, `ViLokt`, `ViRagnar`, `VoodooArcher`, `VoodooSpear`.

The source `Heroes.csv` cells are blank, so this is not a parser omission. The Viking records are likely enemy/temporary units. The Voodoo records also omit fourth passives and may be base enemy-family records. Blossom appears to be a real hero and needs either native/runtime derivation or manual confirmation; do not guess `Phys`/`Magic` based only on class.

`BaseStars` is blank in the source for Akuma and Blossom. Every `Factor per Star` cell is blank for this dataset, so `factor_per_star` should be documented as unavailable, removed from the user-facing contract, or derived from confirmed native logic. It should not be treated as 127 independent import failures.

### English hero names

The validator reports 24 missing English localized names, but every one has a non-empty canonical name from `Heroes.csv`. The UI therefore has usable English text.

Breakdown:

- Absent from `Persos_en.xml`, canonical fallback valid: `Athena`, `Auro`, `Avalon`, `Bjorn`, `Blaze`, `Cuddles`, `Havoc`, `IceGolem`, `Purah`, `Rowan`, `Senshi`, `Surtr`, `Volos`.
- Present with deliberately blank English override, canonical fallback valid: `BgnArcher`, `BgnGiant`, `BgnSpear`, `BgnSword`, `SkeletonGiant`, `SkeletonSword`, `VoodooArcher`, `VoodooDagger`, `VoodooSpear`.
- Case-only key mismatch: `DDSaberDancer` → `DDSaberdancer`; `Pumpking` → `PumpKing`.

The validator should distinguish “no usable English name” from “no localization override.” Missing override should be informational when canonical English exists.

### Character joins and unresolved relations

The two missing character/model records are not missing content:

- Hero `DDSaberDancer` matches character `DDSaberdancer`.
- Hero `Pumpking` matches character `PumpKing`.

Normalize joins case-insensitively but retain both raw IDs and record the normalization/provenance. This should recover their three skills and compact icon references.

The only unresolved skill reference is also a case mismatch:

- `Persos.xml` references `MokingFI` for `MoKing`.
- `Skills.xml` defines `MoKingFI`.

Fixing case-insensitive skill resolution should remove both `unresolved_skill_reference` and its related `unresolved_relation_target` warning and restore the localized canonical name `Fire staff Wave` plus the `SkDesc_SP3_SpearWave` description reference.

### Skills and descriptions

Nine records currently have fewer than three resolved visible spells. Several are almost certainly non-roster units. The important cases are:

- `DDSaberDancer`: 0/3 only because of the character key case mismatch.
- `Pumpking`: 0/3 only because of the character key case mismatch.
- `MoKing`: relation is present but one skill target is unresolved because of `MokingFI`/`MoKingFI` casing.
- `ArthusKnight`: only two `<skill>` entries exist in `Persos.xml`; likely legacy/non-roster.
- `IceGolem`, `ViForky`, `ViLokt`, `ViRagnar`, `VuTNTbomb`, and `SkeletonArcher` have incomplete or sparse skill sets and strongly need classification review.

Nine linked skills lack descriptions under the current rules:

- `ArthusSword`
- `FairyKnightShieldSP2`
- `WaterShoot`
- `MoKingFI` (currently reached as `MokingFI`)
- `TNTbomb`
- `ThrowCardSP1`
- `ForkyAxe`
- `LoktAnchor`
- `TNTExplode`

These are not all equivalent gaps:

- `MoKingFI` already contains `SkDesc_SP3_SpearWave`; case-insensitive resolution should recover it.
- Several are basic attacks (`ArthusSword`, `WaterShoot`, `ThrowCardSP1`, `LoktAnchor`, `TNTbomb`) for which `Skills.xml` supplies mechanics but no prose. Generic in-game descriptions may be constructed by type rather than stored per skill.
- `FairyKnightShieldSP2` has cooldown and HP-percent mechanics but no prose.
- `ForkyAxe` and `TNTExplode` lack English names as well and belong to suspected non-roster units.

Do not label every absent prose block as a broken import. Add a description provenance/status such as `localized`, `inline`, `generic_by_type`, or `unavailable`. A future parser can generate conservative type-based text only when native/game behavior is understood; generated text must not masquerade as source localization.

The current UI exposes only a small subset of component mechanics. Richer extraction can include cooldown, hit count, projectile count, radius/splash radius, duration, effect type/value, HP percentages, boost, reload time, and level-specific overrides. Preserve raw component attributes alongside normalized values.

### Traits / innate attributes

Sixteen current collectibles have no `Ability1`–`Ability3` values:

`ArthusKnight`, `GreenFaery`, `IceGolem`, `Manta`, `Merlinus`, `MummyGiant`, `Necromancer`, `Ox`, `Paladin`, `Petunia`, `Rolexo`, `Trickster`, `ViForky`, `ViLokt`, `WaterMage`, `Witch`.

The corresponding `Heroes.csv` cells are blank. Their `Persos.xml` records also do not provide `<ability>` entries that would fill the gap. This is genuine source absence under the files currently parsed, not a parser bug.

Some are likely non-roster records, but several are real heroes. Possible explanations are that these heroes legitimately have no innate attributes, attributes are derived from skill effects, or a separate/native configuration supplies them. The API/UI should say “No innate attributes found in source data,” not imply the hero definitely has none.

### Fourth passives

Twenty-three rows have blank `SP4`, target, and value in `Heroes.csv`:

`ArthusKnight`, `BgnArcher`, `BgnGiant`, `BgnSpear`, `BgnSword`, `GreenArcher`, `LightKnight`, `SkeletonArcher`, `SkeletonArcherCaptain`, `SkeletonGiant`, `SkeletonSword`, `Spike`, `Swift`, `ViForky`, `ViLokt`, `ViRagnar`, `VoodooArcher`, `VoodooDagger`, `VoodooSpear`, `VuArcher`, `VuHammer`, `VuSword`, `VuTNTbomb`.

Most cluster into obvious enemy/base-unit families. This supports fixing classification before attempting to manufacture missing passives.

Three additional heroes have an SP4 code/value but no generated description because they are not ordinary Buff/Debuff forms:

- `FireKnight`: `Frenzy`, Fire, value 3
- `Red`: `FrenzyForEachBurnAbility`, Self, value 0.5
- `Rowan`: `Frenzy`, Earth, value 3

These require dedicated semantics from localization/native behavior rather than the current generic passive formatter.

### Acquisition versus legacy availability

These concepts must remain separate:

- `Heroes.csv` has legacy/UI flags: Dungeon, Shop, Event, ChestEpic.
- `Config.xml` chest groups provide explicit medal/hero acquisition relationships.
- The native game also calculates dynamic chest/shop/event eligibility.

Current coverage among the 127 records:

- 63 have some explicit chest relation.
- 55 have at least one explicit current relation.
- Eight are only in `ChestHeroesPast`: `Bjorn`, `Lapina`, `MetalRat`, `MoKing`, `MonkiMerry`, `Ra`, `Red`, `Thor`.
- 118 have at least one enabled legacy availability flag.
- 63 rely on legacy flags because they have no current explicit relation.
- Nine have neither: `GreenArcher`, `IceGolem`, `MummyGiant`, `Rolexo`, `SkeletonArcher`, `ViForky`, `ViLokt`, `ViRagnar`, `VuTNTbomb`.

The API currently falls back from explicit acquisition to legacy flags. Keep that fallback visible as lower-confidence provenance rather than presenting both as the same source. The user has manually confirmed that UI “Availability” and medal acquisition sometimes differ, and that Blossom is obtainable from Legendary Chest. Chest-group parsing should remain the authoritative source where available.

Useful native functions for deeper acquisition work include `Profile::FindChestConfigGroup`, `Profile::FillChestWithConfig`, `UnitDesc_PickMedalsHero`, `UnitDescManager::PickRandomHeroes`, `UnitDescManager::FillWithChestUnit`, `OfferManager::FindOrCreatePastChest`, and `UIUnitDexList::Fill`.

### Availability nulls

`ChestEpic` is blank rather than explicitly false for 28 rows. The parser correctly preserves this as null. Do not silently convert null to false without confirming game semantics. Dungeon, Shop, and Event are present for all 127 rows.

### Portrait diagnostics

The validator reports 12 missing portrait references. This matches the 10 no-`iconIdx` candidates plus the two case-mismatched hero/character IDs. After case-insensitive joins, only the ten likely legacy/non-roster records should remain unresolved. Update validation to validate the computed GMI frame, not merely the existence of a generic `portrait` entity.

## Importer diagnostic interpretation

Current warnings:

| Code | Count | Interpretation |
|---|---:|---|
| `missing_localization_key` | 88 | Mix of harmless missing overrides, genuinely absent skill names, and case-sensitive joins; severity/rules need refinement. |
| `missing_portrait_reference` | 10 | Source rows with no generic portrait reference. |
| `missing_compact_portrait_reference` | 12 | Non-playable/legacy/variant rows with no usable compact icon input. |
| `invalid_compact_portrait_reference` | 1 | `CuddlesBerserk` requests absent Earth index 33. |
| `unresolved_relation_target` | 3 | `DDSaberDancer`, `Pumpking`, and `MokingFI`; all have case-insensitive targets. |
| `unresolved_skill_reference` | 1 | `MokingFI` → `MoKingFI` case mismatch. |

The 1,293 `unmatched_artifact` informational diagnostics mostly represent animations, texture atlases, effects, and other files outside current parsers. They should not be presented as 1,293 hero-data errors. Future parsers should explicitly claim only relevant artifacts; consider summarizing unmatched artifacts by extension/category rather than one diagnostic per file.

## Recommended next sequence

1. Add case-insensitive entity/relation resolution with raw-ID retention. Re-import and verify the three unresolved relations disappear.
2. Preserve the implemented ETC1 GMI extractor and provenance-aware portrait mapping; current playable coverage is 116/116.
3. Replace the permissive collectible classifier with evidence-based classification and an `uncertain`/`unreleased` state. Explicitly verify `Werewolf` and the ten no-icon records.
4. Separate normalized acquisition relations from legacy availability fallbacks in API contracts and filters.
5. Refine localization validation so canonical English fallbacks are accepted and blank override entries are not treated as missing usable content.
6. Add description provenance and normalize richer skill mechanics. Fix `MoKingFI` first; avoid invented prose for source-blank basic attacks.
7. Investigate native `UnitDesc` initialization and roster/dex filtering only for fields still unexplained after steps 1–6.
8. Use runtime BlueStacks checks only for unresolved player-facing behavior. Per project instructions, provide Windows PowerShell commands using BlueStacks `HD-Adb.exe`, wait for the user to run them, and never use Linux adb.

## Verification commands

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v

PYTHONPATH=src python3 -m cta_importer import \
  samples/bluestacks/shared-data/cache/content \
  extracted/cta.sqlite \
  --game-id com.godzilab.idlerpg \
  --version 2.0.821

python3 scripts/audit-hero-data.py \
  extracted/cta.sqlite \
  generated/reports/hero-data-audit.md

Database=extracted/cta.sqlite \
  dotnet run --project api/Cta.Api --urls http://localhost:5080

npm run dev --prefix web/cta-web
```

After an importer parser-version change, the import should not reuse the old dataset. If it unexpectedly reports `reused: true`, verify the affected parser descriptor version was incremented.

## Known local-development behavior

- Database paths are resolved from the repository root; starting the API from `api/Cta.Api` should not break a repository-relative `Database` setting.
- The API intentionally ignores old large `generated/portraits` artwork. Authentic job/element files are served read-only from `local/proprietary/ui-icons` via `UiIconRoot`; all playable compact hero icons are served from `local/proprietary/hero-icons` via `HeroIconRoot`.
- The UI shows the full hero name when no compact icon resolves.
- Large `HP_*` presentation art and `SK_*` skill icons must not be used as hero-card fallbacks.
- `Human`, `Viking`, and similar tribe/style values were removed from player-facing roster labels because they are internal source classifications not shown in the game UI.

## Manual facts supplied by the user

Treat these as useful cross-checks, not replacements for source provenance:

- `Werewolf` is not a hero visible in the game.
- Blossom is obtained from Legendary Chest.
- Cuddles is Epic, Barbarian, Earth, Ground, Male; base masteries ATK 50, HP 800, DEF 30; skills Carrot Strike, Carrotquake, Carrot Smash, and Earth-team HP/ATK/DEF buff; attributes include Berserk, Anti Knock-Back, and Life Steal.
- The user supplied additional names/descriptions for Kasumi, Surtr, Blaze, Avalon, Havoc, Pinky, Green Faery, Purah, Trickster, Manta, and Shelly in prior conversation. Prefer game-file recovery and record manual confirmation separately when source text is genuinely absent.

## Worktree caution

The worktree contains extensive uncommitted implementation from this vertical slice. Preserve unrelated/user changes. Before any commit, inspect `git status` and staged files carefully. Never stage proprietary extracted assets, APKs, SQLite databases, generated icons, or generated reports.
# Deployment handoff

The deployable architecture and exact owner actions are documented in `docs/deployment.md`. Normal CI never extracts data or receives the production database. A local, review-gated Pattern C release builds the exact API image that is pushed and deployed.
