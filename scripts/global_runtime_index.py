#!/usr/bin/env python3
"""Build and query GRDR's external, rebuildable cross-source Runtime index."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Any, Iterable, Iterator

from grdr_paths import (
    global_index_file,
    global_index_manifest_file,
    registry_root,
)


INDEX_SCHEMA_VERSION = "1.0.0"
MANIFEST_SCHEMA_VERSION = "1.0.0"
INDEXED_ENTITY_TYPES = (
    "institutions",
    "sources",
    "datasets",
    "data_structures",
    "resources",
    "data_elements",
    "variables",
    "constructs",
    "semantic_nodes",
)
CENTRAL_COLLECTIONS = {
    entity_type: f"{entity_type}.jsonl" for entity_type in INDEXED_ENTITY_TYPES
}
VERIFICATION_RANK = {
    "verified": 0,
    "partially_verified": 1,
    "stale": 2,
    "conflicted": 3,
    "unverified": 4,
    "deprecated": 5,
    "unavailable": 6,
    "unknown": 7,
}
SUMMARY_FIELDS = {
    "institutions": (
        "id", "name", "aliases", "institution_types", "jurisdiction",
        "canonical_url", "verification",
    ),
    "sources": (
        "id", "name", "aliases", "canonical_url", "maintainer_ids",
        "description", "scope", "source_classes", "authority", "access",
        "verification",
    ),
    "datasets": (
        "id", "name", "aliases", "source_native", "source_ids",
        "description", "scope", "resource_ids", "release", "methodology",
        "limitations", "verification",
    ),
    "data_structures": (
        "id", "name", "label", "description", "source_id", "dataset_ids",
        "parent_structure_ids", "structure_type", "verification",
    ),
    "resources": (
        "id", "name", "title", "description", "source_id", "dataset_ids",
        "access_mode", "format", "url", "verification",
    ),
    "data_elements": (
        "id", "name", "label", "description", "dataset_ids",
        "data_structure_ids", "element_type", "unit", "verification",
    ),
    "variables": (
        "id", "name", "label", "description", "definition", "aliases",
        "source_native", "dataset_ids", "data_structure_ids", "construct_ids",
        "role_candidates", "observation_unit", "population", "unit",
        "temporal_resolution", "spatial_resolution", "measurement",
        "comparability", "join_keys", "verification",
    ),
    "constructs": (
        "id", "name", "label", "preferred_label", "aliases", "definition",
        "description", "construct_type", "verification",
    ),
    "semantic_nodes": (
        "id", "name", "label", "preferred_label", "aliases", "definition",
        "description", "node_type", "verification",
    ),
}


class GlobalIndexError(ValueError):
    """Raised when the derived global discovery index cannot be trusted."""


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalized(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(normalized(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(normalized(item) for item in value)
    return str(value).casefold()


def contains(value: Any, query: str | None) -> bool:
    return query is None or normalized(query) in normalized(value)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GlobalIndexError(f"expected a JSON object: {path}")
    return value


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise GlobalIndexError(
                    f"{path}:{line_number}: expected a JSON object"
                )
            yield value


def compact_summary(
    entity_type: str,
    record: dict[str, Any],
    *,
    detailed: bool = False,
) -> dict[str, Any]:
    if detailed:
        fields = SUMMARY_FIELDS.get(
            entity_type, ("id", "name", "label", "verification")
        )
    else:
        fields = (
            "id", "name", "label", "title", "preferred_label", "aliases",
            "description", "definition", "source_ids", "dataset_ids",
            "data_structure_ids", "construct_ids", "role_candidates",
            "measurement", "verification",
        )
    summary = {key: record[key] for key in fields if key in record}
    summary.setdefault("id", record["id"])
    verification = summary.get("verification")
    if isinstance(verification, dict):
        summary["verification"] = {
            key: verification[key]
            for key in ("status", "last_verified_at")
            if key in verification
        }
    if entity_type == "variables":
        measurement = summary.get("measurement")
        if isinstance(measurement, dict):
            summary["measurement"] = {
                key: measurement[key]
                for key in ("type", "directness", "objective_subjective", "definition")
                if key in measurement
            }
        comparability = summary.get("comparability")
        if isinstance(comparability, dict):
            summary["comparability"] = {
                key: comparability[key]
                for key in ("status", "framework", "comparable_across")
                if key in comparability
            }
        source_native = summary.get("source_native")
        if isinstance(source_native, dict):
            summary["source_native"] = {
                key: source_native[key]
                for key in (
                    "system", "dataflow_id", "data_structure_id",
                    "measure_element_id", "series_code", "indicator_code",
                )
                if key in source_native
            }
    return summary


def searchable_text(entity_type: str, record: dict[str, Any]) -> str:
    values: list[Any] = []
    for key in (
        "name", "label", "title", "preferred_label", "description",
        "definition", "aliases", "synonyms",
    ):
        if key in record:
            values.append(record[key])
    if entity_type in {"sources", "datasets"}:
        scope = record.get("scope", {})
        if isinstance(scope, dict):
            for key in ("disciplines", "topics", "observation_units", "modalities"):
                if key in scope:
                    values.append(scope[key])
    if entity_type == "variables":
        measurement = record.get("measurement", {})
        if isinstance(measurement, dict):
            values.extend(
                measurement[key]
                for key in ("definition", "type")
                if key in measurement
            )
        source_native = record.get("source_native", {})
        if isinstance(source_native, dict):
            values.extend(
                source_native[key]
                for key in ("series_code", "indicator_code", "dataflow_id")
                if key in source_native
            )
    return normalized(values)


def display_label(record: dict[str, Any]) -> str:
    return str(
        record.get("preferred_label")
        or record.get("label")
        or record.get("name")
        or record.get("title")
        or record["id"]
    )


def registry_signature(root: Path) -> str:
    records = []
    for filename in sorted(CENTRAL_COLLECTIONS.values()):
        path = root / filename
        if path.is_file():
            stat = path.stat()
            records.append(
                {"name": filename, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
            )
        else:
            records.append({"name": filename, "missing": True})
    return fingerprint(records)


def card_signature(card: dict[str, Any]) -> str:
    return fingerprint(
        {
            "id": card.get("id"),
            "source_id": card.get("source_id"),
            "latest_snapshot": card.get("latest_snapshot"),
            "release": card.get("release"),
            "archive_fingerprint": card.get("archive_fingerprint"),
            "runtime": card.get("runtime"),
            "status": card.get("status"),
        }
    )


def cards_signature(cards: Iterable[dict[str, Any]]) -> str:
    return fingerprint(
        [
            {"source_id": card.get("source_id"), "signature": card_signature(card)}
            for card in sorted(cards, key=lambda item: str(item.get("source_id")))
        ]
    )


def _metadata(connection: sqlite3.Connection) -> dict[str, str]:
    return dict(connection.execute("SELECT key, value FROM metadata"))


def _set_metadata(connection: sqlite3.Connection, key: str, value: Any) -> None:
    connection.execute(
        "INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)",
        (key, json.dumps(value, ensure_ascii=False, sort_keys=True)),
    )


def _metadata_value(metadata: dict[str, str], key: str, default: Any = None) -> Any:
    raw = metadata.get(key)
    return default if raw is None else json.loads(raw)


def _create_schema(connection: sqlite3.Connection) -> str:
    connection.executescript(
        """
        PRAGMA journal_mode=DELETE;
        PRAGMA synchronous=FULL;
        CREATE TABLE metadata (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        CREATE TABLE sources (
          source_id TEXT PRIMARY KEY,
          archive_id TEXT NOT NULL,
          snapshot_id TEXT NOT NULL,
          repository TEXT NOT NULL,
          release TEXT NOT NULL,
          archive_fingerprint TEXT NOT NULL,
          card_signature TEXT NOT NULL,
          runtime_protocol TEXT,
          runtime_asset TEXT,
          entrypoint TEXT,
          agent_index TEXT,
          route_policies_json TEXT NOT NULL,
          status TEXT NOT NULL,
          status_detail TEXT,
          snapshot_path TEXT,
          indexed_at TEXT NOT NULL
        );
        CREATE INDEX sources_status ON sources(status);
        CREATE TABLE records (
          locator_key TEXT PRIMARY KEY,
          record_id TEXT NOT NULL,
          entity_type TEXT NOT NULL,
          origin TEXT NOT NULL,
          source_id TEXT NOT NULL,
          snapshot_id TEXT NOT NULL,
          label TEXT NOT NULL,
          search_text TEXT NOT NULL,
          verification_status TEXT NOT NULL,
          summary_json TEXT NOT NULL,
          callable INTEGER NOT NULL CHECK(callable IN (0, 1))
        );
        CREATE INDEX records_id ON records(record_id);
        CREATE INDEX records_type ON records(entity_type);
        CREATE INDEX records_source ON records(source_id, snapshot_id);
        CREATE INDEX records_callable_type ON records(callable, entity_type);
        CREATE TABLE variable_constructs (
          locator_key TEXT NOT NULL,
          source_id TEXT NOT NULL,
          snapshot_id TEXT NOT NULL,
          variable_id TEXT NOT NULL,
          construct_id TEXT NOT NULL,
          PRIMARY KEY(locator_key, construct_id)
        );
        CREATE INDEX variable_constructs_target
          ON variable_constructs(source_id, snapshot_id, construct_id);
        CREATE TABLE routes (
          source_id TEXT NOT NULL,
          snapshot_id TEXT NOT NULL,
          route_id TEXT NOT NULL,
          authority TEXT,
          access_method TEXT,
          freshness TEXT,
          uri TEXT,
          verification TEXT,
          status TEXT,
          PRIMARY KEY(source_id, snapshot_id, route_id)
        );
        CREATE TABLE variable_routes (
          source_id TEXT NOT NULL,
          snapshot_id TEXT NOT NULL,
          variable_id TEXT NOT NULL,
          route_id TEXT NOT NULL,
          PRIMARY KEY(source_id, snapshot_id, variable_id, route_id)
        );
        CREATE INDEX variable_routes_variable ON variable_routes(variable_id);
        """
    )
    backend = "scan"
    try:
        connection.execute(
            "CREATE VIRTUAL TABLE record_search USING fts5("
            "label, search_text, content='records', content_rowid='rowid')"
        )
        connection.executescript(
            """
            CREATE TRIGGER records_ai AFTER INSERT ON records BEGIN
              INSERT INTO record_search(rowid, label, search_text)
              VALUES (new.rowid, new.label, new.search_text);
            END;
            CREATE TRIGGER records_ad AFTER DELETE ON records BEGIN
              INSERT INTO record_search(record_search, rowid, label, search_text)
              VALUES ('delete', old.rowid, old.label, old.search_text);
            END;
            CREATE TRIGGER records_au AFTER UPDATE ON records BEGIN
              INSERT INTO record_search(record_search, rowid, label, search_text)
              VALUES ('delete', old.rowid, old.label, old.search_text);
              INSERT INTO record_search(rowid, label, search_text)
              VALUES (new.rowid, new.label, new.search_text);
            END;
            """
        )
        backend = "fts5"
    except sqlite3.OperationalError:
        connection.execute("CREATE INDEX records_label ON records(label)")
    _set_metadata(connection, "schema_version", INDEX_SCHEMA_VERSION)
    _set_metadata(connection, "search_backend", backend)
    return backend


def _locator_key(
    origin: str, source_id: str, snapshot_id: str, record_id: str
) -> str:
    return "|".join((origin, source_id, snapshot_id, record_id))


def _fts_available(connection: sqlite3.Connection) -> bool:
    return bool(
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='record_search'"
        ).fetchone()
    )


def _insert_record(
    connection: sqlite3.Connection,
    *,
    entity_type: str,
    record: dict[str, Any],
    origin: str,
    source_id: str,
    snapshot_id: str,
    callable_record: bool,
) -> None:
    summary = compact_summary(entity_type, record, detailed=origin == "central")
    label = display_label(summary)
    search_text = searchable_text(entity_type, record)
    locator_key = _locator_key(origin, source_id, snapshot_id, record["id"])
    verification = record.get("verification", {})
    verification_status = (
        verification.get("status", "unknown")
        if isinstance(verification, dict)
        else "unknown"
    )
    connection.execute(
        """
        INSERT INTO records(
          locator_key, record_id, entity_type, origin, source_id, snapshot_id,
          label, search_text, verification_status, summary_json,
          callable
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            locator_key,
            record["id"],
            entity_type,
            origin,
            source_id,
            snapshot_id,
            label,
            search_text,
            verification_status,
            json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            1 if callable_record else 0,
        ),
    )
    if entity_type == "variables":
        for construct_id in sorted(set(record.get("construct_ids", []))):
            connection.execute(
                "INSERT OR IGNORE INTO variable_constructs VALUES (?, ?, ?, ?, ?)",
                (locator_key, source_id, snapshot_id, record["id"], construct_id),
            )


