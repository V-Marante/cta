# Phase 3: Image Copy

> **Obsolete path — do not retry.** BlueStacks package-scoped retrieval removed the need to copy the Google Play Games sparse disk image. See `reports/19-bluestacks-reconciliation.md`.

## Status

`userdata.img` was not copied successfully.

The user reported that Google Play Games and `crosvm.exe` were turned off. Windows process inspection is still unavailable from WSL, so this is user-confirmed rather than independently verified by `Get-Process`.

## Original Image Metadata

Path:

```text
C:\Users\<windows-user>\AppData\Local\Google\Play Games\userdata_<instance>.gz5\avd\userdata.img
```

WSL path:

```text
/mnt/c/Users/<windows-user>/AppData/Local/Google/Play Games/userdata_<instance>.gz5/avd/userdata.img
```

Metadata gathered with Linux `stat` and `du`:

| File | Logical size | Allocated size by `du` | Last modified |
|---|---:|---:|---|
| `userdata.img` | 85,899,345,920 bytes | about 4.0 GiB | 2026-08-05 10:11:36 +0200 |
| `metadata.img` | 16,777,216 bytes | about 8.3 MiB | 2026-08-05 09:15:16 +0200 |
| `misc.img` | 16,384 bytes | about 64 KiB | 2026-08-05 09:14:23 +0200 |

After the user stopped Google Play Games, the observed `userdata.img` and `metadata.img` modification timestamps changed to approximately 2026-08-05 10:43 +0200.

Free space observed before the copy attempt:

- WSL workspace filesystem: about 833 GiB free
- Windows `C:` volume: about 37 GiB free

After the failed attempt, Windows `C:` reported 0 free space via WSL `df`, while `du` still showed the original `userdata.img` as about 4.0 GiB allocated. This may be a Windows/WSL sparse-file accounting or volume-space condition, but it was not modified or investigated further.

## Sparse Allocation

The image appears sparse: logical size is 80 GiB, while allocated size is about 4.0 GiB. A copy that does not preserve sparseness could require roughly 80 GiB at the destination.

## Copy Attempt

Command run:

```bash
cp --sparse=always --reflink=auto \
  /mnt/c/Users/<windows-user>/AppData/Local/Google/'Play Games'/userdata_<instance>.gz5/avd/userdata.img \
  samples/images/userdata.img
```

Result:

```text
cp: error reading '/mnt/c/Users/<windows-user>/AppData/Local/Google/Play Games/userdata_<instance>.gz5/avd/userdata.img': Input/output error
```

The partial output was renamed to:

```text
samples/images/userdata.img.partial
```

Partial output metadata:

- logical size: 54,362,382,336 bytes
- allocated size: about 3.0 GiB
- status: invalid partial copy, not inspected, not mounted, not hashed as a complete image

If retrying from Linux after resolving the input/output error, the same sparse-preserving copy pattern is still appropriate:

```bash
cp --sparse=always --reflink=auto \
  /mnt/c/Users/<windows-user>/AppData/Local/Google/'Play Games'/userdata_<instance>.gz5/avd/userdata.img \
  samples/images/userdata.img
```

After a successful complete copy, hash both source and copy before inspection:

```bash
sha256sum /mnt/c/Users/<windows-user>/AppData/Local/Google/'Play Games'/userdata_<instance>.gz5/avd/userdata.img
sha256sum samples/images/userdata.img
```

## Safety Confirmation

VM stopped: user-confirmed, not independently verified.

Because the image copy failed and only a partial copy exists, all further image work was stopped.
