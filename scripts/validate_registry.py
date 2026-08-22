#!/usr/bin/env python3
"""Validate GRDR JSONL syntax, schemas when available, IDs, and references."""

from __future__ import annotations

from collections import Counter
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
SCHEMAS = ROOT / "schemas"

COLLECTIONS = {
    "institutions": (REGISTRY / "institutions.jsonl", SCHEMAS / "institution.schema.json"),
    "sources": (REGISTRY / "sources.jsonl", SCHEMAS / "source.schema.json"),
    "datasets": (REGISTRY / "datasets.jsonl", SCHEMAS / "dataset.schema.json"),
    "data_structures": (REGISTRY / "data_structures.jsonl", SCHEMAS / "data_structure.schema.json"),
    "semantic_nodes": (REGISTRY / "semantic_nodes.jsonl", SCHEMAS / "semantic_node.schema.json"),
    "resources": (REGISTRY / "resources.jsonl", SCHEMAS / "resource.schema.json"),
    "data_elements": (REGISTRY / "data_elements.jsonl", SCHEMAS / "data_element.schema.json"),
    "constructs": (REGISTRY / "constructs.jsonl", SCHEMAS / "construct.schema.json"),
    "variables": (REGISTRY / "variables.jsonl", SCHEMAS / "variable.schema.json"),
    "adapters": (REGISTRY / "adapters.jsonl", SCHEMAS / "adapter.schema.json"),
    "storage": (REGISTRY / "storage.jsonl", SCHEMAS / "storage.schema.json"),
    "monitors": (REGISTRY / "monitors.jsonl", SCHEMAS / "monitor.schema.json"),
    "relationships": (REGISTRY / "relationships.jsonl", SCHEMAS / "relationship.schema.json"),
    "source_profiles": (REGISTRY / "source_profiles.jsonl", SCHEMAS / "source_profile.schema.json"),
    "source_archives": (REGISTRY / "source_archives.jsonl", SCHEMAS / "source_archive.schema.json"),
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: record must be a JSON object")
        records.append(value)
    return records


def validate_with_jsonschema(
    collections: dict[str, list[dict[str, Any]]]
) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema is not installed; install with python3 -m pip install -r requirements-validation.txt"]

    errors: list[str] = []
    for name, records in collections.items():
        schema_path = COLLECTIONS[name][1]
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.FormatChecker(),
        )
        for index, record in enumerate(records, 1):
            for error in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
                location = ".".join(str(part) for part in error.path) or "<record>"
                errors.append(f"{COLLECTIONS[name][0]}:{index}:{location}: {error.message}")
    return errors


