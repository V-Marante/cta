# Report status

Start with [`19-bluestacks-reconciliation.md`](19-bluestacks-reconciliation.md). It is the current extraction-source reconciliation and the authority for which older findings remain actionable.

The report series is chronological, not a set of equally current instructions:

| Reports | Status | Use |
|---|---|---|
| `01`–`07` | Historical Google Play Games investigation | Provenance only; access limitations and next steps are superseded |
| `08`–`16` | Historical Google Play Games follow-up | Provenance only; do not retry the disk-image or Linux ADB paths |
| `17` | Current BlueStacks extraction baseline | Authoritative for the retained APKs and shared runtime cache |
| `18` | Current design reference | Schema snapshot based on the BlueStacks corpus; verify counts when the game version changes |
| `19` | Current reconciliation | Source selection, resolved limitations, known gaps, and next retrieval targets |

The current repository corpus was obtained from BlueStacks through its Windows `HD-Adb.exe`. Android interaction must use that route and must be performed by the user from Windows PowerShell. Do not use Linux ADB.

BlueStacks `2.0.821` is the newest version currently obtainable from the installed BlueStacks distribution as verified on 2026-08-06: BlueStacks offered no game update, the game launched successfully, and `dumpsys package` reported `versionCode=200821`. Older Google Play Games logs mention `2.0.822`; treat that as distribution-specific historical evidence, not proof that the current BlueStacks corpus is outdated or that `2.0.822` is currently available.

Generated JSON/text inspection output is ignored and is not current documentation. Markdown reports are human-reviewed records; extracted APKs, game content, databases, inventories, and decoded assets remain local-only.
