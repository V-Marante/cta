CREATE TABLE import_runs (
    id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    game_version TEXT NOT NULL,
    build TEXT,
    content_version TEXT,
    source_digest TEXT NOT NULL,
    parser_set_digest TEXT NOT NULL,
    source_root TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed', 'rejected')),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    version_metadata_json TEXT NOT NULL,
    error_message TEXT
);

CREATE UNIQUE INDEX uq_successful_import
ON import_runs(
    game_id,
    game_version,
    ifnull(build, ''),
    ifnull(content_version, ''),
    source_digest,
    parser_set_digest
)
WHERE status = 'succeeded';

CREATE TABLE parser_executions (
    import_id TEXT NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    artifact_path TEXT NOT NULL,
    parser_id TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    output_schema_version INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('succeeded', 'failed')),
    entity_count INTEGER NOT NULL DEFAULT 0,
    relation_count INTEGER NOT NULL DEFAULT 0,
    localization_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (import_id, artifact_path)
);

CREATE TABLE artifacts (
    import_id TEXT NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    relative_path TEXT NOT NULL,
    byte_size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    media_type TEXT,
    parser_id TEXT,
    PRIMARY KEY (import_id, relative_path)
);

CREATE TABLE entities (
    import_id TEXT NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    parser_id TEXT NOT NULL,
    output_schema_version INTEGER NOT NULL,
    namespace TEXT NOT NULL,
    entity_key TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    source_path TEXT,
    source_line INTEGER,
    source_column INTEGER,
    source_record TEXT,
    PRIMARY KEY (import_id, namespace, entity_key)
);

CREATE INDEX ix_entities_lookup ON entities(namespace, entity_key, import_id);

CREATE TABLE relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id TEXT NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    parser_id TEXT NOT NULL,
    output_schema_version INTEGER NOT NULL,
    relation TEXT NOT NULL,
    source_namespace TEXT NOT NULL,
    source_key TEXT NOT NULL,
    target_namespace TEXT NOT NULL,
    target_key TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    source_path TEXT,
    source_line INTEGER,
    source_column INTEGER,
    source_record TEXT
);

CREATE INDEX ix_relations_source ON relations(import_id, source_namespace, source_key);
CREATE INDEX ix_relations_target ON relations(import_id, target_namespace, target_key);

CREATE TABLE localizations (
    import_id TEXT NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    parser_id TEXT NOT NULL,
    output_schema_version INTEGER NOT NULL,
    namespace TEXT NOT NULL,
    entity_key TEXT NOT NULL,
    locale TEXT NOT NULL,
    field TEXT NOT NULL,
    value TEXT NOT NULL,
    source_path TEXT,
    source_line INTEGER,
    source_column INTEGER,
    source_record TEXT,
    PRIMARY KEY (import_id, namespace, entity_key, locale, field)
);

CREATE TABLE diagnostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id TEXT NOT NULL REFERENCES import_runs(id) ON DELETE CASCADE,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'fatal')),
    code TEXT NOT NULL,
    message TEXT NOT NULL,
    parser_id TEXT,
    source_path TEXT,
    source_line INTEGER,
    source_column INTEGER,
    source_record TEXT,
    details_json TEXT NOT NULL
);

CREATE INDEX ix_diagnostics_import_severity ON diagnostics(import_id, severity);
