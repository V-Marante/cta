from __future__ import annotations

from collections import Counter

from .model import Diagnostic, ImportDataset, Severity, SourceLocation


class CoreValidator:
    validator_id = "core.integrity"

    def validate(self, dataset: ImportDataset) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []
        entity_keys = [(item.namespace, item.key) for item in dataset.entities]
        for key, count in Counter(entity_keys).items():
            if count > 1:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        code="duplicate_entity_key",
                        message=f"duplicate entity key {key[0]}:{key[1]} ({count} records)",
                    )
                )

        known = set(entity_keys)
        for relation in dataset.relations:
            if (relation.source_namespace, relation.source_key) not in known:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARNING,
                        code="unresolved_relation_source",
                        message=f"relation source does not resolve: {relation.source_namespace}:{relation.source_key}",
                        location=relation.source,
                    )
                )
            if (relation.target_namespace, relation.target_key) not in known:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARNING,
                        code="unresolved_relation_target",
                        message=f"relation target does not resolve: {relation.target_namespace}:{relation.target_key}",
                        location=relation.source,
                    )
                )

        for item in dataset.entities:
            if not item.namespace.strip() or not item.key.strip():
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        code="empty_entity_identity",
                        message="entity namespace and key must be non-empty",
                        location=item.source,
                    )
                )
        return tuple(diagnostics)


def blocks_commit(diagnostics: tuple[Diagnostic, ...], fail_on: Severity) -> bool:
    rank = {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2, Severity.FATAL: 3}
    threshold = rank[fail_on]
    return any(rank[item.severity] >= threshold for item in diagnostics)
