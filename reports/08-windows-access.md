# Phase 1: Windows Access From WSL

> **Historical environment note.** Current Android interaction uses user-executed Windows PowerShell and BlueStacks' `HD-Adb.exe`; these WSL interop failures are not extraction blockers. See `reports/19-bluestacks-reconciliation.md`.

## Prior Artifact Review

Before this phase, the existing reports and inventories were read:

- `README.md`
- `reports/01-identifiers.md`
- `reports/02-file-inventory.md`
- `reports/03-engine-detection.md`
- `reports/04-initial-inspection.md`
- `reports/05-runtime-assets.md`
- `reports/06-prioritized-sources.md`
- `reports/07-final-summary.md`
- `inventories/files.csv`
- `inventories/files.json`

## PowerShell Discovery

Commands run:

```bash
command -v powershell.exe
command -v pwsh.exe
ls -l /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
printf '%s\n' "$PATH"
```

Results:

- `powershell.exe` was not on the WSL `PATH`.
- `pwsh.exe` was not on the WSL `PATH`.
- Windows PowerShell exists at:
  - `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`
- Current WSL `PATH` contains Linux/Nix paths only and no Windows system directories.

Attempted explicit invocation:

```bash
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "$PSVersionTable.PSVersion.ToString()"
```

Result:

```text
WSL ERROR: UtilConnectUnix:535: connect failed 1
WSL ERROR: UtilBindVsockAnyPort:309: socket failed 1
```

After the user explicitly allowed PowerShell use, Windows executable interop was retried with elevated command execution:

```bash
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "..."
/mnt/c/Windows/System32/cmd.exe /c ver
```

Result:

```text
Invalid argument
```

## Conclusion

The prior failure did not mean the Windows PowerShell executable was missing. The executable is present, but Windows executable interop from this WSL environment is currently failing. Per user instruction for this phase continuation, the rest of the work used Linux ecosystem tools where possible.

## Consequence

The following Windows-only checks could not be performed from this session:

- `Get-Process client, Service, crosvm`
- Windows process path/module/open-handle inspection
- Windows `Get-NetTCPConnection`
- Windows `Get-FileHash`
- Windows sparse-file allocation APIs

This directly affects image safety: this session cannot independently confirm that Windows `crosvm.exe` is stopped.