def _delete_records(
    connection: sqlite3.Connection,
    *,
    origin: str | None = None,
    source_id: str | None = None,
) -> None:
    clauses = []
    values: list[str] = []
    if origin is not None:
        clauses.append("origin = ?")
        values.append(origin)
    if source_id is not None:
        clauses.append("source_id = ?")
        values.append(source_id)
    where = " AND ".join(clauses) or "1 = 1"
    locator_keys = [
        row[0]
        for row in connection.execute(
            f"SELECT locator_key FROM records WHERE {where}", values
        )
    ]
    if locator_keys:
        connection.executemany(
            "DELETE FROM variable_constructs WHERE locator_key = ?",
            ((key,) for key in locator_keys),
        )
    connection.execute(f"DELETE FROM records WHERE {where}", values)


def _record_source_ids(
    record: dict[str, Any],
    dataset_sources: dict[str, set[str]],
    structure_sources: dict[str, set[str]],
) -> set[str]:
    source_ids = set(record.get("source_ids", []))
    source_id = record.get("source_id")
    if isinstance(source_id, str) and source_id:
        source_ids.add(source_id)
    for dataset_id in record.get("dataset_ids", []):
        source_ids.update(dataset_sources.get(dataset_id, set()))
    for structure_id in record.get("data_structure_ids", []):
        source_ids.update(structure_sources.get(structure_id, set()))
    return source_ids