def validate_integrity(collections: dict[str, list[dict[str, Any]]]) -> list[str]:
    errors: list[str] = []
    all_records = [record for records in collections.values() for record in records]
    ids = [record.get("id") for record in all_records]
    known_ids = set(ids)

    if None in known_ids:
        errors.append("one or more records are missing an id")
    duplicate_ids = sorted(record_id for record_id, count in Counter(ids).items() if count > 1)
    for record_id in duplicate_ids:
        errors.append(f"duplicate id: {record_id}")

    institution_ids = {record["id"] for record in collections["institutions"]}
    source_ids = {record["id"] for record in collections["sources"]}
    dataset_ids = {record["id"] for record in collections["datasets"]}
    data_structure_ids = {record["id"] for record in collections["data_structures"]}
    resource_ids = {record["id"] for record in collections["resources"]}
    data_element_ids = {record["id"] for record in collections["data_elements"]}
    semantic_node_ids = {record["id"] for record in collections["semantic_nodes"]}
    construct_ids = {record["id"] for record in collections["constructs"]}
    for source in collections["sources"]:
        for maintainer_id in source.get("maintainer_ids", []):
            if maintainer_id not in institution_ids:
                errors.append(f"{source.get('id')}: unknown maintainer_id {maintainer_id}")

    for dataset in collections["datasets"]:
        for source_id in dataset.get("source_ids", []):
            if source_id not in source_ids:
                errors.append(f"{dataset.get('id')}: unknown source_id {source_id}")
        for resource_id in dataset.get("resource_ids", []):
            if resource_id not in resource_ids:
                errors.append(f"{dataset.get('id')}: unknown resource_id {resource_id}")

    for resource in collections["resources"]:
        if resource.get("source_id") not in source_ids:
            errors.append(f"{resource.get('id')}: unknown source_id {resource.get('source_id')}")
        for dataset_id in resource.get("dataset_ids", []):
            if dataset_id not in dataset_ids:
                errors.append(f"{resource.get('id')}: unknown dataset_id {dataset_id}")

    for structure in collections["data_structures"]:
        if structure.get("source_id") not in source_ids:
            errors.append(f"{structure.get('id')}: unknown source_id {structure.get('source_id')}")
        for dataset_id in structure.get("dataset_ids", []):
            if dataset_id not in dataset_ids:
                errors.append(f"{structure.get('id')}: unknown dataset_id {dataset_id}")
        for parent_id in structure.get("parent_structure_ids", []):
            if parent_id not in data_structure_ids:
                errors.append(f"{structure.get('id')}: unknown parent_structure_id {parent_id}")
        for child_id in structure.get("child_structure_ids", []):
            if child_id not in data_structure_ids:
                errors.append(f"{structure.get('id')}: unknown child_structure_id {child_id}")
        for element_id in structure.get("key_element_ids", []):
            if element_id not in data_element_ids:
                errors.append(f"{structure.get('id')}: unknown key_element_id {element_id}")
        for semantic_node_id in structure.get("semantic_node_ids", []):
            if semantic_node_id not in semantic_node_ids:
                errors.append(f"{structure.get('id')}: unknown semantic_node_id {semantic_node_id}")
        for resource_id in structure.get("resource_ids", []):
            if resource_id not in resource_ids:
                errors.append(f"{structure.get('id')}: unknown resource_id {resource_id}")

    for variable in collections["variables"]:
        for dataset_id in variable.get("dataset_ids", []):
            if dataset_id not in dataset_ids:
                errors.append(f"{variable.get('id')}: unknown dataset_id {dataset_id}")
        for structure_id in variable.get("data_structure_ids", []):
            if structure_id not in data_structure_ids:
                errors.append(f"{variable.get('id')}: unknown data_structure_id {structure_id}")
        for construct_id in variable.get("construct_ids", []):
            if construct_id not in construct_ids:
                errors.append(f"{variable.get('id')}: unknown construct_id {construct_id}")
        source_native = variable.get("source_native") or {}
        measure_element_id = source_native.get("measure_element_id")
        if measure_element_id and measure_element_id not in data_element_ids:
            errors.append(f"{variable.get('id')}: unknown measure_element_id {measure_element_id}")
        for selection in source_native.get("dimension_selections", []):
            element_id = selection.get("element_id")
            if element_id not in data_element_ids:
                errors.append(f"{variable.get('id')}: unknown dimension element_id {element_id}")

    for element in collections["data_elements"]:
        for dataset_id in element.get("dataset_ids", []):
            if dataset_id not in dataset_ids:
                errors.append(f"{element.get('id')}: unknown dataset_id {dataset_id}")
        for structure_id in element.get("data_structure_ids", []):
            if structure_id not in data_structure_ids:
                errors.append(f"{element.get('id')}: unknown data_structure_id {structure_id}")
        for resource_id in element.get("resource_ids", []):
            if resource_id not in resource_ids:
                errors.append(f"{element.get('id')}: unknown resource_id {resource_id}")

    for construct in collections["constructs"]:
        for broader_id in construct.get("broader_construct_ids", []):
            if broader_id not in construct_ids:
                errors.append(f"{construct.get('id')}: unknown broader_construct_id {broader_id}")

    for node in collections["semantic_nodes"]:
        for parent_id in node.get("parent_ids", []):
            if parent_id not in semantic_node_ids:
                errors.append(f"{node.get('id')}: unknown parent_id {parent_id}")
        for term in node.get("source_native_terms", []):
            if term.get("source_id") not in source_ids:
                errors.append(f"{node.get('id')}: unknown source_native source_id {term.get('source_id')}")

    for adapter in collections["adapters"]:
        if adapter.get("source_id") not in source_ids:
            errors.append(f"{adapter.get('id')}: unknown source_id {adapter.get('source_id')}")
        for resource_id in adapter.get("resource_ids", []):
            if resource_id not in resource_ids:
                errors.append(f"{adapter.get('id')}: unknown resource_id {resource_id}")

    for storage in collections["storage"]:
        if storage.get("dataset_id") not in dataset_ids:
            errors.append(f"{storage.get('id')}: unknown dataset_id {storage.get('dataset_id')}")
        if storage.get("resource_id") not in resource_ids:
            errors.append(f"{storage.get('id')}: unknown resource_id {storage.get('resource_id')}")

    for monitor in collections["monitors"]:
        target_id = monitor.get("target_id")
        if target_id not in known_ids:
            errors.append(f"{monitor.get('id')}: unknown target_id {target_id}")

    for relationship in collections["relationships"]:
        for field in ("subject_id", "object_id"):
            referenced_id = relationship.get(field)
            if referenced_id not in known_ids:
                errors.append(f"{relationship.get('id')}:{field}: unknown id {referenced_id}")

    profiled_source_ids: set[str] = set()
    for profile in collections["source_profiles"]:
        if profile.get("source_id") not in source_ids:
            errors.append(f"{profile.get('id')}: unknown source_id {profile.get('source_id')}")
        if profile.get("source_id") in profiled_source_ids:
            errors.append(f"{profile.get('id')}: duplicate current profile for {profile.get('source_id')}")
        profiled_source_ids.add(profile.get("source_id"))

    archived_source_ids: set[str] = set()
    for archive in collections.get("source_archives", []):
        if archive.get("source_id") not in source_ids:
            errors.append(f"{archive.get('id')}: unknown source_id {archive.get('source_id')}")
        if archive.get("source_id") in archived_source_ids:
            errors.append(f"{archive.get('id')}: duplicate current archive card for {archive.get('source_id')}")
        archived_source_ids.add(archive.get("source_id"))

    return errors


def main() -> int:
    try:
        collections = {
            name: load_jsonl(path)
            for name, (path, _schema_path) in COLLECTIONS.items()
        }
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    schema_messages = validate_with_jsonschema(collections)
    integrity_errors = validate_integrity(collections)
    errors = schema_messages + integrity_errors
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    counts = ", ".join(f"{name}={len(records)}" for name, records in collections.items())
    print(f"GRDR registry validation passed ({counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
