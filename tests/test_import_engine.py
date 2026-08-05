from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cta_importer.contracts import ParseContext, ParserDescriptor
from cta_importer.engine import ImportEngine, ImportRequest
from cta_importer.model import (
    Diagnostic,
    EntityRecord,
    LocalizationRecord,
    ParseResult,
    Severity,
    SourceArtifact,
    SourceLocation,
    VersionInfo,
)
from cta_importer.persistence import SQLiteRepository
from cta_importer.registry import ParserRegistry


class DemoParser:
    descriptor = ParserDescriptor("test.demo", "1.0.0", 1)

    def accepts(self, context: ParseContext, artifact: SourceArtifact) -> bool:
        return artifact.relative_path.endswith(".demo")

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        key, value = artifact.read_text().strip().split("=", 1)
        return ParseResult(
            entities=(EntityRecord("demo", key, {"value": value}, source=SourceLocation(path=artifact.relative_path)),)
        )


class DuplicateLocalizationParser(DemoParser):
    descriptor = ParserDescriptor("test.duplicate_localization", "1.0.0", 1)

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        base = super().parse(context, artifact)
        item = LocalizationRecord("demo", "alpha", "en", "name", "Alpha")
        return ParseResult(entities=base.entities, localizations=(item, item))


class ExplodingParser(DemoParser):
    descriptor = ParserDescriptor("test.exploding", "1.0.0", 1)

    def parse(self, context: ParseContext, artifact: SourceArtifact) -> ParseResult:
        raise RuntimeError("synthetic parser failure")


class RejectingValidator:
    validator_id = "test.reject"

    def validate(self, dataset):
        return (Diagnostic(Severity.ERROR, "synthetic_rejection", "rejected by test"),)


class ImportEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "one.demo").write_text("alpha=one", encoding="utf-8")
        self.repository = SQLiteRepository(self.root / "imports.sqlite")
        self.repository.migrate()
        self.version = VersionInfo("test-game", "1.2.3", build="123")

    def tearDown(self) -> None:
        self.repository.close()
        self.temp.cleanup()

    def test_success_is_atomic_and_idempotent(self) -> None:
        engine = ImportEngine(self.repository, ParserRegistry([DemoParser()]))
        first = engine.import_source(ImportRequest(self.source, version=self.version))
        second = engine.import_source(ImportRequest(self.source, version=self.version))

        self.assertEqual(first.status, "succeeded")
        self.assertEqual(self.repository.count("entities", first.import_id), 1)
        self.assertTrue(second.reused)
        self.assertEqual(second.import_id, first.import_id)

    def test_same_files_with_different_game_version_are_separate_imports(self) -> None:
        engine = ImportEngine(self.repository, ParserRegistry([DemoParser()]))
        first = engine.import_source(ImportRequest(self.source, version=self.version))
        second = engine.import_source(
            ImportRequest(self.source, version=VersionInfo("test-game", "1.2.4", build="124"))
        )
        self.assertFalse(second.reused)
        self.assertNotEqual(second.import_id, first.import_id)

    def test_validation_rejection_persists_diagnostics_not_data(self) -> None:
        from cta_importer.registry import ValidatorRegistry

        engine = ImportEngine(
            self.repository,
            ParserRegistry([DemoParser()]),
            ValidatorRegistry([RejectingValidator()]),
        )
        result = engine.import_source(ImportRequest(self.source, version=self.version))
        self.assertEqual(result.status, "rejected")
        self.assertEqual(self.repository.count("entities", result.import_id), 0)
        self.assertGreater(self.repository.count("diagnostics", result.import_id), 0)

    def test_parser_exception_marks_failed(self) -> None:
        result = ImportEngine(self.repository, ParserRegistry([ExplodingParser()])).import_source(
            ImportRequest(self.source, version=self.version)
        )
        self.assertEqual(result.status, "failed")
        self.assertEqual(self.repository.count("entities", result.import_id), 0)

    def test_persistence_error_rolls_back_all_dataset_rows(self) -> None:
        result = ImportEngine(self.repository, ParserRegistry([DuplicateLocalizationParser()])).import_source(
            ImportRequest(self.source, version=self.version)
        )
        self.assertEqual(result.status, "failed")
        self.assertEqual(self.repository.count("entities", result.import_id), 0)
        self.assertEqual(self.repository.count("localizations", result.import_id), 0)
        self.assertGreater(self.repository.count("diagnostics", result.import_id), 0)


if __name__ == "__main__":
    unittest.main()
