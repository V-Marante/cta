# Report status

Start with [`19-bluestacks-reconciliation.md`](19-bluestacks-reconciliation.md) for extraction state and [`20-hero-progression-semantics-audit.md`](20-hero-progression-semantics-audit.md) for current hero progression/acquisition meaning.

The report series is chronological, not a set of equally current instructions:

| Reports | Status | Use |
|---|---|---|
| `01`–`07` | Historical Google Play Games investigation | Provenance only; access limitations and next steps are superseded |
| `08`–`16` | Historical Google Play Games follow-up | Provenance only; do not retry the disk-image or Linux ADB paths |
| `17` | Current BlueStacks extraction baseline | Authoritative for the retained APKs and shared runtime cache |
| `18` | Current design reference | Schema snapshot based on the BlueStacks corpus; verify counts when the game version changes |
| `19` | Current reconciliation | Source selection, resolved limitations, known gaps, and next retrieval targets |
| `20` | Current semantic audit | Hero stars, rarity, explicit acquisition, and legacy availability |
| `21` | Current stat audit | Hero stat labels, units, DPS derivation, and unresolved source calculations |
| `22` | Current skill/passive audit | Numeric units, placeholder resolution, passive targeting, and unresolved cases |
| `23` | Current localization closure | Missing-description evidence and accessible CTA token rendering |
| `24` | Current release-readiness audit | API contract, accessibility, local performance, exception register, and asset-mode smoke results |
| `25` | Current source reconciliation | Public-version verification, exact retained-source hashes, same-version import/audit results, and refresh trigger |

The current repository corpus was obtained from BlueStacks through its Windows `HD-Adb.exe`. Android interaction must use that route and must be performed by the user from Windows PowerShell. Do not use Linux ADB.

BlueStacks `2.0.821` is the current authoritative version. On 2026-08-06 BlueStacks offered no update, the launched package reported `versionCode=200821`, and current public Google Play metadata independently identified 2.0.821/200821. Older Google Play Games logs contain a `2.0.822` string, but no current public listing or retained package corroborates it as a released build. Treat it only as unexplained historical raw evidence. See report 25.

Generated JSON/text inspection output is ignored and is not current documentation. Markdown reports are human-reviewed records; extracted APKs, game content, databases, inventories, and decoded assets remain local-only.
