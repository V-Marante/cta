from __future__ import annotations

from importlib.metadata import entry_points
from typing import Iterable

from .contracts import ParseContext, Parser, Validator
from .model import SourceArtifact


class RegistryError(ValueError):
    pass


class ParserRegistry:
    ENTRY_POINT_GROUP = "cta_importer.parsers"

    def __init__(self, parsers: Iterable[Parser] = ()) -> None:
        self._parsers: dict[str, Parser] = {}
        for parser in parsers:
            self.register(parser)

    def register(self, parser: Parser) -> None:
        parser_id = parser.descriptor.parser_id
        if parser_id in self._parsers:
            raise RegistryError(f"duplicate parser id: {parser_id}")
        self._parsers[parser_id] = parser

    def load_entry_points(self) -> None:
        for entry_point in entry_points(group=self.ENTRY_POINT_GROUP):
            plugin = entry_point.load()
            self.register(plugin() if isinstance(plugin, type) else plugin)

    def select(self, context: ParseContext, artifact: SourceArtifact) -> Parser | None:
        matches = [parser for parser in self._parsers.values() if parser.accepts(context, artifact)]
        if not matches:
            return None
        matches.sort(key=lambda item: item.descriptor.priority, reverse=True)
        if len(matches) > 1 and matches[0].descriptor.priority == matches[1].descriptor.priority:
            ids = ", ".join(item.descriptor.parser_id for item in matches if item.descriptor.priority == matches[0].descriptor.priority)
            raise RegistryError(f"ambiguous parsers for {artifact.relative_path}: {ids}")
        return matches[0]

    def parser_set(self) -> tuple[Parser, ...]:
        return tuple(sorted(self._parsers.values(), key=lambda item: item.descriptor.parser_id))


class ValidatorRegistry:
    def __init__(self, validators: Iterable[Validator] = ()) -> None:
        self._validators: dict[str, Validator] = {}
        for validator in validators:
            self.register(validator)

    def register(self, validator: Validator) -> None:
        if validator.validator_id in self._validators:
            raise RegistryError(f"duplicate validator id: {validator.validator_id}")
        self._validators[validator.validator_id] = validator

    def validators(self) -> tuple[Validator, ...]:
        return tuple(self._validators[key] for key in sorted(self._validators))
