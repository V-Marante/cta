#!/usr/bin/env python3
"""Extract CTA compact hero portraits from local BlueStacks APK atlases."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import plistlib
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from cta_atlas import Image, crop, numbers, png, pvr_v2

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))
from cta_importer.cta.portraits import portrait_reference  # noqa: E402


ATLASES = ("UIGuildMemberIcons0", "UIGuildMemberIcons1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path, help="read-only CTA base.apk")
    parser.add_argument("content", type=Path, help="read-only materialized cache/content directory")
    parser.add_argument("output", type=Path, help="ignored local/proprietary/hero-icons directory")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_etc1_pvr(payload: bytes) -> Image:
    try:
        import texture2ddecoder
    except ImportError as error:
        raise SystemExit("texture2ddecoder is required; install the pinned asset extra with: python3 -m pip install '.[assets]'") from error
    width, height, pixel_type, data = pvr_v2(payload)
    if pixel_type != 0x36:
        raise ValueError(f"expected ETC1 pixel type 0x36, found 0x{pixel_type:02x}")
    bgra = texture2ddecoder.decode_etc1(data, width, height)
    if len(bgra) != width * height * 4:
        raise ValueError("ETC1 decoder returned an unexpected byte count")
    rgba = bytearray(bgra)
    for offset in range(0, len(rgba), 4):
        rgba[offset], rgba[offset + 2] = rgba[offset + 2], rgba[offset]
    return Image(width, height, bytes(rgba))


def main() -> int:
    args = parse_args()
    heroes_path, characters_path = args.content / "Heroes.csv", args.content / "Persos.xml"
    for path in (args.apk, heroes_path, characters_path):
        if not path.is_file():
            raise SystemExit(f"source not found: {path}")
    rows = list(csv.DictReader(heroes_path.read_text(encoding="utf-8-sig").splitlines()))
    characters = {(node.get("key") or "").lower(): node for node in ET.parse(characters_path).getroot().findall("character")}
    args.output.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "sources": {
            str(args.apk): sha256(args.apk),
            str(heroes_path): sha256(heroes_path),
            str(characters_path): sha256(characters_path),
        },
        "icons": {},
        "unresolved": [],
    }
    with zipfile.ZipFile(args.apk) as archive:
        atlases: dict[str, tuple[Image, dict[str, object]]] = {}
        for atlas_name in ATLASES:
            plist_path, texture_path = f"assets/{atlas_name}.plist", f"assets/{atlas_name}.pvrgz"
            metadata = plistlib.loads(archive.read(plist_path))
            texture = decode_etc1_pvr(gzip.decompress(archive.read(texture_path)))
            if numbers(str(metadata["metadata"]["size"]))[0] != (texture.width, texture.height):
                raise ValueError(f"{atlas_name} plist and texture dimensions disagree")
            atlases[atlas_name] = texture, metadata["frames"]
        for row in rows:
            hero_id = (row.get("Key") or "").strip()
            character = characters.get(hero_id.lower())
            icon_index = character.get("iconIdx") if character is not None else None
            reference = portrait_reference(row.get("Elemental"), icon_index)
            if reference is None:
                manifest["unresolved"].append({"hero_id": hero_id, "element": row.get("Elemental"), "icon_index": icon_index})
                continue
            texture, frames = atlases[reference.atlas_name]
            frame = frames.get(reference.frame_name)
            if frame is None:
                manifest["unresolved"].append({"hero_id": hero_id, "element": row.get("Elemental"),
                    "icon_index": icon_index, "frame": reference.frame_name})
                continue
            icon = crop(texture, frame)
            if (icon.width, icon.height) != (162, 162):
                raise ValueError(f"{reference.frame_name} has unexpected size {icon.width}x{icon.height}")
            filename = f"{hero_id}.png"
            (args.output / filename).write_bytes(png(icon))
            manifest["icons"][hero_id] = {"file": filename, "frame": reference.frame_name,
                "atlas": reference.atlas_name, "plist_entry": reference.plist_entry,
                "texture_entry": reference.texture_entry, "icon_index": reference.icon_index,
                "element_code": reference.element_code}
    (args.output / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(manifest['icons'])} compact hero icons; {len(manifest['unresolved'])} source rows unresolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
