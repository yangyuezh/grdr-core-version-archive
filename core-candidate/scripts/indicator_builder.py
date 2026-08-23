#!/usr/bin/env python3
"""Audit literature-grounded GRDR research-indicator projects."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import distributed_runtime as distributed
from grdr_paths import registry_root


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_FILES = {
    "project": "indicator_project.schema.json",
    "literature": "literature_document.schema.json",
    "evidence": "evidence_unit.schema.json",
    "indicators": "research_indicator.schema.json",
    "mappings": "indicator_mapping.schema.json",
}
PROJECT_FILES = {
    "project": "project.json",
    "literature": "literature.jsonl",
    "evidence": "evidence_units.jsonl",
    "indicators": "indicators.jsonl",
    "mappings": "mappings.jsonl",
}
STAGE_ORDER = {
    "topic_scaffold": 0,
    "corpus_declared": 1,
    "evidence_extracted": 2,
    "indicator_synthesized": 3,
    "human_reviewed": 4,
    "mapping_ready": 5,
}
CONTESTED_MAPPING_STATUSES = {"proxy_candidate", "definition_conflict"}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected a JSON object")
        records.append(value)
    return records


def validate_schemas(
    records: dict[str, dict[str, Any] | list[dict[str, Any]]],
    grdr_root: Path,
) -> tuple[list[str], list[str]]:
    try:
        import jsonschema
    except ImportError:
        return [], ["jsonschema is not installed; JSON Schema validation was skipped"]

    errors: list[str] = []
    for collection, values in records.items():
        schema_path = grdr_root / "schemas" / SCHEMA_FILES[collection]
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.FormatChecker(),
        )
        items = [values] if isinstance(values, dict) else values
        for index, value in enumerate(items, 1):
            for error in sorted(
                validator.iter_errors(value), key=lambda item: list(item.path)
            ):
                location = ".".join(str(part) for part in error.path) or "<record>"
                errors.append(
                    f"{PROJECT_FILES[collection]}:{index}:{location}: {error.message}"
                )
    return errors, []


def duplicate_ids(records: list[dict[str, Any]], collection: str) -> list[str]:
    ids = [item.get("id") for item in records]
    return [
        f"{collection}: duplicate id {record_id}"
        for record_id in sorted(
            {record_id for record_id in ids if record_id and ids.count(record_id) > 1}
        )
    ]


def find_indicator_cycles(indicators: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for indicator_id in indicators:
        path: list[str] = []
        current: str | None = indicator_id
        while current is not None and current in indicators:
            if current in path:
                cycle = path[path.index(current) :] + [current]
                errors.append("indicator hierarchy cycle: " + " -> ".join(cycle))
                break
            path.append(current)
            current = indicators[current].get("parent_indicator_id")
    return sorted(set(errors))


def audit_project(
    project_dir: Path | str,
    grdr_root: Path | str = ROOT,
    grdr_registry: Path | str | None = None,
) -> dict[str, Any]:
    """Return a machine-readable audit without mutating the project."""

    project_path = Path(project_dir).expanduser().resolve()
    root = Path(grdr_root).expanduser().resolve()
    registry = (
        Path(grdr_registry).expanduser().resolve()
        if grdr_registry is not None
        else registry_root()
    )
    errors: list[str] = []
    warnings: list[str] = []

    missing = [
        filename
        for filename in PROJECT_FILES.values()
        if not (project_path / filename).is_file()
    ]
    if missing:
        return {
            "operation": "audit_indicator_project",
            "project_dir": str(project_path),
            "errors": [f"missing required project file: {name}" for name in missing],
            "warnings": [],
            "formal_evidence_ready": False,
            "mapping_ready": False,
        }

    try:
        records: dict[str, dict[str, Any] | list[dict[str, Any]]] = {
            "project": load_json(project_path / PROJECT_FILES["project"]),
            **{
                name: load_jsonl(project_path / filename)
                for name, filename in PROJECT_FILES.items()
                if name != "project"
            },
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "operation": "audit_indicator_project",
            "project_dir": str(project_path),
            "errors": [str(exc)],
            "warnings": [],
            "formal_evidence_ready": False,
            "mapping_ready": False,
        }

    schema_errors, schema_warnings = validate_schemas(records, root)
    errors.extend(schema_errors)
    warnings.extend(schema_warnings)

    project = records["project"]
    assert isinstance(project, dict)
    literature = records["literature"]
    evidence = records["evidence"]
    indicator_records = records["indicators"]
    mappings = records["mappings"]
    assert isinstance(literature, list)
    assert isinstance(evidence, list)
    assert isinstance(indicator_records, list)
    assert isinstance(mappings, list)

    for name, collection in (
        ("literature", literature),
        ("evidence", evidence),
        ("indicators", indicator_records),
        ("mappings", mappings),
    ):
        errors.extend(duplicate_ids(collection, name))

    project_id = project.get("id")
    stage = project.get("evidence_stage")
    stage_rank = STAGE_ORDER.get(str(stage), -1)
    gates = project.get("human_gates", {})
    corpus_gate = gates.get("corpus_boundary", {}).get("status")
    framework_gate = gates.get("indicator_framework", {}).get("status")
    contested_gate = gates.get("contested_mappings", {}).get("status")

    for gate_name, gate in gates.items():
        if gate.get("status") == "approved":
            if not gate.get("reviewer"):
                errors.append(f"human gate {gate_name}: approval requires a reviewer")
            if not gate.get("reviewed_at"):
                errors.append(f"human gate {gate_name}: approval requires reviewed_at")

    for collection_name, collection in (
        ("literature", literature),
        ("evidence", evidence),
        ("indicators", indicator_records),
        ("mappings", mappings),
    ):
        for item in collection:
            if item.get("project_id") != project_id:
                errors.append(
                    f"{collection_name}:{item.get('id')}: project_id does not match {project_id}"
                )

    documents = {item.get("id"): item for item in literature if item.get("id")}
    evidence_by_id = {item.get("id"): item for item in evidence if item.get("id")}
    indicators = {
        item.get("id"): item for item in indicator_records if item.get("id")
    }
    variable_path = registry / "variables.jsonl"
    try:
        variable_ids = {
            item["id"] for item in load_jsonl(variable_path) if item.get("id")
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        variable_ids = set()
        errors.append(f"cannot load GRDR variables: {exc}")
    try:
        archive_path = registry / "source_archives.jsonl"
        cards = load_jsonl(archive_path) if archive_path.is_file() else []
        variable_ids.update(
            item["id"]
            for item in distributed.distributed_entity_records(cards, "variables")
            if item.get("id")
        )
    except (OSError, ValueError, json.JSONDecodeError, distributed.DistributedRuntimeError) as exc:
        errors.append(f"cannot load distributed GRDR variables: {exc}")

    for item in evidence:
        document_id = item.get("document_id")
        if document_id not in documents:
            errors.append(f"evidence:{item.get('id')}: unknown document_id {document_id}")
            continue
        if documents[document_id].get("decision") != "included":
            errors.append(
                f"evidence:{item.get('id')}: document {document_id} is not included"
            )

    children: dict[str, list[str]] = {item_id: [] for item_id in indicators}
    for item_id, item in indicators.items():
        parent_id = item.get("parent_indicator_id")
        if parent_id is not None:
            if parent_id not in indicators:
                errors.append(f"indicator:{item_id}: unknown parent_indicator_id {parent_id}")
            else:
                children[parent_id].append(item_id)
        if item.get("is_leaf") is True and item.get("operational_spec") is None and stage_rank >= 3:
            errors.append(f"indicator:{item_id}: formal leaf requires operational_spec")
        for evidence_id in item.get("evidence_unit_ids", []):
            if evidence_id not in evidence_by_id:
                errors.append(f"indicator:{item_id}: unknown evidence_unit_id {evidence_id}")
            elif evidence_by_id[evidence_id].get("review_status") == "rejected":
                errors.append(f"indicator:{item_id}: cites rejected evidence {evidence_id}")

    for item_id, item in indicators.items():
        actual_leaf = len(children[item_id]) == 0
        if item.get("is_leaf") is not actual_leaf:
            errors.append(
                f"indicator:{item_id}: is_leaf={item.get('is_leaf')} but hierarchy implies {actual_leaf}"
            )
    errors.extend(find_indicator_cycles(indicators))

    included_documents = [item for item in literature if item.get("decision") == "included"]
    if stage == "topic_scaffold":
        if literature or evidence:
            warnings.append(
                "topic_scaffold contains literature records; advance the evidence stage before claiming literature grounding"
            )
        if corpus_gate not in {"exploratory_only", "not_required"}:
            errors.append(
                "topic_scaffold requires corpus_boundary gate status exploratory_only or not_required"
            )
        for item in indicator_records:
            if item.get("provenance_type") != "topic_scaffold":
                errors.append(
                    f"indicator:{item.get('id')}: topic scaffold must use provenance_type topic_scaffold"
                )
            if item.get("evidence_unit_ids"):
                errors.append(
                    f"indicator:{item.get('id')}: topic scaffold must not claim literature evidence"
                )
    elif stage_rank >= 2 and corpus_gate != "approved":
        errors.append(
            "evidence_extracted or later stages require human approval of the corpus boundary"
        )

    if stage_rank >= 2 and not included_documents:
        errors.append("evidence_extracted or later stages require included literature")
    if stage_rank >= 2 and not evidence:
        errors.append("evidence_extracted or later stages require evidence units")
    if stage_rank >= 3:
        if not indicator_records:
            errors.append("indicator_synthesized or later stages require indicators")
        for item in indicator_records:
            if not item.get("evidence_unit_ids"):
                errors.append(
                    f"indicator:{item.get('id')}: formal indicator has no literature evidence"
                )
            if item.get("provenance_type") == "topic_scaffold":
                errors.append(
                    f"indicator:{item.get('id')}: formal indicator cannot retain topic_scaffold provenance"
                )
    if stage_rank >= 4 and framework_gate != "approved":
        errors.append(
            "human_reviewed or mapping_ready stages require approval of the indicator framework"
        )
    if stage_rank >= 4:
        for item in indicator_records:
            if item.get("review_status") not in {"human_reviewed", "approved_for_mapping"}:
                errors.append(
                    f"indicator:{item.get('id')}: human-reviewed stage requires a human-reviewed or mapping-approved node"
                )
    if stage == "mapping_ready":
        for item in indicator_records:
            if item.get("is_leaf") and item.get("review_status") != "approved_for_mapping":
                errors.append(
                    f"indicator:{item.get('id')}: mapping-ready leaf must be approved_for_mapping"
                )

    mapping_by_indicator: dict[str, list[dict[str, Any]]] = {}
    contested_present = False
    for item in mappings:
        mapping_id = item.get("id")
        indicator_id = item.get("indicator_id")
        status = item.get("mapping_status")
        targets = item.get("variable_ids", [])
        if indicator_id not in indicators:
            errors.append(f"mapping:{mapping_id}: unknown indicator_id {indicator_id}")
        elif not indicators[indicator_id].get("is_leaf"):
            errors.append(f"mapping:{mapping_id}: mappings may target leaf indicators only")
        else:
            mapping_by_indicator.setdefault(indicator_id, []).append(item)
        for variable_id in targets:
            if variable_id not in variable_ids:
                errors.append(f"mapping:{mapping_id}: unknown GRDR variable_id {variable_id}")
        if status == "not_found_registry_snapshot" and targets:
            errors.append(f"mapping:{mapping_id}: not-found mapping must have no variable_ids")
        if status in {"direct_match", "transform_required", "proxy_candidate", "definition_conflict"} and len(targets) < 1:
            errors.append(f"mapping:{mapping_id}: {status} requires at least one variable_id")
        if status == "composite_required" and len(targets) < 2:
            errors.append(f"mapping:{mapping_id}: composite_required needs at least two variable_ids")
        if status in {"transform_required", "composite_required"} and not item.get("transformation"):
            errors.append(f"mapping:{mapping_id}: {status} requires a transformation description")
        if status in CONTESTED_MAPPING_STATUSES:
            contested_present = True
            if not item.get("human_review_required"):
                errors.append(f"mapping:{mapping_id}: contested mapping must require human review")
            if item.get("review_status") != "human_approved":
                errors.append(f"mapping:{mapping_id}: contested mapping requires human approval")

    if contested_present and contested_gate != "approved":
        errors.append("proxy or definition-conflict mappings require contested_mappings approval")
    if stage == "mapping_ready":
        leaf_ids = {
            item_id for item_id, item in indicators.items() if item.get("is_leaf")
        }
        missing_mappings = sorted(leaf_ids - set(mapping_by_indicator))
        for indicator_id in missing_mappings:
            errors.append(f"indicator:{indicator_id}: mapping_ready stage lacks a mapping")

    for document in included_documents:
        if document.get("full_text_status") in {"abstract_only", "partial", "unavailable"}:
            warnings.append(
                f"literature:{document.get('id')}: included evidence is not complete full text"
            )
        if not document.get("reference_list_processed"):
            warnings.append(
                f"literature:{document.get('id')}: reference list has not been processed for snowball discovery"
            )

    errors = sorted(set(errors))
    warnings = sorted(set(warnings))
    formal_evidence_ready = (
        stage_rank >= 4
        and corpus_gate == "approved"
        and framework_gate == "approved"
        and bool(indicator_records)
        and not errors
    )
    mapping_ready = stage == "mapping_ready" and formal_evidence_ready and not errors
    return {
        "operation": "audit_indicator_project",
        "registry_version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "project_dir": str(project_path),
        "project_id": project_id,
        "evidence_stage": stage,
        "counts": {
            "literature_documents": len(literature),
            "included_documents": len(included_documents),
            "evidence_units": len(evidence),
            "indicator_nodes": len(indicator_records),
            "leaf_indicators": sum(
                1 for item in indicator_records if item.get("is_leaf")
            ),
            "mappings": len(mappings),
        },
        "human_gates": {
            "corpus_boundary": corpus_gate,
            "indicator_framework": framework_gate,
            "contested_mappings": contested_gate,
        },
        "formal_evidence_ready": formal_evidence_ready,
        "mapping_ready": mapping_ready,
        "errors": errors,
        "warnings": warnings,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Audit a GRDR literature-grounded indicator project"
    )
    root.add_argument("project_dir")
    root.add_argument("--grdr-root", default=str(ROOT))
    root.add_argument("--registry-root")
    return root


def main() -> int:
    args = parser().parse_args()
    result = audit_project(args.project_dir, args.grdr_root, args.registry_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not result["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
