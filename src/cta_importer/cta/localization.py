from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ..contracts import ParseContext, ParserDescriptor
from ..model import LocalizationRecord, ParseResult, SourceArtifact
from .common import location


class EnglishLocalizationParser:
    descriptor = ParserDescriptor("cta.localization.en", "1.3.0", 1, priority=100)
    _pattern = re.compile(r"^(Persos|Skills)_en\.xml$", re.IGNORECASE)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        name = Path(artifact.relative_path).name
        return bool(self._pattern.match(name)) or name in {"Config_en.xml", "Items_en.xml"}

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        root = ET.fromstring(artifact.read_bytes())
        name = Path(artifact.relative_path).name
        if name == "Items_en.xml":
            records = [LocalizationRecord("acquisition_source", key, "en", "name", value, location(artifact, key))
                for node in root.findall("item") if (key := (node.get("key") or "").strip()).startswith("Chest")
                and (value := (node.get("name") or "").strip())]
            return ParseResult(localizations=tuple(records))
        if name == "Config_en.xml":
            records: list[LocalizationRecord] = []
            for group_name, namespace in (("AbilityInfo", "ability"), ("SkDesc", "skill_description")):
                group = root.find(f"./group[@name='{group_name}']")
                if group is None:
                    continue
                for node in group.findall("value"):
                    key, value = (node.get("name") or "").strip(), (node.text or "").strip()
                    if key and value:
                        records.append(LocalizationRecord(namespace, key, "en", "description", value, location(artifact, f"{group_name}/{key}")))
            for node in root.findall("./value"):
                key, value = (node.get("name") or "").strip(), (node.text or "").strip()
                if key.startswith("SkDesc_") and value:
                    records.append(LocalizationRecord("skill_description", key[7:], "en", "description", value, location(artifact, key)))
            return ParseResult(localizations=tuple(records))
        namespace = "hero" if name.lower().startswith("persos_") else "skill"
        records: list[LocalizationRecord] = []
        for node in list(root):
            key = (node.get("key") or "").strip()
            if not key:
                continue
            source = location(artifact, key)
            if value := (node.get("name") or "").strip():
                records.append(LocalizationRecord(namespace, key, "en", "name", value, source))
            info = node.find("info")
            if info is not None and info.text and info.text.strip():
                records.append(LocalizationRecord(namespace, key, "en", "description", info.text.strip(), source))
        return ParseResult(localizations=tuple(records))
