from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import ImportEngine, ImportRequest
from .model import Severity, VersionInfo
from .persistence import SQLiteRepository
from .registry import ParserRegistry
from .registry import ValidatorRegistry
from .cta import HeroLibraryValidator, cta_parsers


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Versioned game-data importer")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-db", help="create or migrate an importer database")
    init.add_argument("database", type=Path)

    plugins = sub.add_parser("list-parsers", help="list installed parser plugins")

    run = sub.add_parser("import", help="import a source tree using installed parser plugins")
    run.add_argument("source", type=Path)
    run.add_argument("database", type=Path)
    run.add_argument("--game-id", required=True)
    run.add_argument("--version", required=True)
    run.add_argument("--build")
    run.add_argument("--content-version")
    run.add_argument("--require-all-artifacts", action="store_true")
    run.add_argument("--fail-on", choices=[item.value for item in Severity], default=Severity.ERROR.value)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "init-db":
        with SQLiteRepository(args.database) as repository:
            repository.migrate()
        print(f"database ready: {args.database}")
        return 0

    registry = ParserRegistry(cta_parsers())
    registry.load_entry_points()
    if args.command == "list-parsers":
        for parser in registry.parser_set():
            descriptor = parser.descriptor
            print(f"{descriptor.parser_id}\t{descriptor.parser_version}\tschema={descriptor.output_schema_version}\tpriority={descriptor.priority}")
        return 0

    version = VersionInfo(
        game_id=args.game_id,
        version=args.version,
        build=args.build,
        content_version=args.content_version,
    )
    with SQLiteRepository(args.database) as repository:
        repository.migrate()
        result = ImportEngine(repository, registry, ValidatorRegistry([HeroLibraryValidator()])).import_source(
            ImportRequest(
                source_root=args.source,
                version=version,
                fail_on=Severity(args.fail_on),
                require_all_artifacts=args.require_all_artifacts,
            )
        )
    print(json.dumps({
        "import_id": result.import_id,
        "status": result.status,
        "reused": result.reused,
        "artifacts": result.artifact_count,
        "parsed_artifacts": result.parsed_artifact_count,
        "entities": result.entity_count,
        "relations": result.relation_count,
        "localizations": result.localization_count,
        "diagnostics": len(result.diagnostics),
    }, indent=2))
    return 0 if result.status == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