def _ingest_central_registry(connection: sqlite3.Connection, root: Path) -> int:
    _delete_records(connection, origin="central")
    snapshot_record_ids = {
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT record_id FROM records WHERE origin = 'snapshot'"
        )
    }
    dataset_sources: dict[str, set[str]] = {}
    structure_sources: dict[str, set[str]] = {}
    construct_sources: dict[str, set[str]] = {}
    inserted = 0

    for record in iter_jsonl(root / "datasets.jsonl"):
        dataset_sources[record["id"]] = set(record.get("source_ids", []))
    for record in iter_jsonl(root / "data_structures.jsonl"):
        structure_sources[record["id"]] = _record_source_ids(
            record, dataset_sources, structure_sources
        )
    variables_path = root / "variables.jsonl"
    for record in iter_jsonl(variables_path):
        if record["id"] in snapshot_record_ids:
            continue
        source_ids = _record_source_ids(record, dataset_sources, structure_sources)
        for construct_id in record.get("construct_ids", []):
            construct_sources.setdefault(construct_id, set()).update(source_ids)
        for source_id in sorted(source_ids or {""}):
            _insert_record(
                connection,
                entity_type="variables",
                record=record,
                origin="central",
                source_id=source_id,
                snapshot_id="",
                callable_record=False,
            )
            inserted += 1

    for record in iter_jsonl(root / "sources.jsonl"):
        if record["id"] in snapshot_record_ids:
            continue
        _insert_record(
            connection,
            entity_type="sources",
            record=record,
            origin="central",
            source_id=record["id"],
            snapshot_id="",
            callable_record=False,
        )
        inserted += 1
    for record in iter_jsonl(root / "datasets.jsonl"):
        if record["id"] in snapshot_record_ids:
            continue
        for source_id in sorted(dataset_sources.get(record["id"], set()) or {""}):
            _insert_record(
                connection,
                entity_type="datasets",
                record=record,
                origin="central",
                source_id=source_id,
                snapshot_id="",
                callable_record=False,
            )
            inserted += 1
    for record in iter_jsonl(root / "data_structures.jsonl"):
        if record["id"] in snapshot_record_ids:
            continue
        for source_id in sorted(structure_sources.get(record["id"], set()) or {""}):
            _insert_record(
                connection,
                entity_type="data_structures",
                record=record,
                origin="central",
                source_id=source_id,
                snapshot_id="",
                callable_record=False,
            )
            inserted += 1
    for entity_type in ("institutions", "resources", "data_elements"):
        for record in iter_jsonl(root / CENTRAL_COLLECTIONS[entity_type]):
            if record["id"] in snapshot_record_ids:
                continue
            source_ids = _record_source_ids(record, dataset_sources, structure_sources)
            for source_id in sorted(source_ids or {""}):
                _insert_record(
                    connection,
                    entity_type=entity_type,
                    record=record,
                    origin="central",
                    source_id=source_id,
                    snapshot_id="",
                    callable_record=False,
                )
                inserted += 1
    for record in iter_jsonl(root / "constructs.jsonl"):
        if record["id"] in snapshot_record_ids:
            continue
        for source_id in sorted(construct_sources.get(record["id"], set()) or {""}):
            _insert_record(
                connection,
                entity_type="constructs",
                record=record,
                origin="central",
                source_id=source_id,
                snapshot_id="",
                callable_record=False,
            )
            inserted += 1
    for record in iter_jsonl(root / "semantic_nodes.jsonl"):
        if record["id"] in snapshot_record_ids:
            continue
        _insert_record(
            connection,
            entity_type="semantic_nodes",
            record=record,
            origin="central",
            source_id="",
            snapshot_id="",
            callable_record=False,
        )
        inserted += 1
    return inserted


def _delete_source(connection: sqlite3.Connection, source_id: str) -> None:
    _delete_records(connection, origin="snapshot", source_id=source_id)
    connection.execute("DELETE FROM routes WHERE source_id = ?", (source_id,))
    connection.execute("DELETE FROM variable_routes WHERE source_id = ?", (source_id,))
    connection.execute("DELETE FROM sources WHERE source_id = ?", (source_id,))


