from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .contracts import ParseContext, VersionResolver
from .discovery import discover, source_digest
from .model import Diagnostic, ImportDataset, ParsedArtifact, Severity, SourceLocation, VersionInfo
from .persistence import SQLiteRepository
from .registry import ParserRegistry, RegistryError, ValidatorRegistry
from .validation import CoreValidator, blocks_commit


@dataclass(frozen=True, slots=True)
class ImportRequest:
    source_root: Path
    version: VersionInfo | None = None
    version_resolver: VersionResolver | None = None
    fail_on: Severity = Severity.ERROR
    require_all_artifacts: bool = False


@dataclass(frozen=True, slots=True)
class ImportResult:
    import_id: str
    status: str
    reused: bool
    artifact_count: int
    parsed_artifact_count: int
    entity_count: int
    relation_count: int
    localization_count: int
    diagnostics: tuple[Diagnostic, ...]


class ImportEngine:
    def __init__(
        self,
        repository: SQLiteRepository,
        parsers: ParserRegistry,
        validators: ValidatorRegistry | None = None,
    ) -> None:
        self.repository = repository
        self.parsers = parsers
        self.validators = validators or ValidatorRegistry()

    def import_source(self, request: ImportRequest) -> ImportResult:
        root = request.source_root.resolve(strict=True)
        version = self._resolve_version(request, root)
        artifacts = discover(root)
        digest = source_digest(artifacts)
        parser_digest = self._parser_set_digest()
        prior = self.repository.find_successful(version, digest, parser_digest)
        if prior:
            return ImportResult(prior, "succeeded", True, len(artifacts), 0, 0, 0, 0, ())

        import_id = self.repository.start_run(version, root, digest, parser_digest)
        diagnostics: list[Diagnostic] = []
        parsed: list[ParsedArtifact] = []
        context = ParseContext(version=version, source_root=root)
        try:
            for artifact in artifacts:
                try:
                    parser = self.parsers.select(context, artifact)
                except RegistryError as exc:
                    diagnostics.append(
                        Diagnostic(Severity.FATAL, "ambiguous_parser", str(exc), location=SourceLocation(path=artifact.relative_path))
                    )
                    continue
                if parser is None:
                    severity = Severity.ERROR if request.require_all_artifacts else Severity.INFO
                    diagnostics.append(
                        Diagnostic(severity, "unmatched_artifact", "no parser accepted artifact", location=SourceLocation(path=artifact.relative_path))
                    )
                    continue
                descriptor = parser.descriptor
                try:
                    result = parser.parse(context, artifact)
                except Exception as exc:
                    diagnostics.append(
                        Diagnostic(
                            Severity.FATAL,
                            "parser_exception",
                            f"{type(exc).__name__}: {exc}",
                            parser_id=descriptor.parser_id,
                            location=SourceLocation(path=artifact.relative_path),
                        )
                    )
                    continue
                diagnostics.extend(result.diagnostics)
                parsed.append(
                    ParsedArtifact(
                        artifact=artifact,
                        parser_id=descriptor.parser_id,
                        parser_version=descriptor.parser_version,
                        output_schema_version=descriptor.output_schema_version,
                        result=result,
                    )
                )

            dataset = ImportDataset(
                version=version,
                entities=tuple(entity for item in parsed for entity in item.result.entities),
                relations=tuple(relation for item in parsed for relation in item.result.relations),
                localizations=tuple(localization for item in parsed for localization in item.result.localizations),
                diagnostics=tuple(diagnostics),
            )
            validators = (CoreValidator(), *self.validators.validators())
            for validator in validators:
                diagnostics.extend(validator.validate(dataset))

            if blocks_commit(tuple(diagnostics), request.fail_on):
                status = "failed" if any(item.code in {"parser_exception", "import_exception"} for item in diagnostics) else "rejected"
                self.repository.finish_without_data(import_id, status, artifacts, diagnostics)
                return self._result(import_id, status, artifacts, parsed, diagnostics)

            self.repository.commit_success(import_id, artifacts, parsed, diagnostics)
            return self._result(import_id, "succeeded", artifacts, parsed, diagnostics)
        except Exception as exc:
            failure = Diagnostic(Severity.FATAL, "import_exception", f"{type(exc).__name__}: {exc}")
            diagnostics.append(failure)
            self.repository.finish_without_data(import_id, "failed", artifacts, diagnostics, str(exc))
            return self._result(import_id, "failed", artifacts, (), diagnostics)

    def _resolve_version(self, request: ImportRequest, root: Path) -> VersionInfo:
        if request.version and request.version_resolver:
            raise ValueError("provide version or version_resolver, not both")
        if request.version:
            return request.version
        if request.version_resolver:
            return request.version_resolver.resolve(root)
        raise ValueError("version metadata or a version resolver is required")

    def _parser_set_digest(self) -> str:
        descriptors = [
            {
                "id": item.descriptor.parser_id,
                "version": item.descriptor.parser_version,
                "schema": item.descriptor.output_schema_version,
                "priority": item.descriptor.priority,
            }
            for item in self.parsers.parser_set()
        ]
        value = json.dumps(descriptors, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(value).hexdigest()

    @staticmethod
    def _result(import_id: str, status: str, artifacts: tuple, parsed: tuple | list, diagnostics: list[Diagnostic]) -> ImportResult:
        return ImportResult(
            import_id=import_id,
            status=status,
            reused=False,
            artifact_count=len(artifacts),
            parsed_artifact_count=len(parsed),
            entity_count=sum(len(item.result.entities) for item in parsed),
            relation_count=sum(len(item.result.relations) for item in parsed),
            localization_count=sum(len(item.result.localizations) for item in parsed),
            diagnostics=tuple(diagnostics),
        )
