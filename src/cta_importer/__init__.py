"""Extensible, versioned game-data import infrastructure."""

from .contracts import Parser, Validator, VersionResolver
from .engine import ImportEngine, ImportRequest, ImportResult
from .model import Diagnostic, EntityRecord, RelationRecord, Severity, VersionInfo
from .persistence import SQLiteRepository
from .registry import ParserRegistry, ValidatorRegistry

__all__ = [
    "Diagnostic",
    "EntityRecord",
    "ImportEngine",
    "ImportRequest",
    "ImportResult",
    "Parser",
    "ParserRegistry",
    "RelationRecord",
    "SQLiteRepository",
    "Severity",
    "Validator",
    "ValidatorRegistry",
    "VersionInfo",
    "VersionResolver",
]
