# Phase 4: Image Format

> **Obsolete path.** Disk-image format analysis is no longer a prerequisite because BlueStacks provided package-scoped files. See `reports/19-bluestacks-reconciliation.md`.

## Status

Not performed.

Reason: `samples/images/userdata.img` does not exist as a complete verified copy. A sparse copy attempt failed with an input/output error and left `samples/images/userdata.img.partial`, which was not inspected because it is incomplete.

## Available Linux Tools

Installed and available:

- `file`
- `fdisk`
- `blkid`
- `debugfs`
- `unzip`
- `adb`
- `aapt2`

Not available in this session:

- `parted`
- `qemu-img`
- `7z`
- `guestfish`
- `simg2img`

## Planned Commands After Safe Copy

Once a complete `samples/images/userdata.img` exists, inspect the copy only:

```bash
file samples/images/userdata.img
fdisk -l samples/images/userdata.img
blkid -p samples/images/userdata.img
xxd -l 4096 samples/images/userdata.img
```

Do not mount or convert in place. If Android sparse conversion is needed, create a derived file under `working/images/`.
