#!/usr/bin/env python3
"""Extract provenance-backed CTA job and element icons from a local base APK."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import plistlib
import struct
import zipfile
from pathlib import Path

from cta_atlas import Image, crop, numbers, png, pvr_v2

ELEMENTS = {
    "dark": ("UI1", "Elt_DA.png"),
    "earth": ("UI1", "Elt_EA.png"),
    "fire": ("UI1", "Elt_FI.png"),
    "light": ("UI1", "Elt_LI.png"),
    "water": ("UI1", "Elt_WA.png"),
}
JOBS = {
    "barbarian": ("UI1", "HE_JobBarbarian.png"),
    "brawler": ("UI1", "HE_JobFighter.png"),
    "gunner": ("UI1", "HE_JobGunner.png"),
    "knight": ("UI1", "HE_JobKnight.png"),
    "lancer": ("UI1", "HE_JobLancer.png"),
    "magician": ("UI1", "HE_JobMagician.png"),
    "ranger": ("UI1", "HE_JobRanger.png"),
    "rogue": ("UI1", "HE_JobRogue.png"),
    "samurai": ("UI1", "HE_JobSamurai.png"),
    "support": ("UI1", "HE_JobSupport.png"),
}
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path, help="read-only CTA base.apk")
    parser.add_argument("output", type=Path, help="ignored local/proprietary/ui-icons directory")
    return parser.parse_args()


def decode_pvr(payload: bytes) -> Image:
    width, height, pixel_type, data = pvr_v2(payload)
    if pixel_type == 0x12:  # RGBA8888, masks in the PVR header establish byte order.
        expected = width * height * 4
        if len(data) != expected:
            raise ValueError(f"RGBA8888 length {len(data)} does not match {expected}")
        rgba = data
    elif pixel_type == 0x10:  # RGBA4444, little-endian according to header masks.
        expected = width * height * 2
        if len(data) != expected:
            raise ValueError(f"RGBA4444 length {len(data)} does not match {expected}")
        rgba = bytearray(width * height * 4)
        for index, value in enumerate(struct.iter_unpack("<H", data)):
            pixel = value[0]
            rgba[index * 4 : index * 4 + 4] = bytes(
                (((pixel >> 12) & 0xF) * 17, ((pixel >> 8) & 0xF) * 17,
                 ((pixel >> 4) & 0xF) * 17, ((pixel >> 0) & 0xF) * 17)
            )
        rgba = bytes(rgba)
    else:
        raise ValueError(f"unsupported PVR v2 pixel type 0x{pixel_type:02x}")
    return Image(width, height, rgba)


def main() -> int:
    args = parse_args()
    if not args.apk.is_file():
        raise SystemExit(f"APK not found: {args.apk}")
    args.output.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "source": str(args.apk),
        "source_sha256": hashlib.sha256(args.apk.read_bytes()).hexdigest(),
        "icons": {},
    }
    with zipfile.ZipFile(args.apk) as archive:
        atlases: dict[str, tuple[Image, dict[str, object]]] = {}
        for atlas in sorted({value[0] for value in (*ELEMENTS.values(), *JOBS.values())}):
            plist_path = f"assets/{atlas}.plist"
            texture_path = f"assets/{atlas}.pvrgz"
            metadata = plistlib.loads(archive.read(plist_path))
            texture = decode_pvr(gzip.decompress(archive.read(texture_path)))
            expected_size = numbers(str(metadata["metadata"]["size"]))[0]
            if expected_size != (texture.width, texture.height):
                raise ValueError(f"{atlas} plist size {expected_size} does not match PVR size {(texture.width, texture.height)}")
            atlases[atlas] = texture, metadata["frames"]
        for category, definitions in (("elements", ELEMENTS), ("jobs", JOBS)):
            directory = args.output / category
            directory.mkdir(parents=True, exist_ok=True)
            for name, (atlas, frame_name) in definitions.items():
                texture, frames = atlases[atlas]
                icon = crop(texture, frames[frame_name])
                relative = Path(category) / f"{name}.png"
                (args.output / relative).write_bytes(png(icon))
                manifest["icons"][str(relative)] = {
                    "apk_entry": f"assets/{atlas}.pvrgz",
                    "plist_entry": f"assets/{atlas}.plist",
                    "frame": frame_name,
                    "width": icon.width,
                    "height": icon.height,
                }
    (args.output / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(manifest['icons'])} authentic icons to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