def _ingest_source_snapshot(
    connection: sqlite3.Connection,
    card: dict[str, Any],
    cache_root: str | Path | None,
    *,
    verify: bool,
) -> tuple[str, int, str | None]:
    source_id = card["source_id"]
    _delete_source(connection, source_id)
    runtime = card.get("runtime") if isinstance(card.get("runtime"), dict) else {}
    indexed_at = now()
    status_detail = None
    snapshot = None
    try:
        import distributed_runtime as distributed

        status = distributed.local_snapshot_status(card, cache_root, verify=verify)
        if not status.get("runtime_ready") and not status.get("available_local"):
            distributed.materialize_source_snapshot(card, cache_root, scope="agent")
            status = distributed.local_snapshot_status(card, cache_root, verify=verify)
        if not status.get("runtime_ready"):
            raise GlobalIndexError("; ".join(status.get("errors", [])) or "runtime unavailable")
        snapshot = Path(status["snapshot_path"])
        agent_index = snapshot / runtime["agent_index"]
        source_connection = sqlite3.connect(agent_index)
        try:
            inserted = 0
            rows = source_connection.execute(
                "SELECT id, entity_type, payload_json FROM records ORDER BY entity_type, id"
            )
            for _record_id, entity_type, payload_json in rows:
                if entity_type not in INDEXED_ENTITY_TYPES:
                    continue
                record = json.loads(payload_json)
                _insert_record(
                    connection,
                    entity_type=entity_type,
                    record=record,
                    origin="snapshot",
                    source_id=source_id,
                    snapshot_id=card["latest_snapshot"],
                    callable_record=True,
                )
                inserted += 1
        finally:
            source_connection.close()

        access_path = snapshot / "agent" / "online_access.json"
        audit_path = snapshot / "agent" / "online_runtime_audit.json"
        access = read_json(access_path) if access_path.is_file() else {}
        audit = read_json(audit_path) if audit_path.is_file() else {}
        route_results = {
            item.get("route_id"): item for item in audit.get("route_results", [])
        }
        for route in access.get("routes", []):
            result = route_results.get(route.get("route_id"), {})
            connection.execute(
                "INSERT OR REPLACE INTO routes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source_id,
                    card["latest_snapshot"],
                    route["route_id"],
                    route.get("authority"),
                    route.get("access_method"),
                    route.get("freshness"),
                    route.get("uri"),
                    route.get("verification"),
                    result.get("status", "declared"),
                ),
            )
        for mapping in audit.get("variable_routes", []):
            for route_id in mapping.get("route_ids", []):
                connection.execute(
                    "INSERT OR REPLACE INTO variable_routes VALUES (?, ?, ?, ?)",
                    (source_id, card["latest_snapshot"], mapping["variable_id"], route_id),
                )
        route_policies = access.get("route_policies", {})
        source_status = "ready"
    except (OSError, KeyError, ValueError, sqlite3.Error, json.JSONDecodeError) as exc:
        inserted = 0
        route_policies = {}
        source_status = "unavailable"
        status_detail = str(exc)

    connection.execute(
        """
        INSERT OR REPLACE INTO sources(
          source_id, archive_id, snapshot_id, repository, release,
          archive_fingerprint, card_signature, runtime_protocol, runtime_asset,
          entrypoint, agent_index, route_policies_json, status, status_detail,
          snapshot_path, indexed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_id,
            card.get("id", ""),
            card.get("latest_snapshot", ""),
            card.get("repository", ""),
            card.get("release", ""),
            card.get("archive_fingerprint", ""),
            card_signature(card),
            runtime.get("protocol_version"),
            runtime.get("asset"),
            runtime.get("entrypoint"),
            runtime.get("agent_index"),
            json.dumps(route_policies, ensure_ascii=False, sort_keys=True),
            source_status,
            status_detail,
            str(snapshot) if snapshot is not None else None,
            indexed_at,
        ),
    )
    return source_status, inserted, status_detail


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _connection_status(connection: sqlite3.Connection, path: Path) -> dict[str, Any]:
    metadata = _metadata(connection)
    source_counts = dict(
        connection.execute("SELECT status, COUNT(*) FROM sources GROUP BY status")
    )
    entity_counts = dict(
        connection.execute("SELECT entity_type, COUNT(*) FROM records GROUP BY entity_type")
    )
    unavailable = [
        {"source_id": row[0], "snapshot_id": row[1], "reason": row[2]}
        for row in connection.execute(
            "SELECT source_id, snapshot_id, status_detail FROM sources "
            "WHERE status != 'ready' ORDER BY source_id"
        )
    ]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "index_schema_version": _metadata_value(metadata, "schema_version"),
        "status": "ready" if not unavailable else "degraded",
        "index_path": str(path),
        "search_backend": _metadata_value(metadata, "search_backend", "scan"),
        "built_at": _metadata_value(metadata, "built_at"),
        "updated_at": _metadata_value(metadata, "updated_at"),
        "central_registry_signature": _metadata_value(
            metadata, "central_registry_signature"
        ),
        "source_cards_signature": _metadata_value(metadata, "source_cards_signature"),
        "source_count": sum(source_counts.values()),
        "source_status_counts": source_counts,
        "record_count": sum(entity_counts.values()),
        "entity_counts": entity_counts,
        "variable_route_count": connection.execute(
            "SELECT COUNT(*) FROM variable_routes"
        ).fetchone()[0],
        "route_count": connection.execute("SELECT COUNT(*) FROM routes").fetchone()[0],
        "unavailable_sources": unavailable,
        "rebuildable": True,
        "canonical": False,
    }


def _open_checked(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    try:
        metadata = _metadata(connection)
        if _metadata_value(metadata, "schema_version") != INDEX_SCHEMA_VERSION:
            raise GlobalIndexError("global index schema version is unsupported")
        return connection
    except Exception:
        connection.close()
        raise


def update_global_index(
    cards: Iterable[dict[str, Any]],
    cache_root: str | Path | None = None,
    *,
    rebuild: bool = False,
    verify_sources: bool = True,
    registry_dir: str | Path | None = None,
    index_path: str | Path | None = None,
) -> dict[str, Any]:
    """Incrementally synchronize the derived index with central state and latest cards."""

    cards = sorted(list(cards), key=lambda item: item["source_id"])
    central_root = (
        Path(registry_dir).expanduser().resolve()
        if registry_dir is not None
        else registry_root()
    )
    path = (
        Path(index_path).expanduser().resolve()
        if index_path is not None
        else global_index_file()
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    central_fingerprint = registry_signature(central_root)
    card_fingerprint = cards_signature(cards)
    actions = {
        "central_rebuilt": False,
        "sources_updated": [],
        "sources_removed": [],
        "sources_unchanged": [],
    }

    must_rebuild = rebuild or not path.is_file()
    if not must_rebuild:
        try:
            checked = _open_checked(path)
            checked.close()
        except (sqlite3.Error, GlobalIndexError, json.JSONDecodeError):
            must_rebuild = True

    if must_rebuild:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        temporary.unlink(missing_ok=True)
        try:
            connection = sqlite3.connect(temporary)
            try:
                _create_schema(connection)
                for card in cards:
                    source_status, _inserted, _detail = _ingest_source_snapshot(
                        connection, card, cache_root, verify=verify_sources
                    )
                    actions["sources_updated"].append(
                        {"source_id": card["source_id"], "status": source_status}
                    )
                _ingest_central_registry(connection, central_root)
                actions["central_rebuilt"] = True
                timestamp = now()
                _set_metadata(connection, "central_registry_signature", central_fingerprint)
                _set_metadata(connection, "source_cards_signature", card_fingerprint)
                _set_metadata(connection, "built_at", timestamp)
                _set_metadata(connection, "updated_at", timestamp)
                connection.commit()
            finally:
                connection.close()
            os.replace(temporary, path)
        except Exception:
            temporary.unlink(missing_ok=True)
            Path(str(temporary) + "-journal").unlink(missing_ok=True)
            Path(str(temporary) + "-wal").unlink(missing_ok=True)
            Path(str(temporary) + "-shm").unlink(missing_ok=True)
            raise
    else:
        connection = _open_checked(path)
        try:
            metadata = _metadata(connection)
            central_needs_rebuild = (
                _metadata_value(metadata, "central_registry_signature")
                != central_fingerprint
            )

            current_cards = {card["source_id"]: card for card in cards}
            existing = {
                row[0]: {
                    "card_signature": row[1],
                    "status": row[2],
                    "snapshot_path": row[3],
                }
                for row in connection.execute(
                    "SELECT source_id, card_signature, status, snapshot_path FROM sources"
                )
            }
            for source_id in sorted(set(existing) - set(current_cards)):
                _delete_source(connection, source_id)
                actions["sources_removed"].append(source_id)
            for source_id, card in sorted(current_cards.items()):
                prior = existing.get(source_id)
                expected_path_exists = False
                try:
                    import distributed_runtime as distributed

                    expected_path_exists = distributed.snapshot_path(
                        card, cache_root
                    ).is_dir()
                except (OSError, ValueError):
                    pass
                changed = (
                    prior is None
                    or prior["card_signature"] != card_signature(card)
                    or (prior["status"] == "ready" and not expected_path_exists)
                    or prior["status"] != "ready"
                )
                if changed:
                    source_status, _inserted, _detail = _ingest_source_snapshot(
                        connection, card, cache_root, verify=verify_sources
                    )
                    actions["sources_updated"].append(
                        {"source_id": source_id, "status": source_status}
                    )
                else:
                    actions["sources_unchanged"].append(source_id)
            if (
                central_needs_rebuild
                or actions["sources_updated"]
                or actions["sources_removed"]
            ):
                _ingest_central_registry(connection, central_root)
                actions["central_rebuilt"] = True
            changed = bool(
                actions["central_rebuilt"]
                or actions["sources_updated"]
                or actions["sources_removed"]
            )
            if changed:
                _set_metadata(connection, "central_registry_signature", central_fingerprint)
                _set_metadata(connection, "source_cards_signature", card_fingerprint)
                _set_metadata(connection, "updated_at", now())
                connection.commit()
        finally:
            connection.close()

    connection = _open_checked(path)
    try:
        status = _connection_status(connection, path)
    finally:
        connection.close()
    manifest = {**status, "last_update_actions": actions}
    manifest_path = (
        global_index_manifest_file()
        if index_path is None
        else path.with_name("grdr-global-index-manifest.json")
    )
    if (
        must_rebuild
        or actions["central_rebuilt"]
        or actions["sources_updated"]
        or actions["sources_removed"]
        or not manifest_path.is_file()
    ):
        _write_manifest(manifest_path, manifest)
    return {"operation": "update_global_index", **manifest}


def ensure_global_index(
    cards: Iterable[dict[str, Any]],
    cache_root: str | Path | None = None,
    *,
    registry_dir: str | Path | None = None,
    index_path: str | Path | None = None,
) -> dict[str, Any]:
    return update_global_index(
        cards,
        cache_root,
        registry_dir=registry_dir,
        index_path=index_path,
    )


def global_index_status(
    cards: Iterable[dict[str, Any]],
    cache_root: str | Path | None = None,
    *,
    refresh: bool = True,
    registry_dir: str | Path | None = None,
    index_path: str | Path | None = None,
) -> dict[str, Any]:
    path = (
        Path(index_path).expanduser().resolve()
        if index_path is not None
        else global_index_file()
    )
    if refresh:
        return ensure_global_index(
            cards,
            cache_root,
            registry_dir=registry_dir,
            index_path=path,
        )
    if not path.is_file():
        return {
            "operation": "global_index_status",
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "status": "absent",
            "index_path": str(path),
            "rebuildable": True,
            "canonical": False,
        }
    connection = _open_checked(path)
    try:
        return {"operation": "global_index_status", **_connection_status(connection, path)}
    finally:
        connection.close()


def audit_global_index(
    cards: Iterable[dict[str, Any]],
    cache_root: str | Path | None = None,
    *,
    verify_sources: bool = False,
    registry_dir: str | Path | None = None,
    index_path: str | Path | None = None,
) -> dict[str, Any]:
    cards = list(cards)
    status = ensure_global_index(
        cards,
        cache_root,
        registry_dir=registry_dir,
        index_path=index_path,
    )
    path = Path(status["index_path"])
    connection = _open_checked(path)
    errors = []
    warnings = []
    try:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
        if quick_check != "ok":
            errors.append(f"SQLite quick_check failed: {quick_check}")
        metadata = _metadata(connection)
        central_root = (
            Path(registry_dir).expanduser().resolve()
            if registry_dir is not None
            else registry_root()
        )
        if _metadata_value(metadata, "central_registry_signature") != registry_signature(
            central_root
        ):
            errors.append("central registry signature is stale")
        if _metadata_value(metadata, "source_cards_signature") != cards_signature(cards):
            errors.append("source-card signature is stale")
        duplicate_routes = connection.execute(
            "SELECT COUNT(*) FROM (SELECT source_id, snapshot_id, variable_id, route_id, "
            "COUNT(*) AS n FROM variable_routes GROUP BY 1,2,3,4 HAVING n > 1)"
        ).fetchone()[0]
        if duplicate_routes:
            errors.append("duplicate Variable-to-route rows exist")
    finally:
        connection.close()

    verified_sources = []
    if verify_sources:
        import distributed_runtime as distributed

        for card in cards:
            source_status = distributed.local_snapshot_status(
                card, cache_root, verify=True, force_verify=True
            )
            verified_sources.append(
                {
                    "source_id": card["source_id"],
                    "runtime_ready": source_status["runtime_ready"],
                    "errors": source_status["errors"],
                }
            )
            if not source_status["runtime_ready"]:
                errors.append(
                    f"{card['source_id']}: full source verification failed"
                )
    elif status.get("unavailable_sources"):
        warnings.append("Some source snapshots are not locally materialized or callable.")
    return {
        "operation": "audit_global_index",
        "status": "passed" if not errors else "failed",
        "index": status,
        "full_source_verification": verified_sources,
        "errors": errors,
        "warnings": warnings,
    }


def _query_tokens(values: Iterable[str]) -> list[str]:
    return sorted(
        {
            token.casefold()
            for value in values
            for token in re.findall(r"[^\W_]+", str(value), flags=re.UNICODE)
            if len(token) >= 2
        }
    )


def _candidate_rows(
    connection: sqlite3.Connection,
    entity_types: Iterable[str],
    query_terms: Iterable[str],
    *,
    limit: int,
) -> list[sqlite3.Row]:
    connection.row_factory = sqlite3.Row
    types = sorted(set(entity_types))
    placeholders = ",".join("?" for _ in types)
    terms = [str(item).strip() for item in query_terms if str(item).strip()]
    tokens = _query_tokens(terms)
    candidate_limit = max(limit * 100, 1000)
    if tokens and _fts_available(connection):
        query = " OR ".join(
            f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens
        )
        rows = connection.execute(
            f"""
            SELECT records.*
            FROM record_search
            JOIN records ON records.rowid = record_search.rowid
            WHERE record_search MATCH ? AND records.entity_type IN ({placeholders})
            ORDER BY bm25(record_search)
            LIMIT ?
            """,
            (query, *types, candidate_limit),
        ).fetchall()
        if rows:
            return rows
    return connection.execute(
        f"SELECT * FROM records WHERE entity_type IN ({placeholders}) "
        "ORDER BY callable DESC, verification_status, label LIMIT ?",
        (*types, candidate_limit),
    ).fetchall()


def _matching_variable_locator_keys(
    connection: sqlite3.Connection,
    construct_query: str,
    *,
    limit: int,
) -> set[str]:
    construct_rows = _candidate_rows(
        connection,
        ("constructs",),
        (construct_query,),
        limit=max(limit, 100),
    )
    construct_ids = sorted(
        {
            row["record_id"]
            for row in construct_rows
            if contains(row["search_text"], construct_query)
        }
    )
    locator_keys: set[str] = set()
    for start in range(0, len(construct_ids), 500):
        chunk = construct_ids[start:start + 500]
        placeholders = ",".join("?" for _ in chunk)
        locator_keys.update(
            row[0]
            for row in connection.execute(
                f"SELECT locator_key FROM variable_constructs "
                f"WHERE construct_id IN ({placeholders})",
                chunk,
            )
        )
    return locator_keys


def _rows_for_locator_keys(
    connection: sqlite3.Connection,
    locator_keys: Iterable[str],
    *,
    limit: int,
) -> list[sqlite3.Row]:
    result: list[sqlite3.Row] = []
    keys = sorted(
        set(locator_keys),
        key=lambda key: (not key.startswith("snapshot|"), key),
    )
    for start in range(0, len(keys), 500):
        chunk = keys[start:start + 500]
        placeholders = ",".join("?" for _ in chunk)
        result.extend(
            connection.execute(
                f"SELECT * FROM records WHERE locator_key IN ({placeholders})",
                chunk,
            ).fetchall()
        )
        if len(result) >= limit:
            break
    return result[:limit]


def _ready_source_ids(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT source_id FROM sources WHERE status = 'ready'"
        )
    }


def _row_allowed(
    row: sqlite3.Row,
    ready_source_ids: set[str],
    snapshot_policy: str,
) -> bool:
    return not (
        snapshot_policy == "latest_callable"
        and row["origin"] == "central"
        and row["source_id"] in ready_source_ids
    )


def _row_result(row: sqlite3.Row) -> dict[str, Any]:
    record = json.loads(row["summary_json"])
    if row["origin"] == "snapshot":
        record["_grdr_snapshot"] = {
            "source_id": row["source_id"],
            "snapshot_id": row["snapshot_id"],
        }
    record["_grdr_global_locator"] = {
        "origin": row["origin"],
        "source_id": row["source_id"] or None,
        "snapshot_id": row["snapshot_id"] or None,
        "callable": bool(row["callable"]),
    }
    return record


def search_records(
    cards: Iterable[dict[str, Any]],
    entity_types: Iterable[str],
    cache_root: str | Path | None = None,
    *,
    query: str | None = None,
    construct: str | None = None,
    dataset_id: str | None = None,
    role: str | None = None,
    measurement_type: str | None = None,
    verification: str | None = None,
    snapshot_policy: str = "latest_callable",
    limit: int = 25,
    registry_dir: str | Path | None = None,
    index_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    if snapshot_policy not in {"latest_callable", "history"}:
        raise GlobalIndexError("snapshot_policy must be latest_callable or history")
    status = ensure_global_index(
        cards,
        cache_root,
        registry_dir=registry_dir,
        index_path=index_path,
    )
    connection = _open_checked(Path(status["index_path"]))
    try:
        types = tuple(entity_types)
        construct_locators: set[str] | None = None
        if construct and "variables" in types:
            construct_locators = _matching_variable_locator_keys(
                connection, construct, limit=max(limit * 100, 1000)
            )
        if construct_locators is not None and not query and set(types) == {"variables"}:
            rows = _rows_for_locator_keys(
                connection,
                construct_locators,
                limit=max(limit * 100, 1000),
            )
        else:
            rows = _candidate_rows(
                connection,
                types,
                [query] if query else [],
                limit=limit,
            )
        ready = _ready_source_ids(connection)
        scored = []
        for row in rows:
            if not _row_allowed(row, ready, snapshot_policy):
                continue
            if query and not contains(row["search_text"], query):
                continue
            if construct_locators is not None and row["locator_key"] not in construct_locators:
                continue
            summary = json.loads(row["summary_json"])
            if dataset_id and dataset_id not in summary.get("dataset_ids", []):
                continue
            if role and role not in summary.get("role_candidates", []):
                continue
            if measurement_type and measurement_type != summary.get("measurement", {}).get("type"):
                continue
            if verification and verification != row["verification_status"]:
                continue
            label = normalized(row["label"])
            score = (10 if query and normalized(query) == label else 0)
            score += 4 if query and normalized(query) in label else 0
            score += 3 if construct and construct_locators is not None else 0
            score += 2 if row["callable"] else 0
            scored.append((score, row))
        scored.sort(
            key=lambda item: (
                -item[0],
                VERIFICATION_RANK.get(item[1]["verification_status"], 99),
                item[1]["origin"] != "snapshot",
                item[1]["label"].casefold(),
                item[1]["record_id"],
            )
        )
        deduped: dict[str, sqlite3.Row] = {}
        for _score, row in scored:
            deduped.setdefault(row["record_id"], row)
            if len(deduped) >= limit:
                break
        return [_row_result(row) for row in deduped.values()]
    finally:
        connection.close()


def hydrate_snapshot_records(
    cards: Iterable[dict[str, Any]],
    records: Iterable[dict[str, Any]],
    cache_root: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Hydrate only selected snapshot hits from their authoritative source indexes."""

    import distributed_runtime as distributed

    cards_by_source = {card["source_id"]: card for card in cards}
    hydrated = []
    connections: dict[str, sqlite3.Connection] = {}
    snapshots: dict[str, Path] = {}
    try:
        for record in records:
            locator = record.get("_grdr_global_locator", {})
            source_id = locator.get("source_id")
            snapshot_id = locator.get("snapshot_id")
            card = cards_by_source.get(source_id)
            if (
                locator.get("origin") != "snapshot"
                or card is None
                or card.get("latest_snapshot") != snapshot_id
            ):
                hydrated.append(record)
                continue
            if source_id not in connections:
                status = distributed.local_snapshot_status(card, cache_root, verify=False)
                if not status["runtime_ready"]:
                    hydrated.append(record)
                    continue
                snapshot = Path(status["snapshot_path"])
                snapshots[source_id] = snapshot
                connections[source_id] = sqlite3.connect(
                    snapshot / card["runtime"]["agent_index"]
                )
            exact = distributed.record_by_id(connections[source_id], record["id"])
            if exact is None:
                hydrated.append(record)
                continue
            exact["_grdr_snapshot"] = {
                "source_id": source_id,
                "snapshot_id": snapshot_id,
                "location": str(snapshots[source_id]),
                "release": card["release"],
            }
            exact["_grdr_global_locator"] = locator
            hydrated.append(exact)
    finally:
        for connection in connections.values():
            connection.close()
    return hydrated


def search_semantic_candidates(
    cards: Iterable[dict[str, Any]],
    query_terms: Iterable[str],
    cache_root: str | Path | None = None,
    *,
    limit: int = 25,
    snapshot_policy: str = "latest_callable",
    registry_dir: str | Path | None = None,
    index_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    terms = [str(item).strip() for item in query_terms if str(item).strip()]
    status = ensure_global_index(
        cards,
        cache_root,
        registry_dir=registry_dir,
        index_path=index_path,
    )
    connection = _open_checked(Path(status["index_path"]))
    try:
        rows = _candidate_rows(
            connection,
            ("constructs", "semantic_nodes", "variables"),
            terms,
            limit=max(limit * 8, 80),
        )
        ready = _ready_source_ids(connection)
        candidates: dict[tuple[str, str, str], dict[str, Any]] = {}

        def merge(
            target_row: sqlite3.Row,
            *,
            via: str,
            matched_terms: list[str],
            variable_hint: str | None = None,
        ) -> None:
            target = json.loads(target_row["summary_json"])
            target_type = (
                "construct"
                if target_row["entity_type"] == "constructs"
                else "semantic_node"
            )
            key = (
                target["id"],
                target_row["source_id"],
                target_row["snapshot_id"],
            )
            item = candidates.setdefault(
                key,
                {
                    "target_type": target_type,
                    "target_id": target["id"],
                    "target_label": display_label(target),
                    "target_definition": target.get("definition", ""),
                    "retrieval_via": [],
                    "matched_terms": [],
                    "lexical_score": 0.0,
                    "variable_hint_ids": [],
                    "snapshot": (
                        {
                            "source_id": target_row["source_id"],
                            "snapshot_id": target_row["snapshot_id"],
                        }
                        if target_row["origin"] == "snapshot"
                        else None
                    ),
                    "verification_status": target_row["verification_status"],
                },
            )
            if via not in item["retrieval_via"]:
                item["retrieval_via"].append(via)
            item["matched_terms"] = sorted(
                set(item["matched_terms"]) | set(matched_terms)
            )
            item["lexical_score"] = max(
                item["lexical_score"],
                float(len(matched_terms) + (2 if target_type == "construct" else 0)),
            )
            if variable_hint and variable_hint not in item["variable_hint_ids"]:
                item["variable_hint_ids"].append(variable_hint)

        eligible_rows = [
            row
            for row in rows
            if _row_allowed(row, ready, snapshot_policy)
            and any(contains(row["search_text"], term) for term in terms)
        ]
        variable_rows = [
            row for row in eligible_rows if row["entity_type"] == "variables"
        ]
        variable_construct_map: dict[str, list[str]] = {}
        variable_locator_keys = [row["locator_key"] for row in variable_rows]
        for start in range(0, len(variable_locator_keys), 500):
            chunk = variable_locator_keys[start:start + 500]
            placeholders = ",".join("?" for _ in chunk)
            for locator_key, construct_id in connection.execute(
                f"SELECT locator_key, construct_id FROM variable_constructs "
                f"WHERE locator_key IN ({placeholders})",
                chunk,
            ):
                variable_construct_map.setdefault(locator_key, []).append(construct_id)
        target_locator_keys = {
            _locator_key(
                row["origin"], row["source_id"], row["snapshot_id"], construct_id
            )
            for row in variable_rows
            for construct_id in variable_construct_map.get(row["locator_key"], [])
        }
        target_rows = {
            row["locator_key"]: row
            for row in _rows_for_locator_keys(
                connection, target_locator_keys, limit=max(len(target_locator_keys), 1)
            )
        }

        for row in eligible_rows:
            matched = [term for term in terms if contains(row["search_text"], term)]
            if row["entity_type"] in {"constructs", "semantic_nodes"}:
                merge(
                    row,
                    via=(
                        "construct_text"
                        if row["entity_type"] == "constructs"
                        else "semantic_node_text"
                    ),
                    matched_terms=matched,
                )
                continue
            construct_ids = variable_construct_map.get(row["locator_key"], [])
            for construct_id in construct_ids:
                target_row = target_rows.get(
                    _locator_key(
                        row["origin"],
                        row["source_id"],
                        row["snapshot_id"],
                        construct_id,
                    )
                )
                if target_row is not None:
                    merge(
                        target_row,
                        via="variable_text",
                        matched_terms=matched,
                        variable_hint=row["record_id"],
                    )
        ordered = sorted(
            candidates.values(),
            key=lambda item: (
                -item["lexical_score"],
                item["target_type"] != "construct",
                VERIFICATION_RANK.get(item["verification_status"], 99),
                item["snapshot"] is None,
                item["target_label"].casefold(),
            ),
        )
        return ordered[:limit]
    finally:
        connection.close()


def route_variable(
    cards: Iterable[dict[str, Any]],
    variable_id: str,
    cache_root: str | Path | None = None,
    *,
    route_policy: str = "latest",
    registry_dir: str | Path | None = None,
    index_path: str | Path | None = None,
) -> dict[str, Any]:
    if route_policy not in {"latest", "reproducible", "offline"}:
        raise GlobalIndexError(f"unknown route policy: {route_policy}")
    cards = list(cards)
    status = ensure_global_index(
        cards,
        cache_root,
        registry_dir=registry_dir,
        index_path=index_path,
    )
    connection = _open_checked(Path(status["index_path"]))
    try:
        rows = connection.execute(
            """
            SELECT records.source_id, records.snapshot_id, records.verification_status,
                   sources.release, sources.repository, sources.runtime_protocol,
                   sources.route_policies_json, sources.snapshot_path
            FROM records
            JOIN sources ON sources.source_id = records.source_id
              AND sources.snapshot_id = records.snapshot_id
            WHERE records.record_id = ? AND records.entity_type = 'variables'
              AND records.callable = 1 AND sources.status = 'ready'
            ORDER BY records.verification_status, records.source_id
            """,
            (variable_id,),
        ).fetchall()
        candidates = []
        for row in rows:
            source_id, snapshot_id = row[0], row[1]
            declared_route_ids = [
                item[0]
                for item in connection.execute(
                    "SELECT route_id FROM variable_routes WHERE source_id = ? "
                    "AND snapshot_id = ? AND variable_id = ? ORDER BY route_id",
                    (source_id, snapshot_id, variable_id),
                )
            ]
            route_records = [
                {
                    "route_id": item[0],
                    "authority": item[1],
                    "access_method": item[2],
                    "freshness": item[3],
                    "uri": item[4],
                    "verification": item[5],
                    "status": item[6],
                }
                for item in connection.execute(
                    "SELECT route_id, authority, access_method, freshness, uri, "
                    "verification, status FROM routes WHERE source_id = ? "
                    "AND snapshot_id = ? AND route_id IN ("
                    + (",".join("?" for _ in declared_route_ids) or "NULL")
                    + ")",
                    (source_id, snapshot_id, *declared_route_ids),
                )
            ]
            policies = json.loads(row[6]) if row[6] else {}
            candidates.append(
                {
                    "source_id": source_id,
                    "snapshot_id": snapshot_id,
                    "release": row[3],
                    "repository": row[4],
                    "runtime_protocol": row[5],
                    "route_policy": route_policy,
                    "route_class_order": policies.get(route_policy, []),
                    "declared_variable_route_ids": declared_route_ids,
                    "declared_routes": route_records,
                    "snapshot_path": row[7],
                }
            )
        return {
            "operation": "route_variable",
            "global_index_schema_version": INDEX_SCHEMA_VERSION,
            "variable_id": variable_id,
            "route_policy": route_policy,
            "candidate_source_count": len(candidates),
            "candidates": candidates,
            "status": "routable" if candidates else "not_found_in_callable_index",
        }
    finally:
        connection.close()


def candidate_source_ids_for_variable(
    cards: Iterable[dict[str, Any]],
    variable_id: str,
    cache_root: str | Path | None = None,
) -> list[str]:
    return [
        item["source_id"]
        for item in route_variable(cards, variable_id, cache_root)["candidates"]
    ]


def callable_source_ids(
    cards: Iterable[dict[str, Any]],
    cache_root: str | Path | None = None,
) -> set[str]:
    status = ensure_global_index(cards, cache_root)
    connection = _open_checked(Path(status["index_path"]))
    try:
        return _ready_source_ids(connection)
    finally:
        connection.close()


def cards_match_external_registry(cards: Iterable[dict[str, Any]]) -> bool:
    """Return true only when a library caller supplied the live external card set."""

    supplied = list(cards)
    archive_path = registry_root() / "source_archives.jsonl"
    external = list(iter_jsonl(archive_path))
    return cards_signature(supplied) == cards_signature(external)
