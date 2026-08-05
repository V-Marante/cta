from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence, runtime_checkable

from .model import Diagnostic, ImportDataset, ParseResult, SourceArtifact, VersionInfo


@dataclass(frozen=True, slots=True)
class ParserDescriptor:
    parser_id: str
    parser_version: str
    output_schema_version: int
    priority: int = 0


@dataclass(frozen=True, slots=True)
class ParseContext:
    version: VersionInfo
    source_root: Path


@runtime_checkable
class Parser(Protocol):
    @property
    def descriptor(self) -> ParserDescriptor: ...

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool: ...

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult: ...


@runtime_checkable
class Validator(Protocol):
    @property
    def validator_id(self) -> str: ...

    def validate(self, dataset: ImportDataset) -> Sequence[Diagnostic]: ...


@runtime_checkable
class VersionResolver(Protocol):
    def resolve(self, source_root: Path) -> VersionInfo: ...
