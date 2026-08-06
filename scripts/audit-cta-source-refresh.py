#!/usr/bin/env python3
"""Reconcile a retained BlueStacks CTA pull without modifying source inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


PACKAGE = "com.godzilab.idlerpg"
CANONICAL = ("Heroes.csv", "Persos.xml", "Skills.xml", "Items.xml", "Config.xml", "Config_en.xml")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Retained samples/bluestacks directory")
    parser.add_argument("output", type=Path, help="Ignored JSON output path")
    args = parser.parse_args()

    apk_root = args.root / "apk"
    log_root = args.root / "logs"
    shared_root = args.root / "shared-data"
    content_root = shared_root / "cache" / "content"
    patch_root = shared_root / "cache" / "patch"

    dump = (log_root / f"{PACKAGE}.dumpsys-package.txt").read_text(encoding="utf-8-sig")
    version_name = re.search(r"versionName=([^\s]+)", dump)
    version_code = re.search(r"versionCode=(\d+)", dump)

    recorded = {}
    for line in (log_root / f"{PACKAGE}.apk-sha256.txt").read_text(encoding="utf-8-sig").splitlines():
        if match := re.match(r"([0-9a-fA-F]{64})\s+(.+)", line.strip()):
            recorded[Path(match.group(2)).name] = match.group(1).lower()
    apk_rows = []
    for path in sorted(apk_root.glob("*.apk")):
        actual = digest(path)
        apk_rows.append({"name": path.name, "size": path.stat().st_size, "sha256": actual,
                         "recorded_sha256": recorded.get(path.name), "matches_record": actual == recorded.get(path.name)})

    prefix = f"/sdcard/Android/data/{PACKAGE}/"
    listed = {
        line.removeprefix(prefix)
        for line in (log_root / f"{PACKAGE}.shared-files.txt").read_text(encoding="utf-8-sig").splitlines()
        if line.startswith(prefix)
    }
    materialized = {
        path.relative_to(shared_root).as_posix()
        for path in shared_root.rglob("*") if path.is_file()
    }

    patches = []
    patch_members: dict[str, list[tuple[str, str]]] = {}
    for path in sorted(patch_root.glob("*.bin")):
        with zipfile.ZipFile(path) as archive:
            members = []
            for info in archive.infolist():
                if info.is_dir():
                    continue
                members.append((info.filename, hashlib.sha256(archive.read(info)).hexdigest()))
            patch_members[path.name] = members
            patches.append({"name": path.name, "size": path.stat().st_size, "sha256": digest(path),
                            "member_count": len(members), "first_member": members[0][0] if members else None,
                            "last_member": members[-1][0] if members else None})

    canonical = []
    for name in CANONICAL:
        source = content_root / name
        source_hash = digest(source) if source.is_file() else None
        matches = [bundle for bundle, members in patch_members.items()
                   if any(Path(member).name == name and member_hash == source_hash for member, member_hash in members)]
        canonical.append({"name": name, "present": source.is_file(), "size": source.stat().st_size if source.is_file() else None,
                          "sha256": source_hash, "matching_patch_bundles": matches})

    result = {
        "package": PACKAGE,
        "version_name": version_name.group(1) if version_name else None,
        "version_code": int(version_code.group(1)) if version_code else None,
        "apk_files": apk_rows,
        "apk_hashes_match_record": bool(apk_rows) and all(row["matches_record"] for row in apk_rows),
        "shared_listing_count": len(listed),
        "materialized_shared_count": len(materialized),
        "listed_but_missing": sorted(listed - materialized),
        "materialized_but_unlisted": sorted(materialized - listed),
        "patch_bundles": patches,
        "canonical_sources": canonical,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "version": f"{result['version_name']} ({result['version_code']})",
        "apks": len(apk_rows),
        "apk_hashes_match": result["apk_hashes_match_record"],
        "listed_shared_files": len(listed),
        "missing_shared_files": len(result["listed_but_missing"]),
        "extra_shared_files": len(result["materialized_but_unlisted"]),
        "patches": len(patches),
        "canonical_sources": len(canonical),
        "output": str(args.output),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
