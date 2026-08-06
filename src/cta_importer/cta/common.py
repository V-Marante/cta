from __future__ import annotations

from ..model import SourceArtifact, SourceLocation


def location(artifact: SourceArtifact, record: str) -> SourceLocation:
    return SourceLocation(path=artifact.relative_path, record=record)


def scalar(value: str | None):
    if value is None or not value.strip():
        return None
    value = value.strip()
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def flag(value: str | None) -> bool | None:
    if value is None or not value.strip():
        return None
    return value.strip().lower() in {"1", "x", "true", "yes"}
