from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(frozen=True, slots=True)
class SourceLocation:
    path: str | None = None
    line: int | None = None
    column: int | None = None
    record: str | None = None


@dataclass(frozen=True, slots=True)
class Diagnostic:
    severity: Severity
    code: str
    message: str
    parser_id: str | None = None
    location: SourceLocation = field(default_factory=SourceLocation)
    details: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VersionInfo:
    game_id: str
    version: str
    build: str | None = None
    content_version: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SourceArtifact:
    root: Path
    relative_path: str
    size: int
    sha256: str
    media_type: str | None = None

    @property
    def path(self) -> Path:
        return self.root / self.relative_path

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()

    def read_text(self, encoding: str = "utf-8-sig") -> str:
        return self.path.read_text(encoding=encoding)


@dataclass(frozen=True, slots=True)
class EntityRecord:
    namespace: str
    key: str
    payload: Mapping[str, JsonValue]
    ordinal: int = 0
    source: SourceLocation = field(default_factory=SourceLocation)


@dataclass(frozen=True, slots=True)
class RelationRecord:
    relation: str
    source_namespace: str
    source_key: str
    target_namespace: str
    target_key: str
    payload: Mapping[str, JsonValue] = field(default_factory=dict)
    ordinal: int = 0
    source: SourceLocation = field(default_factory=SourceLocation)


@dataclass(frozen=True, slots=True)
class LocalizationRecord:
    namespace: str
    key: str
    locale: str
    field: str
    value: str
    source: SourceLocation = field(default_factory=SourceLocation)


@dataclass(frozen=True, slots=True)
class ParseResult:
    entities: tuple[EntityRecord, ...] = ()
    relations: tuple[RelationRecord, ...] = ()
    localizations: tuple[LocalizationRecord, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class ImportDataset:
    version: VersionInfo
    entities: tuple[EntityRecord, ...]
    relations: tuple[RelationRecord, ...]
    localizations: tuple[LocalizationRecord, ...]
    diagnostics: tuple[Diagnostic, ...]


@dataclass(frozen=True, slots=True)
class ParsedArtifact:
    artifact: SourceArtifact
    parser_id: str
    parser_version: str
    output_schema_version: int
    result: ParseResult
