#!/usr/bin/env python3
"""Validate and summarize JSON, XML, CSV/TSV, and ZIP-like files."""

from __future__ import annotations

import argparse
import csv
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


def summarize_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return {"format": "json", "top_level": "object", "keys": sorted(map(str, data.keys()))[:50]}
    if isinstance(data, list):
        return {"format": "json", "top_level": "array", "length": len(data), "first_type": type(data[0]).__name__ if data else None}
    return {"format": "json", "top_level": type(data).__name__}


def summarize_xml(path: Path) -> dict:
    root = ET.parse(path).getroot()
    children = {}
    for child in list(root)[:100]:
        children[child.tag] = children.get(child.tag, 0) + 1
    return {"format": "xml", "root": root.tag, "attributes": sorted(root.attrib.keys()), "child_tag_counts_sample": children}


def summarize_csv(path: Path, delimiter: str) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        rows = []
        for _, row in zip(range(11), reader):
            rows.append(row)
    return {"format": "tsv" if delimiter == "\t" else "csv", "sample_rows": rows, "sample_row_count": len(rows)}


def summarize_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        return {
            "format": "zip-compatible",
            "entry_count": len(infos),
            "entries_sample": [
                {"name": item.filename, "size": item.file_size, "compressed_size": item.compress_size}
                for item in infos[:100]
            ],
        }


def summarize(path: Path) -> dict:
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            return summarize_json(path)
        if suffix == ".xml":
            return summarize_xml(path)
        if suffix == ".csv":
            return summarize_csv(path, ",")
        if suffix == ".tsv":
            return summarize_csv(path, "\t")
        if suffix in {".zip", ".apk", ".apks", ".xapk"} or zipfile.is_zipfile(path):
            return summarize_zip(path)
        return {"format": "unsupported_by_this_script"}
    except Exception as exc:
        return {"format": "error", "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = [{"path": raw, **summarize(Path(raw))} for raw in args.files]
    Path(args.output).write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
