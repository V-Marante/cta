# Hero stat and source-calculation semantics audit

This current follow-up covers the 116 playable heroes in CTA 2.0.821.

## Conclusions

| Source field | Presentation | Unit/meaning | Evidence |
|---|---|---|---|
| `Atk` | ATK | Base attack damage, source points | Direct English hero-stat help |
| `HP` | HP | Capacity to withstand damage, source points | Direct English hero-stat help |
| `Def` | DEF | Incoming-damage reduction parameter; formula/unit unresolved | Direct meaning, unresolved numeric formula |
| `AtkRange` | Attack range | Distance before an attack can begin; internal distance units | Direct meaning, unresolved physical unit |
| `AtkReload` | Attack interval | Base interval used by attack-per-second calculation; internal time units | Strongly supported by native getters and DPS relation |
| `MoveSpeed` | Move speed | Base travel speed; internal speed units | Direct English hero-stat help |
| `Ctk` | Critical rate | Percent chance of a critical hit | Direct English and `%` formatting evidence |
| `CtkDmg` | Critical damage | Percent extra critical-hit damage | Direct English and `%` formatting evidence |
| `Resistance` | Effect resistance | Percent chance to resist a status effect | Direct English help/tip evidence |
| `Evade` | Dodge | Percent chance to evade an incoming attack | Direct English and parameterized `%` evidence |
| `DPS` | Derived base DPS | Conventional half-up rounding of `Atk / AtkReload`; excludes skills, criticals, buffs, and account progression | Exact corpus relation plus native `GetAtkPerSec` |
| `POW` | Raw POW | Unresolved source score, not current hero/account power | Runtime power functions depend on level/stars and other systems |

Zero is a real value, not missing. Null represents absence. In the playable set all twelve primary source stats are populated; Dodge is legitimately zero for 103 heroes. The API retains numeric zero and the frontend renders it (including `0%`).

## Spreadsheet/design columns

`Atk w/ stars`, `HP w/ stars`, `POW / Stars`, and `Factor per Star` remain separately persisted as unresolved `source_calculations`. They are not mixed into the base combat display:

- `Atk w/ stars`: zero for 112 playable heroes, nonzero for 4.
- `HP w/ stars`: zero for 110, nonzero for 6.
- `POW / Stars`: nonzero for all 116 but contradicted by extreme editor-like outliers and lacks a proven runtime/UI definition.
- `Factor per Star`: null for all 116 playable heroes (one non-playable source row contains 2).

The former frontend heading “Masteries” was rejected: these are base/source hero values, not the separate mastery system represented by `MasteryManager`, Paragon data, and mastery UI symbols.

## Reproduction

```bash
PYTHONPATH=src python3 -m cta_importer import samples/bluestacks/shared-data/cache/content extracted/cta.sqlite --game-id com.godzilab.idlerpg --version 2.0.821
PYTHONPATH=src python3 scripts/audit-hero-stats.py extracted/cta.sqlite extracted/hero-stat-audit.md --game-id com.godzilab.idlerpg
```

Generated audit output remains ignored.
