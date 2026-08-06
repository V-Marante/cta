## BlueStacks

This project uses BlueStacks.

Whenever Android interaction is required:

- Generate PowerShell commands.
- Wait for the user to execute them.
- Continue from the returned output.

Do not use Linux adb.
Use Windows PowerShell and BlueStacks' HD-Adb.exe.

## Repository hygiene

- Never stage or commit extracted game files.
- Treat `samples/`, `assets/`, and `extracted/` as read-only local inputs.
- Prefer authentic in-game data and assets over approximations whenever they are available locally and their provenance can be established.
- Put every copied, decoded, converted, or application-ready proprietary asset under `local/proprietary/`. Organize it by purpose, for example `local/proprietary/hero-icons/` and `local/proprietary/ui-icons/`.
- `local/proprietary/` is local runtime material: tools and applications may generate and read it, but tests and clean-checkout workflows must continue to work without it by using fallbacks or synthetic fixtures.
- Do not weaken `.gitignore` merely to make a test pass.
- Test fixtures must be minimal, synthetic where possible, and explicitly reviewed before committing.
- Generated SQLite files and generated reports must not be committed.
- Migrations, parser source, validation code, tests, and human-written design documents should be committed.
- Before every commit, inspect `git status`, the staged file list, and `git check-ignore local/proprietary/`; ensure no proprietary binary or extracted data is staged.
