from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from typing import Iterable

from .model import SourceArtifact


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def discover(root: Path, ignored_names: Iterable[str] = ()) -> tuple[SourceArtifact, ...]:
    root = root.resolve(strict=True)
    ignored = set(ignored_names)
    artifacts = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name not in ignored):
        relative = path.relative_to(root).as_posix()
        artifacts.append(
            SourceArtifact(
                root=root,
                relative_path=relative,
                size=path.stat().st_size,
                sha256=_sha256(path),
                media_type=mimetypes.guess_type(path.name)[0],
            )
        )
    return tuple(artifacts)


def source_digest(artifacts: Iterable[SourceArtifact]) -> str:
    digest = hashlib.sha256()
    for artifact in sorted(artifacts, key=lambda item: item.relative_path):
        digest.update(artifact.relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(artifact.size).encode("ascii"))
        digest.update(b"\0")
        digest.update(artifact.sha256.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()
