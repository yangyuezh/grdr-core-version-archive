#!/usr/bin/env python3
"""Discover, materialize, search, and invoke distributed GRDR source snapshots."""

from __future__ import annotations

import hashlib
import json
import os
import datetime as dt
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from typing import Any, Iterable

from grdr_paths import elements_root as configured_elements_root

LOGICAL_COMPONENTS = {"knowledge", "agent", "observations"}


class DistributedRuntimeError(ValueError):
    """Raised when a distributed snapshot cannot be trusted or invoked."""


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DistributedRuntimeError(f"expected a JSON object: {path}")
    return value


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def load_cards(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def elements_root(value: str | Path | None = None) -> Path:
    if value is not None:
        return Path(value).expanduser().resolve()
    return configured_elements_root()


def source_slug(card: dict[str, Any]) -> str:
    prefix = "grdr:source-archive:"
    card_id = str(card.get("id", ""))
    if not card_id.startswith(prefix):
        raise DistributedRuntimeError(f"invalid source archive id: {card_id}")
    return card_id.removeprefix(prefix)


def snapshot_path(card: dict[str, Any], root: str | Path | None = None) -> Path:
    return elements_root(root) / "sources" / source_slug(card) / "snapshots" / card["latest_snapshot"]


def runtime_paths(card: dict[str, Any], root: str | Path | None = None) -> tuple[Path, Path, Path]:
    snapshot = snapshot_path(card, root)
    runtime = card.get("runtime")
    if not isinstance(runtime, dict):
        raise DistributedRuntimeError(f"{card['source_id']} latest snapshot has no callable Agent runtime")
    return snapshot, snapshot / runtime["agent_index"], snapshot / runtime["entrypoint"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def snapshot_inventory(snapshot: Path) -> list[dict[str, Any]]:
    records = []
    for component in sorted(LOGICAL_COMPONENTS):
        base = snapshot / component
        for path in sorted(base.rglob("*")):
            relative = path.relative_to(snapshot)
            if not path.is_file() or any(
                part.startswith("._") or part == ".DS_Store"
                for part in relative.parts
            ):
                continue
            records.append({
                "path": relative.as_posix(),
                "component": component,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            })
    return records


def manifest_records_for_location(
    manifest: dict[str, Any],
    location: str,
) -> list[dict[str, Any]]:
    if manifest.get("schema_version") == "2.0.0":
        return manifest["logical_files"]
    return [
        {key: value for key, value in item.items() if key != "locations"}
        for item in manifest["logical_files"]
        if location in item.get("locations", [])
    ]


def local_snapshot_status(card: dict[str, Any], root: str | Path | None = None, verify: bool = False) -> dict[str, Any]:
    snapshot = snapshot_path(card, root)
    status: dict[str, Any] = {
        "source_id": card["source_id"],
        "snapshot_id": card["latest_snapshot"],
        "snapshot_path": str(snapshot),
        "online_release": card["release"],
        "available_local": snapshot.is_dir(),
        "runtime_ready": False,
        "logical_parity_verified": False,
        "location_inventory_verified": False,
        "observation_location_verified": False,
        "errors": [],
        "warnings": [],
    }
    if not snapshot.is_dir():
        status["errors"].append("local Elements snapshot is not materialized")
        return status
    try:
        _, index, entrypoint = runtime_paths(card, root)
    except DistributedRuntimeError as exc:
        status["errors"].append(str(exc))
        return status
    descriptor_path = snapshot / "agent" / "runtime.json"
    receipt_path = snapshot / "receipts" / "storage_receipt.json"
    audit_path = snapshot / "agent" / "runtime_audit.json"
    required = [index, entrypoint, descriptor_path, receipt_path, audit_path]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        status["errors"].extend(f"missing {path}" for path in missing)
        return status
    receipt = read_json(receipt_path)
    descriptor = read_json(descriptor_path)
    audit = read_json(audit_path)
    if receipt.get("logical_content_fingerprint") != card.get("archive_fingerprint"):
        status["errors"].append("Elements receipt fingerprint differs from the central source card")
    if descriptor.get("source_id") != card["source_id"]:
        status["errors"].append("runtime descriptor source_id differs from the central source card")
    if audit.get("status") != "ready" or audit.get("unresolved_variable_count") != 0:
        status["errors"].append("runtime audit does not prove complete variable resolution")
    manifest_path = snapshot / "receipts" / "manifest.json"
    manifest = read_json(manifest_path) if manifest_path.is_file() else None
    if manifest is not None:
        if manifest.get("source_id") != card["source_id"] or manifest.get("snapshot_id") != card["latest_snapshot"]:
            status["errors"].append("Elements manifest identity differs from the central source card")
        if manifest.get("logical_content_fingerprint") != card.get("archive_fingerprint"):
            status["errors"].append("Elements manifest fingerprint differs from the central source card")
        profile = manifest.get("snapshot_profile")
        if isinstance(profile, dict):
            status["snapshot_profile"] = profile
            status["observation_replication_mode"] = profile["observation_replication"]["mode"]
            status["observation_placements"] = profile["observation_placement"]["locations"]
    status["runtime_ready"] = not status["errors"]
    status["runtime_audit"] = audit
    if verify:
        records = snapshot_inventory(snapshot)
        if manifest is None:
            actual = fingerprint(records)
            status["computed_logical_fingerprint"] = actual
            status["logical_parity_verified"] = actual == card.get("archive_fingerprint")
            status["location_inventory_verified"] = status["logical_parity_verified"]
            status["observation_location_verified"] = status["logical_parity_verified"]
            if not status["logical_parity_verified"]:
                status["errors"].append("computed Elements logical fingerprint differs from the central source card")
        else:
            expected = manifest_records_for_location(manifest, "elements")
            actual_knowledge_agent = [
                item for item in records if item["component"] in {"knowledge", "agent"}
            ]
            expected_knowledge_agent = [
                item for item in expected if item["component"] in {"knowledge", "agent"}
            ]
            if actual_knowledge_agent != expected_knowledge_agent:
                status["errors"].append("Elements knowledge or Agent inventory differs from the snapshot manifest")
            actual_observations = [
                item for item in records if item["component"] == "observations"
            ]
            expected_observations = [
                item for item in expected if item["component"] == "observations"
            ]
            status["observation_location_verified"] = actual_observations == expected_observations
            if not status["observation_location_verified"]:
                status["warnings"].append(
                    "The callable snapshot is mounted, but the complete Elements observation placement is not materialized."
                )
            status["location_inventory_verified"] = (
                actual_knowledge_agent == expected_knowledge_agent
                and status["observation_location_verified"]
            )
            status["logical_parity_verified"] = status["location_inventory_verified"]
            status["computed_elements_inventory_fingerprint"] = fingerprint(records)
        status["runtime_ready"] = not status["errors"]
    return status


def available_runtimes(cards: Iterable[dict[str, Any]], root: str | Path | None = None) -> list[tuple[dict[str, Any], Path]]:
    result = []
    for card in cards:
        if not isinstance(card.get("runtime"), dict):
            continue
        status = local_snapshot_status(card, root)
        if status["runtime_ready"]:
            result.append((card, Path(status["snapshot_path"])))
    return result


def records_by_type(connection: sqlite3.Connection, entity_type: str) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT payload_json FROM records WHERE entity_type = ?", (entity_type,))
    return [json.loads(row[0]) for row in rows]


def distributed_entity_records(
    cards: Iterable[dict[str, Any]], entity_type: str, root: str | Path | None = None
) -> list[dict[str, Any]]:
    """Return one deduplicated entity collection across callable local snapshots."""
    by_id: dict[str, dict[str, Any]] = {}
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            for item in records_by_type(connection, entity_type):
                item["_grdr_snapshot"] = {
                    "source_id": card["source_id"],
                    "snapshot_id": card["latest_snapshot"],
                    "release": card["release"],
                }
                by_id[item["id"]] = item
        finally:
            connection.close()
    return [by_id[key] for key in sorted(by_id)]


def record_by_id(connection: sqlite3.Connection, record_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT payload_json FROM records WHERE id = ?", (record_id,)).fetchone()
    return json.loads(row[0]) if row else None


def normalized(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(normalized(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(normalized(item) for item in value)
    return str(value).casefold()


def contains(value: Any, query: str | None) -> bool:
    return query is None or query.casefold() in normalized(value)


def relationship_records(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return relationship payloads from one source index."""

    rows = connection.execute(
        "SELECT id, subject_id, predicate, object_id, payload_json FROM relationships"
    )
    result = []
    for relationship_id, subject_id, predicate, object_id, payload_json in rows:
        payload = json.loads(payload_json)
        payload.setdefault("id", relationship_id)
        payload.setdefault("subject_id", subject_id)
        payload.setdefault("predicate", predicate)
        payload.setdefault("object_id", object_id)
        result.append(payload)
    return result


def distributed_relationship_records(
    cards: Iterable[dict[str, Any]], root: str | Path | None = None
) -> list[dict[str, Any]]:
    """Return deduplicated relationship records across callable snapshots."""

    by_snapshot_and_id: dict[tuple[str, str, str], dict[str, Any]] = {}
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            for item in relationship_records(connection):
                item["_grdr_snapshot"] = {
                    "source_id": card["source_id"],
                    "snapshot_id": card["latest_snapshot"],
                    "release": card["release"],
                }
                key = (card["source_id"], card["latest_snapshot"], item["id"])
                by_snapshot_and_id[key] = item
        finally:
            connection.close()
    return [by_snapshot_and_id[key] for key in sorted(by_snapshot_and_id)]


def _query_tokens(query_terms: Iterable[str]) -> list[str]:
    result = {
        token.casefold()
        for term in query_terms
        for token in re.findall(r"[^\W_]+", str(term), flags=re.UNICODE)
        if len(token) >= 2
    }
    return sorted(result)


def _search_index_records(
    connection: sqlite3.Connection,
    query_terms: Iterable[str],
    entity_types: Iterable[str],
    limit: int,
) -> list[dict[str, Any]]:
    tokens = _query_tokens(query_terms)
    if not tokens:
        return []
    types = sorted(set(entity_types))
    placeholders = ",".join("?" for _ in types)
    fts_exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='record_search'"
    ).fetchone()
    rows: list[tuple[str, str, str]]
    if fts_exists:
        query = " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)
        rows = connection.execute(
            f"""
            SELECT records.entity_type, records.payload_json, records.search_text
            FROM record_search
            JOIN records ON records.id = record_search.id
            WHERE record_search MATCH ? AND records.entity_type IN ({placeholders})
            ORDER BY bm25(record_search)
            LIMIT ?
            """,
            (query, *types, limit),
        ).fetchall()
    else:
        rows = connection.execute(
            f"SELECT entity_type, payload_json, search_text FROM records WHERE entity_type IN ({placeholders})",
            types,
        ).fetchall()
    scored = []
    for entity_type, payload_json, search_text in rows:
        payload = json.loads(payload_json)
        haystack = normalized(search_text or payload)
        label = normalized(payload.get("preferred_label") or payload.get("label") or payload.get("name"))
        matched = [token for token in tokens if token in haystack]
        if not matched:
            continue
        exact_label = any(normalized(term) == label for term in query_terms if str(term).strip())
        prefix_label = any(label.startswith(normalized(term)) for term in query_terms if str(term).strip())
        score = float(len(matched) + (6 if exact_label else 0) + (2 if prefix_label else 0))
        scored.append(
            {
                "entity_type": entity_type,
                "record": payload,
                "matched_terms": matched,
                "lexical_score": score,
            }
        )
    return sorted(
        scored,
        key=lambda item: (-item["lexical_score"], normalized(item["record"].get("preferred_label") or item["record"].get("label") or item["record"].get("name"))),
    )[:limit]


def distributed_semantic_candidates(
    cards: Iterable[dict[str, Any]],
    query_terms: Iterable[str],
    root: str | Path | None = None,
    *,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Recall Construct/SemanticNode targets, including hits discovered through Variable text."""

    candidates: dict[tuple[str, str, str], dict[str, Any]] = {}
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            hits = _search_index_records(
                connection,
                query_terms,
                ("constructs", "semantic_nodes", "variables"),
                max(limit * 8, 80),
            )
            for hit in hits:
                record = hit["record"]
                targets: list[tuple[str, dict[str, Any], str, str | None]] = []
                if hit["entity_type"] == "constructs":
                    targets.append(("construct", record, "construct_text", None))
                elif hit["entity_type"] == "semantic_nodes":
                    targets.append(("semantic_node", record, "semantic_node_text", None))
                elif hit["entity_type"] == "variables":
                    for construct_id in record.get("construct_ids", []):
                        construct = record_by_id(connection, construct_id)
                        if construct:
                            targets.append(("construct", construct, "variable_text", record["id"]))
                for target_type, target, via, variable_hint in targets:
                    key = (card["source_id"], card["latest_snapshot"], target["id"])
                    item = candidates.setdefault(
                        key,
                        {
                            "target_type": target_type,
                            "target_id": target["id"],
                            "target_label": target.get("preferred_label") or target.get("label") or target.get("name") or target["id"],
                            "target_definition": target.get("definition", ""),
                            "retrieval_via": [],
                            "matched_terms": [],
                            "lexical_score": 0.0,
                            "variable_hint_ids": [],
                            "verification_status": target.get("verification", {}).get("status", "unknown"),
                            "snapshot": {
                                "source_id": card["source_id"],
                                "snapshot_id": card["latest_snapshot"],
                                "release": card["release"],
                            },
                        },
                    )
                    if via not in item["retrieval_via"]:
                        item["retrieval_via"].append(via)
                    item["matched_terms"] = sorted(set(item["matched_terms"]) | set(hit["matched_terms"]))
                    item["lexical_score"] = max(item["lexical_score"], hit["lexical_score"] + (1.0 if target_type == "construct" else 0.0))
                    if variable_hint and variable_hint not in item["variable_hint_ids"]:
                        item["variable_hint_ids"].append(variable_hint)
        finally:
            connection.close()
    ordered = sorted(
        candidates.values(),
        key=lambda item: (
            -item["lexical_score"],
            item["target_type"] != "construct",
            item["verification_status"] != "verified",
            item["target_label"].casefold(),
        ),
    )
    return ordered[:limit]


def _edge(
    relationship: dict[str, Any] | None,
    subject_id: str,
    predicate: str,
    object_id: str,
    traversal_direction: str,
) -> dict[str, Any]:
    return {
        "relationship_id": relationship.get("id") if relationship else None,
        "subject_id": subject_id,
        "predicate": predicate,
        "object_id": object_id,
        "traversal_direction": traversal_direction,
    }


def _dedupe_edges(edges: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in edges:
        key = (
            item.get("relationship_id"), item["subject_id"], item["predicate"],
            item["object_id"], item["traversal_direction"],
        )
        result[key] = item
    return [result[key] for key in sorted(result, key=lambda value: tuple("" if item is None else str(item) for item in value))]


def semantic_paths_in_connection(
    connection: sqlite3.Connection,
    target_id: str,
    target_type: str,
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Traverse one stored B target through the evidence graph to A records."""

    relationships = relationship_records(connection)
    outgoing: dict[tuple[str, str], list[dict[str, Any]]] = {}
    incoming: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in relationships:
        outgoing.setdefault((item["subject_id"], item["predicate"]), []).append(item)
        incoming.setdefault((item["object_id"], item["predicate"]), []).append(item)

    construct_entries: list[tuple[str, list[str], list[dict[str, Any]]]] = []
    if target_type == "construct":
        if record_by_id(connection, target_id):
            construct_entries.append((target_id, [], []))
    elif target_type == "semantic_node":
        for relation in outgoing.get((target_id, "describes"), []):
            if relation["object_id"].startswith("grdr:construct:"):
                construct_entries.append(
                    (
                        relation["object_id"],
                        [target_id],
                        [_edge(relation, target_id, "describes", relation["object_id"], "forward")],
                    )
                )
        for relation in incoming.get((target_id, "classified_as"), []):
            if relation["subject_id"].startswith("grdr:construct:"):
                construct_entries.append(
                    (
                        relation["subject_id"],
                        [target_id],
                        [_edge(relation, relation["subject_id"], "classified_as", target_id, "reverse")],
                    )
                )
    else:
        raise DistributedRuntimeError(f"unsupported semantic target type: {target_type}")

    paths = []
    seen: set[tuple[str, str]] = set()
    for construct_id, semantic_ids, semantic_edges in construct_entries:
        variable_edges = incoming.get((construct_id, "measures"), []) + incoming.get((construct_id, "proxy_for"), [])
        variable_ids = {item["subject_id"] for item in variable_edges if item["subject_id"].startswith("grdr:variable:")}
        for variable in records_by_type(connection, "variables"):
            if construct_id in variable.get("construct_ids", []):
                variable_ids.add(variable["id"])
        for variable_id in sorted(variable_ids):
            if len(paths) >= limit:
                return paths
            if (construct_id, variable_id) in seen:
                continue
            seen.add((construct_id, variable_id))
            variable = record_by_id(connection, variable_id)
            if not variable:
                continue
            edges = list(semantic_edges)
            matching_variable_edge = next(
                (item for item in variable_edges if item["subject_id"] == variable_id),
                None,
            )
            edges.append(
                _edge(
                    matching_variable_edge,
                    variable_id,
                    matching_variable_edge["predicate"] if matching_variable_edge else "measures",
                    construct_id,
                    "reverse" if matching_variable_edge else "payload_link",
                )
            )

            element_edges = incoming.get((variable_id, "operationalizes"), [])
            element_ids = {
                item["subject_id"] for item in element_edges
                if item["subject_id"].startswith("grdr:data-element:")
            }
            measure_element = variable.get("source_native", {}).get("measure_element_id")
            if measure_element:
                element_ids.add(measure_element)
            for element_id in sorted(element_ids):
                relation = next((item for item in element_edges if item["subject_id"] == element_id), None)
                edges.append(_edge(relation, element_id, "operationalizes", variable_id, "reverse" if relation else "payload_link"))

            structure_ids = set(variable.get("data_structure_ids", []))
            for element_id in element_ids:
                element = record_by_id(connection, element_id)
                if element:
                    structure_ids.update(element.get("data_structure_ids", []))
                for relation in incoming.get((element_id, "defines"), []):
                    if relation["subject_id"].startswith("grdr:data-structure:"):
                        structure_ids.add(relation["subject_id"])
                        edges.append(_edge(relation, relation["subject_id"], "defines", element_id, "reverse"))
            for structure_id in variable.get("data_structure_ids", []):
                edges.append(_edge(None, structure_id, "structures", variable_id, "payload_link"))

            dataset_ids = set(variable.get("dataset_ids", []))
            for structure_id in structure_ids:
                structure = record_by_id(connection, structure_id)
                if structure:
                    dataset_ids.update(structure.get("dataset_ids", []))
                for relation in incoming.get((structure_id, "organized_as"), []):
                    if relation["subject_id"].startswith("grdr:dataset:"):
                        dataset_ids.add(relation["subject_id"])
                        edges.append(_edge(relation, relation["subject_id"], "organized_as", structure_id, "reverse"))
            for dataset_id in variable.get("dataset_ids", []):
                edges.append(_edge(None, dataset_id, "contains_variable", variable_id, "payload_link"))

            paths.append(
                {
                    "target_type": target_type,
                    "target_id": target_id,
                    "semantic_node_ids": semantic_ids,
                    "construct_id": construct_id,
                    "variable_id": variable_id,
                    "data_element_ids": sorted(element_ids),
                    "data_structure_ids": sorted(structure_ids),
                    "dataset_ids": sorted(dataset_ids),
                    "edges": _dedupe_edges(edges),
                    "verification_status": variable.get("verification", {}).get("status", "unknown"),
                }
            )
    return paths


def distributed_semantic_paths(
    cards: Iterable[dict[str, Any]],
    target_id: str,
    target_type: str,
    root: str | Path | None = None,
    *,
    source_id: str | None = None,
    snapshot_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Traverse B→A paths inside the exact callable snapshots that contain a target."""

    paths = []
    for card, snapshot in available_runtimes(cards, root):
        if source_id and card["source_id"] != source_id:
            continue
        if snapshot_id and card["latest_snapshot"] != snapshot_id:
            continue
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            if record_by_id(connection, target_id) is None:
                continue
            for item in semantic_paths_in_connection(connection, target_id, target_type, limit=max(0, limit - len(paths))):
                item["_grdr_snapshot"] = {
                    "source_id": card["source_id"],
                    "snapshot_id": card["latest_snapshot"],
                    "release": card["release"],
                    "location": str(snapshot),
                }
                item["callable"] = True
                paths.append(item)
                if len(paths) >= limit:
                    return paths
        finally:
            connection.close()
    return paths


def distributed_variable_matches(
    cards: Iterable[dict[str, Any]],
    root: str | Path | None = None,
    *,
    query: str | None = None,
    construct: str | None = None,
    dataset_id: str | None = None,
    role: str | None = None,
    measurement_type: str | None = None,
    verification: str | None = None,
) -> list[dict[str, Any]]:
    matches = []
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            constructs = {item["id"]: item for item in records_by_type(connection, "constructs")}
            for variable in records_by_type(connection, "variables"):
                linked_constructs = [constructs[item] for item in variable.get("construct_ids", []) if item in constructs]
                if not contains(variable, query) or not contains(linked_constructs, construct):
                    continue
                if dataset_id and dataset_id not in variable.get("dataset_ids", []):
                    continue
                if role and role not in variable.get("role_candidates", []):
                    continue
                if measurement_type and measurement_type != variable.get("measurement", {}).get("type"):
                    continue
                if verification and verification != variable.get("verification", {}).get("status"):
                    continue
                matches.append({**variable, "_grdr_snapshot": {
                    "source_id": card["source_id"],
                    "snapshot_id": card["latest_snapshot"],
                    "location": str(snapshot),
                    "release": card["release"],
                }})
        finally:
            connection.close()
    matches.sort(key=lambda item: (item.get("verification", {}).get("status") != "verified", item.get("label", "").casefold()))
    return matches


def resolve_distributed_variable(cards: Iterable[dict[str, Any]], variable_id: str, root: str | Path | None = None) -> dict[str, Any] | None:
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            variable = record_by_id(connection, variable_id)
            if variable is None or not variable_id.startswith("grdr:variable:"):
                continue
            datasets = [record_by_id(connection, item) for item in variable.get("dataset_ids", [])]
            constructs = [record_by_id(connection, item) for item in variable.get("construct_ids", [])]
            structures = [record_by_id(connection, item) for item in variable.get("data_structure_ids", [])]
            return {
                "variable": variable,
                "datasets": [item for item in datasets if item],
                "constructs": [item for item in constructs if item],
                "data_structures": [item for item in structures if item],
                "snapshot": {
                    "source_id": card["source_id"],
                    "snapshot_id": card["latest_snapshot"],
                    "location": str(snapshot),
                    "release": card["release"],
                },
            }
        finally:
            connection.close()
    return None


def invoke_source_runtime(
    cards: Iterable[dict[str, Any]],
    variable_id: str,
    operation: str,
    root: str | Path | None = None,
    extra_args: Iterable[str] = (),
) -> dict[str, Any]:
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            if record_by_id(connection, variable_id) is None:
                continue
        finally:
            connection.close()
        entrypoint = snapshot / card["runtime"]["entrypoint"]
        arguments = list(extra_args)
        invocation_timeout = 90.0
        if "--timeout" in arguments:
            try:
                invocation_timeout = max(30.0, float(arguments[arguments.index("--timeout") + 1]) + 30.0)
            except (IndexError, ValueError):
                pass
        command = [sys.executable, str(entrypoint), operation, "--index", str(index), "--variable-id", variable_id, *arguments]
        try:
            completed = subprocess.run(
                command,
                cwd=entrypoint.parent,
                capture_output=True,
                text=True,
                timeout=invocation_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise DistributedRuntimeError(
                f"source runtime exceeded {invocation_timeout:g} seconds"
            ) from exc
        if completed.returncode:
            raise DistributedRuntimeError((completed.stderr or completed.stdout).strip() or "source runtime invocation failed")
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise DistributedRuntimeError("source runtime did not emit one JSON object") from exc
        return {
            "source_id": card["source_id"],
            "snapshot_id": card["latest_snapshot"],
            "runtime_protocol": card["runtime"]["protocol_version"],
            "result": result,
        }
    raise DistributedRuntimeError(f"variable is absent from every locally available source runtime: {variable_id}")


def callable_card_for_variable(
    cards: Iterable[dict[str, Any]],
    variable_id: str,
    root: str | Path | None = None,
) -> dict[str, Any] | None:
    for card, snapshot in available_runtimes(cards, root):
        index = snapshot / card["runtime"]["agent_index"]
        connection = sqlite3.connect(index)
        try:
            if record_by_id(connection, variable_id) is not None:
                return card
        finally:
            connection.close()
    return None


def research_project_data_snapshot(
    cards: Iterable[dict[str, Any]],
    variable_id: str,
    project_dir: str | Path,
    root: str | Path | None = None,
    extra_args: Iterable[str] = (),
) -> dict[str, Any]:
    cards = list(cards)
    project = Path(project_dir).expanduser().resolve()
    if not (project / "workflow.json").is_file():
        raise DistributedRuntimeError(
            f"research-project cache target has no workflow.json: {project}"
        )
    arguments = list(extra_args)
    if "--dry-run" in arguments:
        raise DistributedRuntimeError("a dry run cannot be sealed as a research-project data snapshot")
    if "--output-dir" in arguments:
        raise DistributedRuntimeError(
            "research-project data snapshots own --output-dir; do not provide both"
        )
    selected_card = callable_card_for_variable(cards, variable_id, root)
    if selected_card is None:
        raise DistributedRuntimeError(
            f"variable is absent from every locally available source runtime: {variable_id}"
        )
    profile = selected_card.get("snapshot_profile")
    if isinstance(profile, dict):
        placement = profile["observation_placement"]
        if (
            "research_project_cache" not in placement["locations"]
            or placement["cache"]["mode"] != "on_demand"
            or not placement["cache"]["research_project_snapshots"]
        ):
            raise DistributedRuntimeError(
                "source snapshot policy does not permit research-project caching"
            )
    timestamp = dt.datetime.now(dt.timezone.utc)
    fetched_at = timestamp.isoformat()
    query_fingerprint = fingerprint({
        "variable_id": variable_id,
        "arguments": arguments,
        "fetched_at": fetched_at,
    })
    capture_id = timestamp.strftime("%Y%m%dT%H%M%SZ") + "-" + query_fingerprint[:12]
    variable_slug = re.sub(r"[^a-z0-9]+", "-", variable_id.casefold()).strip("-")
    capture = project / "data_snapshots" / variable_slug / capture_id
    if capture.exists():
        raise DistributedRuntimeError(f"research data snapshot already exists: {capture}")
    data_dir = capture / "data"
    data_dir.mkdir(parents=True)
    try:
        invocation = invoke_source_runtime(
            [selected_card],
            variable_id,
            "fetch-variable",
            root,
            [*arguments, "--output-dir", str(data_dir)],
        )
        result_path = data_dir / "runtime_result.json"
        atomic_write_text(
            result_path,
            json.dumps(invocation["result"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        files = []
        for path in sorted(data_dir.rglob("*")):
            if not path.is_file():
                continue
            files.append({
                "path": path.relative_to(capture).as_posix(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            })
        manifest = {
            "schema_version": "1.0.0",
            "capture_id": capture_id,
            "research_project_path": str(project),
            "source_id": invocation["source_id"],
            "source_snapshot_id": invocation["snapshot_id"],
            "variable_id": variable_id,
            "runtime_protocol": invocation["runtime_protocol"],
            "query_arguments": arguments,
            "fetched_at": fetched_at,
            "files": files,
            "data_content_fingerprint": fingerprint(files),
        }
        manifest["manifest_fingerprint"] = fingerprint(manifest)
        manifest_path = capture / "manifest.json"
        atomic_write_text(
            manifest_path,
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        index_path = project / "data_snapshot_index.jsonl"
        existing_index = index_path.read_text(encoding="utf-8") if index_path.is_file() else ""
        atomic_write_text(
            index_path,
            existing_index
            + json.dumps(manifest, ensure_ascii=False, separators=(",", ":"))
            + "\n",
        )
        return {
            **invocation,
            "research_data_snapshot": {
                "capture_id": capture_id,
                "path": str(capture),
                "file_count": len(files),
                "data_content_fingerprint": manifest["data_content_fingerprint"],
                "manifest_fingerprint": manifest["manifest_fingerprint"],
            },
        }
    except Exception:
        shutil.rmtree(capture, ignore_errors=True)
        raise


def safe_extract(archive_path: Path, destination: Path) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        root = destination.resolve()
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if root not in target.parents and target != root:
                raise DistributedRuntimeError(f"unsafe archive member: {member.name}")
            if member.issym() or member.islnk():
                raise DistributedRuntimeError(f"archive links are not permitted: {member.name}")
        archive.extractall(destination)


def materialize_source_snapshot(card: dict[str, Any], root: str | Path | None = None) -> dict[str, Any]:
    if not isinstance(card.get("runtime"), dict):
        raise DistributedRuntimeError("the indexed snapshot predates the callable runtime artifact format")
    destination = snapshot_path(card, root)
    if destination.exists():
        status = local_snapshot_status(card, root, verify=True)
        if not status["runtime_ready"]:
            raise DistributedRuntimeError("existing Elements callable snapshot differs from the central card")
        return {"status": "already_materialized", **status}
    repository = card["repository"].removeprefix("https://github.com/").rstrip("/")
    release_tag = card["release"].rsplit("/tag/", 1)[-1]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{card['latest_snapshot']}.", dir=destination.parent) as temporary:
        workspace = Path(temporary)
        downloads = workspace / "downloads"
        downloads.mkdir()
        completed = subprocess.run(
            ["gh", "release", "download", release_tag, "--repo", repository, "--dir", str(downloads)],
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            raise DistributedRuntimeError((completed.stderr or completed.stdout).strip() or "GitHub Release download failed")
        manifest_path = downloads / "manifest.json"
        if not manifest_path.is_file():
            raise DistributedRuntimeError("GitHub Release has no manifest.json")
        manifest = read_json(manifest_path)
        if manifest.get("source_id") != card["source_id"] or manifest.get("snapshot_id") != card["latest_snapshot"]:
            raise DistributedRuntimeError("GitHub Release manifest identity differs from the central card")
        if manifest.get("logical_content_fingerprint") != card["archive_fingerprint"]:
            raise DistributedRuntimeError("GitHub Release manifest fingerprint differs from the central card")
        expanded_release = workspace / "expanded-release"
        expanded_release.mkdir()
        for asset in manifest["release_assets"]:
            path = downloads / asset["name"]
            if not path.is_file() or sha256_file(path) != asset["sha256"] or path.stat().st_size != asset["size_bytes"]:
                raise DistributedRuntimeError(f"GitHub Release asset failed SHA-256 verification: {asset['name']}")
            if path.name.endswith(".tar.gz"):
                safe_extract(path, expanded_release)
            elif asset["component"] == "agent" and len(asset["logical_paths"]) == 1:
                target = expanded_release / asset["logical_paths"][0]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            else:
                raise DistributedRuntimeError(f"unsupported Release asset representation: {asset['name']}")
        actual_release = snapshot_inventory(expanded_release)
        expected_release = manifest_records_for_location(manifest, "github_release")
        if actual_release != expected_release:
            raise DistributedRuntimeError("expanded GitHub Release differs from its declared location inventory")
        logical = workspace / "logical"
        logical.mkdir()
        expected_elements = {
            item["path"]: item for item in manifest_records_for_location(manifest, "elements")
        }
        for record in actual_release:
            if record["path"] not in expected_elements:
                continue
            source = expanded_release / record["path"]
            target = logical / record["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        receipt = downloads / "storage_receipt.json"
        if not receipt.is_file():
            raise DistributedRuntimeError("GitHub Release has no final Storage receipt")
        receipts = logical / "receipts"
        receipts.mkdir()
        shutil.copy2(receipt, receipts / receipt.name)
        shutil.copy2(manifest_path, receipts / "manifest.json")
        shutil.move(str(logical), str(destination))
    status = local_snapshot_status(card, root, verify=True)
    if not status["runtime_ready"]:
        raise DistributedRuntimeError("materialized callable snapshot failed final verification")
    return {"status": "materialized", **status}
