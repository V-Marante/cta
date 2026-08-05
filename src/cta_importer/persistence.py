from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Iterable, Iterator

from .model import Diagnostic, ParsedArtifact, SourceArtifact, VersionInfo


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sql_statements(script: str) -> Iterator[str]:
    buffer = ""
    for line in script.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statement = buffer.strip()
            if statement:
                yield statement
            buffer = ""
    if buffer.strip():
        raise RuntimeError("incomplete SQL migration statement")


@dataclass(frozen=True, slots=True)
class RunRow:
    import_id: str
    status: str


class SQLiteRepository:
    """SQLite persistence boundary with migration and transaction ownership."""

    def __init__(self, path: Path, *, busy_timeout_ms: int = 30_000) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = NORMAL")

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SQLiteRepository":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextmanager
    def transaction(self, mode: str = "IMMEDIATE") -> Iterator[sqlite3.Connection]:
        self.connection.execute(f"BEGIN {mode}")
        try:
            yield self.connection
        except BaseException:
            self.connection.execute("ROLLBACK")
            raise
        else:
            self.connection.execute("COMMIT")

    def migrate(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        migration_root = files("cta_importer.migrations")
        for resource in sorted(migration_root.iterdir(), key=lambda item: item.name):
            if not resource.name.endswith(".sql"):
                continue
            sql = resource.read_text(encoding="utf-8")
            checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
            row = self.connection.execute(
                "SELECT checksum FROM schema_migrations WHERE version = ?", (resource.name,)
            ).fetchone()
            if row:
                if row["checksum"] != checksum:
                    raise RuntimeError(f"applied migration checksum changed: {resource.name}")
                continue
            with self.transaction("EXCLUSIVE"):
                for statement in _sql_statements(sql):
                    self.connection.execute(statement)
                self.connection.execute(
                    "INSERT INTO schema_migrations(version, checksum, applied_at) VALUES (?, ?, ?)",
                    (resource.name, checksum, _now()),
                )

    def find_successful(self, version: VersionInfo, source_digest: str, parser_set_digest: str) -> str | None:
        row = self.connection.execute(
            """SELECT id FROM import_runs
               WHERE game_id = ? AND game_version = ? AND build IS ? AND content_version IS ?
                 AND source_digest = ? AND parser_set_digest = ? AND status = 'succeeded'""",
            (
                version.game_id,
                version.version,
                version.build,
                version.content_version,
                source_digest,
                parser_set_digest,
            ),
        ).fetchone()
        return row["id"] if row else None

    def start_run(
        self,
        version: VersionInfo,
        source_root: Path,
        source_digest: str,
        parser_set_digest: str,
    ) -> str:
        import_id = str(uuid.uuid4())
        self.connection.execute(
            """INSERT INTO import_runs(
                   id, game_id, game_version, build, content_version, source_digest,
                   parser_set_digest, source_root, status, started_at, version_metadata_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running', ?, ?)""",
            (
                import_id,
                version.game_id,
                version.version,
                version.build,
                version.content_version,
                source_digest,
                parser_set_digest,
                str(source_root),
                _now(),
                _json(version.metadata),
            ),
        )
        return import_id

    def commit_success(
        self,
        import_id: str,
        artifacts: Iterable[SourceArtifact],
        parsed: Iterable[ParsedArtifact],
        diagnostics: Iterable[Diagnostic],
    ) -> None:
        parsed_items = tuple(parsed)
        parser_by_path = {item.artifact.relative_path: item.parser_id for item in parsed_items}
        with self.transaction():
            self._insert_artifacts(import_id, artifacts, parser_by_path)
            for item in parsed_items:
                self._insert_parse_result(import_id, item)
            self._insert_diagnostics(import_id, diagnostics)
            self.connection.execute(
                "UPDATE import_runs SET status = 'succeeded', finished_at = ? WHERE id = ?",
                (_now(), import_id),
            )

    def finish_without_data(
        self,
        import_id: str,
        status: str,
        artifacts: Iterable[SourceArtifact],
        diagnostics: Iterable[Diagnostic],
        error_message: str | None = None,
    ) -> None:
        if status not in {"failed", "rejected"}:
            raise ValueError(f"invalid terminal status: {status}")
        with self.transaction():
            self._insert_artifacts(import_id, artifacts, {})
            self._insert_diagnostics(import_id, diagnostics)
            self.connection.execute(
                "UPDATE import_runs SET status = ?, finished_at = ?, error_message = ? WHERE id = ?",
                (status, _now(), error_message, import_id),
            )

    def _insert_artifacts(
        self, import_id: str, artifacts: Iterable[SourceArtifact], parser_by_path: dict[str, str]
    ) -> None:
        self.connection.executemany(
            """INSERT INTO artifacts(import_id, relative_path, byte_size, sha256, media_type, parser_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                (
                    import_id,
                    item.relative_path,
                    item.size,
                    item.sha256,
                    item.media_type,
                    parser_by_path.get(item.relative_path),
                )
                for item in artifacts
            ),
        )

    def _insert_parse_result(self, import_id: str, parsed: ParsedArtifact) -> None:
        result = parsed.result
        self.connection.execute(
            """INSERT INTO parser_executions(
                   import_id, artifact_path, parser_id, parser_version, output_schema_version,
                   status, entity_count, relation_count, localization_count
               ) VALUES (?, ?, ?, ?, ?, 'succeeded', ?, ?, ?)""",
            (
                import_id,
                parsed.artifact.relative_path,
                parsed.parser_id,
                parsed.parser_version,
                parsed.output_schema_version,
                len(result.entities),
                len(result.relations),
                len(result.localizations),
            ),
        )
        for item in result.entities:
            location = item.source
            self.connection.execute(
                """INSERT INTO entities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    import_id, parsed.parser_id, parsed.output_schema_version, item.namespace,
                    item.key, item.ordinal, _json(item.payload), location.path,
                    location.line, location.column, location.record,
                ),
            )
        for item in result.relations:
            location = item.source
            self.connection.execute(
                """INSERT INTO relations(
                       import_id, parser_id, output_schema_version, relation, source_namespace,
                       source_key, target_namespace, target_key, ordinal, payload_json,
                       source_path, source_line, source_column, source_record
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    import_id, parsed.parser_id, parsed.output_schema_version, item.relation,
                    item.source_namespace, item.source_key, item.target_namespace, item.target_key,
                    item.ordinal, _json(item.payload), location.path, location.line,
                    location.column, location.record,
                ),
            )
        for item in result.localizations:
            location = item.source
            self.connection.execute(
                """INSERT INTO localizations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    import_id, parsed.parser_id, parsed.output_schema_version, item.namespace,
                    item.key, item.locale, item.field, item.value, location.path,
                    location.line, location.column, location.record,
                ),
            )

    def _insert_diagnostics(self, import_id: str, diagnostics: Iterable[Diagnostic]) -> None:
        self.connection.executemany(
            """INSERT INTO diagnostics(
                   import_id, severity, code, message, parser_id, source_path, source_line,
                   source_column, source_record, details_json
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                (
                    import_id, item.severity.value, item.code, item.message, item.parser_id,
                    item.location.path, item.location.line, item.location.column,
                    item.location.record, _json(item.details),
                )
                for item in diagnostics
            ),
        )

    def run_status(self, import_id: str) -> sqlite3.Row | None:
        return self.connection.execute("SELECT * FROM import_runs WHERE id = ?", (import_id,)).fetchone()

    def count(self, table: str, import_id: str) -> int:
        if table not in {"artifacts", "entities", "relations", "localizations", "diagnostics", "parser_executions"}:
            raise ValueError(f"unsupported table: {table}")
        row = self.connection.execute(f"SELECT count(*) AS n FROM {table} WHERE import_id = ?", (import_id,)).fetchone()
        return int(row["n"])
