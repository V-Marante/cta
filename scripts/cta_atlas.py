"""Small dependency-free image/crop/PNG primitives for CTA atlas extractors."""

from __future__ import annotations

import re
import struct
import zlib
from dataclasses import dataclass


PAIR = re.compile(r"\{(-?\d+),(-?\d+)\}")


@dataclass(frozen=True)
class Image:
    width: int
    height: int
    rgba: bytes


def pvr_v2(payload: bytes) -> tuple[int, int, int, bytes]:
    if len(payload) < 52:
        raise ValueError("PVR payload is shorter than its v2 header")
    header = struct.unpack_from("<13I", payload)
    header_size, height, width, _, flags, data_size = header[:6]
    if header_size != 52 or header[11] != 0x21525650:
        raise ValueError("expected a PVR v2 texture")
    data = payload[header_size : header_size + data_size]
    if len(data) != data_size:
        raise ValueError(f"PVR data length {len(data)} does not match header {data_size}")
    return width, height, flags & 0xFF, data


def numbers(value: str) -> list[tuple[int, int]]:
    return [(int(x), int(y)) for x, y in PAIR.findall(value)]


def crop(image: Image, frame: dict[str, object]) -> Image:
    (x, y), (width, height) = numbers(str(frame["frame"]))
    rotated = bool(frame.get("rotated", False))
    source_width, source_height = numbers(str(frame["sourceSize"]))[0]
    (source_x, source_y), (trim_width, trim_height) = numbers(str(frame["sourceColorRect"]))
    packed_width, packed_height = (height, width) if rotated else (width, height)
    if x < 0 or y < 0 or x + packed_width > image.width or y + packed_height > image.height:
        raise ValueError(f"frame outside {image.width}x{image.height} atlas")
    packed = bytearray(packed_width * packed_height * 4)
    for row in range(packed_height):
        start = ((y + row) * image.width + x) * 4
        packed[row * packed_width * 4 : (row + 1) * packed_width * 4] = image.rgba[start : start + packed_width * 4]
    if rotated:
        unrotated = bytearray(width * height * 4)
        for row in range(height):
            for column in range(width):
                source = (column * packed_width + (packed_width - 1 - row)) * 4
                target = (row * width + column) * 4
                unrotated[target : target + 4] = packed[source : source + 4]
        packed = unrotated
    if (trim_width, trim_height) != (width, height):
        raise ValueError("plist frame and sourceColorRect dimensions disagree")
    canvas = bytearray(source_width * source_height * 4)
    for row in range(height):
        source = row * width * 4
        target = ((source_y + row) * source_width + source_x) * 4
        canvas[target : target + width * 4] = packed[source : source + width * 4]
    return Image(source_width, source_height, bytes(canvas))


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def png(image: Image) -> bytes:
    rows = b"".join(b"\0" + image.rgba[row * image.width * 4 : (row + 1) * image.width * 4] for row in range(image.height))
    return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", image.width, image.height, 8, 6, 0, 0, 0))
            + png_chunk(b"IDAT", zlib.compress(rows, 9)) + png_chunk(b"IEND", b""))
