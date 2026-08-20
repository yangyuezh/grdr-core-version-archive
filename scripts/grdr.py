#!/usr/bin/env python3
"""Dependency-free local JSON interface to the GRDR foundation registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
REGISTRY_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
ENTITY_FILES = {
    "institution": "institutions.jsonl",
    "source": "sources.jsonl",
    "dataset": "datasets.jsonl",
    "data_structure": "data_structures.jsonl",
    "resource": "resources.jsonl",
    "data_element": "data_elements.jsonl",
    "construct": "constructs.jsonl",
    "semantic_node": "semantic_nodes.jsonl",
    "variable": "variables.jsonl",
    "adapter": "adapters.jsonl",
    "storage": "storage.jsonl",
    "monitor": "monitors.jsonl",
    "source_profile": "source_profiles.jsonl",
}
VERIFICATION_RANK = {
    "verified": 0,
    "partially_verified": 1,
    "stale": 2,
    "conflicted": 3,
    "unverified": 4,
    "deprecated": 5,
    "unavailable": 6,
}


def load_jsonl(name: str) -> list[dict[str, Any]]:
    path = REGISTRY / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalized_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(normalized_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(normalized_text(item) for item in value)
    return str(value).casefold()


def contains(value: Any, query: str | None) -> bool:
    return query is None or query.casefold() in normalized_text(value)


def emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def source_summary(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": source["id"],
        "name": source["name"],
        "canonical_url": source["canonical_url"],
        "disciplines": source["scope"]["disciplines"],
        "topics": source["scope"]["topics"],
        "geographic_scope": source["scope"]["geographic_scope"],
        "source_classes": source["source_classes"],
        "authority_roles": source["authority"]["roles"],
        "access": source["access"],
        "verification": source["verification"],
    }


def verification_sort(record: dict[str, Any]) -> tuple[int, str]:
    return (
        VERIFICATION_RANK.get(record["verification"]["status"], 99),
        record["name"].casefold(),
    )


def entity_index() -> dict[str, dict[str, Any]]:
    return {
        record["id"]: record
        for filename in ENTITY_FILES.values()
        for record in load_jsonl(filename)
    }


def verification_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        verification = record.get("verification")
        if not verification:
            continue
        status = verification["status"]
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def layer_summary(
    number: int,
    name: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    if not records:
        state = "not_started"
    elif all(item["verification"]["status"] == "unverified" for item in records):
        state = "registered_unverified"
    else:
        state = "registered_with_evidence"
    return {
        "layer": number,
        "name": name,
        "state": state,
        "record_count": len(records),
        "record_ids": [item["id"] for item in records],
        "verification": verification_counts(records),
    }


def build_source_depth_profile(source: dict[str, Any]) -> dict[str, Any]:
    institutions = {item["id"]: item for item in load_jsonl("institutions.jsonl")}
    relationships = load_jsonl("relationships.jsonl")
    datasets = [
        item
        for item in load_jsonl("datasets.jsonl")
        if source["id"] in item["source_ids"]
    ]
    dataset_ids = {item["id"] for item in datasets}
    resources = [
        item
        for item in load_jsonl("resources.jsonl")
        if item["source_id"] == source["id"]
        or dataset_ids.intersection(item["dataset_ids"])
    ]
    data_structures = [
        item
        for item in load_jsonl("data_structures.jsonl")
        if item["source_id"] == source["id"]
        or dataset_ids.intersection(item["dataset_ids"])
    ]
    data_elements = [
        item
        for item in load_jsonl("data_elements.jsonl")
        if dataset_ids.intersection(item["dataset_ids"])
    ]
    variables = [
        item
        for item in load_jsonl("variables.jsonl")
        if dataset_ids.intersection(item["dataset_ids"])
    ]
    construct_ids = {
        construct_id
        for item in variables
        for construct_id in item["construct_ids"]
    }
    constructs = [
        item
        for item in load_jsonl("constructs.jsonl")
        if item["id"] in construct_ids
    ]
    related_institution_ids = set(source["maintainer_ids"])
    related_institution_ids.update(
        edge["object_id"]
        for edge in relationships
        if edge["subject_id"] in {source["id"], *dataset_ids}
        and edge["object_id"] in institutions
        and edge["predicate"] in {"produced_by", "published_by", "maintained_by", "governed_by"}
    )
    maintainers = [institutions[item] for item in sorted(related_institution_ids)]
    declared_profile = next(
        (
            item
            for item in load_jsonl("source_profiles.jsonl")
            if item["source_id"] == source["id"]
        ),
        None,
    )
    layers = [
        layer_summary(1, "institution", maintainers),
        layer_summary(2, "source", [source]),
        layer_summary(3, "dataset", datasets),
        layer_summary(4, "data_structure", data_structures),
        layer_summary(5, "data_element_and_variable", data_elements + variables),
        layer_summary(6, "construct", constructs),
    ]
    populated = [item["name"] for item in layers if item["record_count"] > 0]
    if all(item["record_count"] > 0 for item in layers):
        stage = "six_layer_chain_present"
    elif variables or data_elements:
        stage = "variable_depth_started"
    elif data_structures:
        stage = "data_structure_depth_started"
    elif datasets:
        stage = "dataset_depth_started"
    else:
        stage = "source_only"

    required_actions = {
        "institution": "Verify the publishing, maintaining, producing, and governing institutions with official mandate evidence.",
        "source": "Verify canonical identity, scope, authority role, access modes, license, and provenance.",
        "dataset": "Enumerate the official catalog and register prioritized datasets with methodology, coverage, release, citation, and limitations.",
        "data_structure": "Recover the database's native hierarchy, tables, dataflows, schemas, files, questionnaires, or scientific arrays and register their exact identifiers.",
        "data_element_and_variable": "Register 5A source-native elements, then create 5B research-matchable variables only from explicit measure-plus-dimension semantics.",
        "construct": "Map variables to theoretical constructs and label direct, constructed, modeled, forecast, subjective, and proxy measurements.",
    }
    gaps = [
        {
            "layer": item["layer"],
            "name": item["name"],
            "state": item["state"],
            "recommended_action": required_actions[item["name"]],
        }
        for item in layers
        if item["state"] != "registered_with_evidence"
    ]
    if not gaps and declared_profile is None:
        gaps.append(
            {
                "layer": None,
                "name": "inventory_scope",
                "state": "not_assessed",
                "recommended_action": "Declare whether this is a representative, question-driven, prioritized, catalog-level, or exhaustive profile; then expand and verify the stated scope.",
            }
        )

    coverage_gaps = []
    if declared_profile is not None:
        coverage_gaps = [
            {
                "entity": name,
                "claim": claim,
                "meaning": "Records exist, but the declared upstream scope is not complete at this entity level.",
            }
            for name, claim in declared_profile["layer_claims"].items()
            if claim != "scope_complete"
        ]
        if declared_profile["access_claim"] != "scope_complete":
            coverage_gaps.append(
                {
                    "entity": "access",
                    "claim": declared_profile["access_claim"],
                    "meaning": "Access routes are attached as sidecars, but the declared access inventory is not complete.",
                }
            )

    return {
        "source_id": source["id"],
        "source_name": source["name"],
        "canonical_url": source["canonical_url"],
        "profile_stage": stage,
        "deep_map_scope_complete": bool(
            declared_profile
            and all(
                claim == "scope_complete"
                for claim in declared_profile["layer_claims"].values()
            )
        ),
        "populated_layers": populated,
        "layers": layers,
        "variable_matching_ready": bool(variables and datasets),
        "data_element_count": len(data_elements),
        "variable_count": len(variables),
        "data_structure_count": len(data_structures),
        "access_sidecar": {
            "state": "registered" if resources else "not_started",
            "resource_count": len(resources),
            "resource_ids": [item["id"] for item in resources],
            "note": "Access resources are attached to content entities and do not occupy a deep-map layer.",
        },
        "declared_profile": declared_profile,
        "catalog_completeness": (
            declared_profile["inventory_claim"]
            if declared_profile is not None
            else "not_assessed"
        ),
        "gaps": gaps,
        "coverage_gaps": coverage_gaps,
        "warnings": [
            "A populated layer proves only that GRDR has records at that layer; it does not prove that the upstream database has been completely inventoried.",
            "A missing layer is a GRDR coverage gap, not evidence that the upstream database lacks that layer.",
            "Source-level topic tags must never be treated as proof that a specific dataset or variable exists.",
            "variable_matching_ready means at least one registered variable can be matched; it does not mean that all datasets or variables in the source have been deep-mapped.",
        ],
    }


def search_sources(args: argparse.Namespace) -> None:
    sources = load_jsonl("sources.jsonl")
    matches: list[dict[str, Any]] = []
    for source in sources:
        if not contains(source, args.query):
            continue
        if not contains(source["scope"]["disciplines"], args.discipline):
            continue
        if not contains(source["scope"]["topics"], args.topic):
            continue
        if args.source_class and args.source_class not in source["source_classes"]:
            continue
        if args.geography and args.geography != source["scope"]["geographic_scope"]:
            continue
        if args.verification and args.verification != source["verification"]["status"]:
            continue
        matches.append(source)

    matches.sort(key=verification_sort)
    limited = matches[: args.limit]
    emit(
        {
            "operation": "search_sources",
            "registry_version": REGISTRY_VERSION,
            "result_count": len(limited),
            "total_matches": len(matches),
            "results": [source_summary(source) for source in limited],
            "warnings": [
                "Bootstrap nominations may contain unverified scope tags. Inspect each result's verification object and evidence before use."
            ],
        }
    )


def search_datasets(args: argparse.Namespace) -> None:
    datasets = load_jsonl("datasets.jsonl")
    matches: list[dict[str, Any]] = []
    for dataset in datasets:
        if not contains(dataset, args.query):
            continue
        if not contains(dataset["scope"]["disciplines"], args.discipline):
            continue
        if not contains(dataset["scope"]["topics"], args.topic):
            continue
        if not contains(dataset["scope"]["observation_units"], args.observation_unit):
            continue
        if args.verification and args.verification != dataset["verification"]["status"]:
            continue
        matches.append(dataset)

    matches.sort(key=verification_sort)
    limited = matches[: args.limit]
    emit(
        {
            "operation": "search_datasets",
            "registry_version": REGISTRY_VERSION,
            "result_count": len(limited),
            "total_matches": len(matches),
            "results": [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "source_native": item.get("source_native"),
                    "source_ids": item["source_ids"],
                    "description": item["description"],
                    "scope": item["scope"],
                    "resource_ids": item["resource_ids"],
                    "verification": item["verification"],
                }
                for item in limited
            ],
            "warnings": [
                "Dataset coverage is in an early depth-building phase; no match does not establish that a dataset does not exist."
            ],
        }
    )


def search_variables(args: argparse.Namespace) -> None:
    variables = load_jsonl("variables.jsonl")
    constructs = {item["id"]: item for item in load_jsonl("constructs.jsonl")}
    matches: list[dict[str, Any]] = []
    for variable in variables:
        linked_constructs = [
            constructs[item]
            for item in variable["construct_ids"]
            if item in constructs
        ]
        if not contains(variable, args.query):
            continue
        if not contains(linked_constructs, args.construct):
            continue
        if args.dataset_id and args.dataset_id not in variable["dataset_ids"]:
            continue
        if args.role and args.role not in variable["role_candidates"]:
            continue
        if args.measurement_type and args.measurement_type != variable["measurement"]["type"]:
            continue
        if args.verification and args.verification != variable["verification"]["status"]:
            continue
        matches.append(variable)

    matches.sort(key=verification_sort)
    limited = matches[: args.limit]
    emit(
        {
            "operation": "search_variables",
            "registry_version": REGISTRY_VERSION,
            "result_count": len(limited),
            "total_matches": len(matches),
            "results": [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "label": item["label"],
                    "source_native": item.get("source_native"),
                    "dataset_ids": item["dataset_ids"],
                    "construct_ids": item["construct_ids"],
                    "role_candidates": item["role_candidates"],
                    "observation_unit": item["observation_unit"],
                    "unit": item["unit"],
                    "measurement": item["measurement"],
                    "comparability": item["comparability"],
                    "join_keys": item["join_keys"],
                    "verification": item["verification"],
                }
                for item in limited
            ],
            "warnings": [
                "Variable coverage is illustrative in the foundation release; topic tags on a source are not treated as proof of variable availability."
            ],
        }
    )


def search_semantic_nodes(args: argparse.Namespace) -> None:
    records = load_jsonl("semantic_nodes.jsonl")
    results = [
        item for item in records
        if contains(item, args.query)
        and (args.node_type is None or item["node_type"] == args.node_type)
    ]
    results.sort(key=lambda item: (
        VERIFICATION_RANK.get(item["verification"]["status"], 99),
        item["preferred_label"].casefold(),
    ))
    emit({
        "operation": "search_semantic_nodes", "registry_version": REGISTRY_VERSION,
        "result_count": len(results), "results": results,
    })


def get_source(args: argparse.Namespace) -> None:
    sources = {source["id"]: source for source in load_jsonl("sources.jsonl")}
    institutions = {item["id"]: item for item in load_jsonl("institutions.jsonl")}
    relationships = load_jsonl("relationships.jsonl")
    source = sources.get(args.source_id)
    if source is None:
        emit(
            {
                "operation": "get_source",
                "registry_version": REGISTRY_VERSION,
                "error": "source_not_found",
                "source_id": args.source_id,
            }
        )
        raise SystemExit(2)

    related_institutions = [
        institutions[item]
        for item in source["maintainer_ids"]
        if item in institutions
    ]
    related_edges = [
        edge
        for edge in relationships
        if edge["subject_id"] == args.source_id or edge["object_id"] == args.source_id
    ]
    emit(
        {
            "operation": "get_source",
            "registry_version": REGISTRY_VERSION,
            "source": source,
            "maintainers": related_institutions,
            "relationships": related_edges,
        }
    )


def get_dataset(args: argparse.Namespace) -> None:
    datasets = {item["id"]: item for item in load_jsonl("datasets.jsonl")}
    dataset = datasets.get(args.dataset_id)
    if dataset is None:
        emit({"operation": "get_dataset", "registry_version": REGISTRY_VERSION, "error": "dataset_not_found", "dataset_id": args.dataset_id})
        raise SystemExit(2)

    sources = {item["id"]: item for item in load_jsonl("sources.jsonl")}
    resources = load_jsonl("resources.jsonl")
    data_structures = load_jsonl("data_structures.jsonl")
    variables = load_jsonl("variables.jsonl")
    data_elements = load_jsonl("data_elements.jsonl")
    emit(
        {
            "operation": "get_dataset",
            "registry_version": REGISTRY_VERSION,
            "dataset": dataset,
            "sources": [sources[item] for item in dataset["source_ids"] if item in sources],
            "resources": [item for item in resources if args.dataset_id in item["dataset_ids"]],
            "data_structures": [item for item in data_structures if args.dataset_id in item["dataset_ids"]],
            "data_elements": [item for item in data_elements if args.dataset_id in item["dataset_ids"]],
            "variables": [item for item in variables if args.dataset_id in item["dataset_ids"]],
        }
    )


def get_variable(args: argparse.Namespace) -> None:
    variables = {item["id"]: item for item in load_jsonl("variables.jsonl")}
    variable = variables.get(args.variable_id)
    if variable is None:
        emit({"operation": "get_variable", "registry_version": REGISTRY_VERSION, "error": "variable_not_found", "variable_id": args.variable_id})
        raise SystemExit(2)

    datasets = {item["id"]: item for item in load_jsonl("datasets.jsonl")}
    constructs = {item["id"]: item for item in load_jsonl("constructs.jsonl")}
    structures = {item["id"]: item for item in load_jsonl("data_structures.jsonl")}
    emit(
        {
            "operation": "get_variable",
            "registry_version": REGISTRY_VERSION,
            "variable": variable,
            "datasets": [datasets[item] for item in variable["dataset_ids"] if item in datasets],
            "constructs": [constructs[item] for item in variable["construct_ids"] if item in constructs],
            "data_structures": [structures[item] for item in variable["data_structure_ids"] if item in structures],
        }
    )


def get_semantic_node(args: argparse.Namespace) -> None:
    records = {item["id"]: item for item in load_jsonl("semantic_nodes.jsonl")}
    node = records.get(args.semantic_node_id)
    if node is None:
        emit({"operation": "get_semantic_node", "registry_version": REGISTRY_VERSION, "error": "semantic_node_not_found", "semantic_node_id": args.semantic_node_id})
        return
    children = [item for item in records.values() if node["id"] in item.get("parent_ids", [])]
    relationships = [
        item for item in load_jsonl("relationships.jsonl")
        if node["id"] in {item["subject_id"], item["object_id"]}
    ]
    emit({
        "operation": "get_semantic_node", "registry_version": REGISTRY_VERSION,
        "semantic_node": node,
        "parents": [records[item] for item in node.get("parent_ids", []) if item in records],
        "children": children, "relationships": relationships,
    })


def get_data_element(args: argparse.Namespace) -> None:
    elements = {item["id"]: item for item in load_jsonl("data_elements.jsonl")}
    element = elements.get(args.element_id)
    if element is None:
        emit({"operation": "get_data_element", "registry_version": REGISTRY_VERSION, "error": "data_element_not_found", "element_id": args.element_id})
        raise SystemExit(2)

    datasets = {item["id"]: item for item in load_jsonl("datasets.jsonl")}
    resources = {item["id"]: item for item in load_jsonl("resources.jsonl")}
    structures = {item["id"]: item for item in load_jsonl("data_structures.jsonl")}
    emit(
        {
            "operation": "get_data_element",
            "registry_version": REGISTRY_VERSION,
            "data_element": element,
            "datasets": [datasets[item] for item in element["dataset_ids"] if item in datasets],
            "resources": [resources[item] for item in element["resource_ids"] if item in resources],
            "data_structures": [structures[item] for item in element["data_structure_ids"] if item in structures],
        }
    )


def get_data_structure(args: argparse.Namespace) -> None:
    structures = {item["id"]: item for item in load_jsonl("data_structures.jsonl")}
    structure = structures.get(args.data_structure_id)
    if structure is None:
        emit({"operation": "get_data_structure", "registry_version": REGISTRY_VERSION, "error": "data_structure_not_found", "data_structure_id": args.data_structure_id})
        raise SystemExit(2)

    datasets = {item["id"]: item for item in load_jsonl("datasets.jsonl")}
    resources = {item["id"]: item for item in load_jsonl("resources.jsonl")}
    elements = load_jsonl("data_elements.jsonl")
    variables = load_jsonl("variables.jsonl")
    emit(
        {
            "operation": "get_data_structure",
            "registry_version": REGISTRY_VERSION,
            "data_structure": structure,
            "datasets": [datasets[item] for item in structure["dataset_ids"] if item in datasets],
            "parent_structures": [structures[item] for item in structure["parent_structure_ids"] if item in structures],
            "resources": [resources[item] for item in structure["resource_ids"] if item in resources],
            "data_elements": [item for item in elements if args.data_structure_id in item["data_structure_ids"]],
            "variables": [item for item in variables if args.data_structure_id in item["data_structure_ids"]],
        }
    )


def trace_provenance(args: argparse.Namespace) -> None:
    entities = entity_index()
    if args.entity_id not in entities:
        emit({"operation": "trace_provenance", "registry_version": REGISTRY_VERSION, "error": "entity_not_found", "entity_id": args.entity_id})
        raise SystemExit(2)

    relationships = load_jsonl("relationships.jsonl")
    visited = {args.entity_id}
    frontier = {args.entity_id}
    included_edges: dict[str, dict[str, Any]] = {}
    for _level in range(args.depth):
        next_frontier: set[str] = set()
        for edge in relationships:
            if edge["subject_id"] in frontier or edge["object_id"] in frontier:
                included_edges[edge["id"]] = edge
                for entity_id in (edge["subject_id"], edge["object_id"]):
                    if entity_id not in visited:
                        visited.add(entity_id)
                        next_frontier.add(entity_id)
        frontier = next_frontier
        if not frontier:
            break

    emit(
        {
            "operation": "trace_provenance",
            "registry_version": REGISTRY_VERSION,
            "root_id": args.entity_id,
            "depth": args.depth,
            "nodes": [entities[item] for item in sorted(visited) if item in entities],
            "edges": [included_edges[item] for item in sorted(included_edges)],
            "warnings": [
                "The trace contains only explicit, evidence-backed registry edges; absence of an edge is not evidence of no relationship."
            ],
        }
    )


def diagnose_coverage(args: argparse.Namespace) -> None:
    request_path = Path(args.request_file).expanduser().resolve()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    constructs = load_jsonl("constructs.jsonl")
    variables = load_jsonl("variables.jsonl")
    findings: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    for requirement in request.get("constructs", []):
        requested_name = requirement["name"]
        requested_normalized = requested_name.casefold()
        matched_constructs = [
            item
            for item in constructs
            if requested_normalized == item["name"].casefold()
            or requested_normalized in {alias.casefold() for alias in item.get("aliases", [])}
        ]
        matched_ids = {item["id"] for item in matched_constructs}
        matched_variables = [
            item
            for item in variables
            if matched_ids.intersection(item["construct_ids"])
        ]

        if matched_variables:
            best_rank = min(
                VERIFICATION_RANK.get(item["verification"]["status"], 99)
                for item in matched_variables
            )
            if best_rank == VERIFICATION_RANK["verified"]:
                status = "verified_available"
            elif best_rank == VERIFICATION_RANK["partially_verified"]:
                status = "partially_verified_available"
            else:
                status = "reported_available_unverified"
            findings.append(
                {
                    "requirement": requirement,
                    "status": status,
                    "constructs": matched_constructs,
                    "variables": matched_variables,
                }
            )
            continue

        gap = {
            "requirement": requirement,
            "status": "conceptually_required_not_found",
            "gap_type": "construct_without_registered_variable" if matched_constructs else "construct_not_registered",
            "interpretation": "No variable-level match was found in this registry snapshot; this is a registry coverage gap, not evidence that no external data exists.",
            "recommended_action": "Search verified source catalogs and methodology documentation, then register candidate constructs, datasets, and variables with evidence.",
        }
        findings.append(gap)
        gaps.append(gap)

    emit(
        {
            "operation": "diagnose_coverage",
            "registry_version": REGISTRY_VERSION,
            "request_file": str(request_path),
            "request_id": request.get("request_id"),
            "question": request.get("question"),
            "findings": findings,
            "data_gaps": gaps,
            "summary": {
                "requirements": len(findings),
                "with_registered_variables": len(findings) - len(gaps),
                "registry_gaps": len(gaps),
            },
            "warnings": [
                "This operation diagnoses registry coverage only. It does not yet evaluate temporal, spatial, population, construct-validity, joinability, or causal-identification fit."
            ],
        }
    )


def list_adapters(args: argparse.Namespace) -> None:
    records = [
        item
        for item in load_jsonl("adapters.jsonl")
        if (args.source_id is None or item["source_id"] == args.source_id)
        and (args.status is None or item["state"]["status"] == args.status)
        and (args.storage_mode is None or args.storage_mode in item["supported_storage_modes"])
    ]
    emit({"operation": "list_adapters", "registry_version": REGISTRY_VERSION, "result_count": len(records), "results": records})


def list_storage(args: argparse.Namespace) -> None:
    records = [
        item
        for item in load_jsonl("storage.jsonl")
        if (args.dataset_id is None or item["dataset_id"] == args.dataset_id)
        and (args.mode is None or item["mode"] == args.mode)
    ]
    emit({"operation": "list_storage", "registry_version": REGISTRY_VERSION, "result_count": len(records), "results": records})


def list_monitors(args: argparse.Namespace) -> None:
    records = [
        item
        for item in load_jsonl("monitors.jsonl")
        if (args.status is None or item["state"]["status"] == args.status)
        and (args.enabled is None or item["enabled"] is args.enabled)
    ]
    emit({"operation": "list_monitors", "registry_version": REGISTRY_VERSION, "result_count": len(records), "results": records})


def audit_source_depth(args: argparse.Namespace) -> None:
    sources = {item["id"]: item for item in load_jsonl("sources.jsonl")}
    source = sources.get(args.source_id)
    if source is None:
        emit(
            {
                "operation": "audit_source_depth",
                "registry_version": REGISTRY_VERSION,
                "error": "source_not_found",
                "source_id": args.source_id,
                "recommended_action": "Search for an existing source record before nominating a new institution and source.",
            }
        )
        raise SystemExit(2)
    emit(
        {
            "operation": "audit_source_depth",
            "registry_version": REGISTRY_VERSION,
            "profile": build_source_depth_profile(source),
        }
    )


def audit_all_source_depth(_args: argparse.Namespace) -> None:
    profiles = [
        build_source_depth_profile(source)
        for source in load_jsonl("sources.jsonl")
    ]
    stage_counts: dict[str, int] = {}
    for profile in profiles:
        stage = profile["profile_stage"]
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    emit(
        {
            "operation": "audit_all_source_depth",
            "registry_version": REGISTRY_VERSION,
            "source_count": len(profiles),
            "stage_counts": dict(sorted(stage_counts.items())),
            "variable_matching_ready_sources": sum(
                1 for item in profiles if item["variable_matching_ready"]
            ),
            "profiles": profiles,
            "warnings": [
                "Depth stages describe registered GRDR content, not complete upstream database inventories."
            ],
        }
    )


def audit_indicator_project(args: argparse.Namespace) -> None:
    """Audit a question-specific literature and indicator project."""

    from indicator_builder import audit_project

    result = audit_project(args.project_dir, ROOT)
    emit(result)
    if result["errors"]:
        raise SystemExit(2)


def run_research_operation(operation: str, callback: Any) -> None:
    try:
        emit(callback())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        emit(
            {
                "operation": operation,
                "registry_version": REGISTRY_VERSION,
                "error": type(exc).__name__,
                "message": str(exc),
            }
        )
        raise SystemExit(2) from exc


def start_research_project_command(args: argparse.Namespace) -> None:
    from research_project import start_research_project

    run_research_operation(
        "start_research_project",
        lambda: start_research_project(args.spec_file, args.project_dir),
    )


def research_project_status_command(args: argparse.Namespace) -> None:
    from research_project import research_project_status

    run_research_operation(
        "research_project_status",
        lambda: research_project_status(args.project_dir),
    )


def approve_human_gate_command(args: argparse.Namespace) -> None:
    from research_project import approve_human_gate

    run_research_operation(
        "approve_human_gate",
        lambda: approve_human_gate(args.project_dir, args.gate, args.reviewer, args.notes),
    )


def resume_research_project_command(args: argparse.Namespace) -> None:
    from research_project import resume_research_project

    run_research_operation(
        "resume_research_project",
        lambda: resume_research_project(args.project_dir),
    )


def match_indicators_command(args: argparse.Namespace) -> None:
    from research_project import perform_matching

    run_research_operation(
        "match_indicators",
        lambda: perform_matching(args.project_dir),
    )


def expand_from_data_gaps_command(args: argparse.Namespace) -> None:
    from research_project import expand_from_data_gaps

    run_research_operation(
        "expand_from_data_gaps",
        lambda: expand_from_data_gaps(args.project_dir),
    )


def rerun_matching_command(args: argparse.Namespace) -> None:
    from research_project import perform_matching

    run_research_operation(
        "rerun_matching",
        lambda: perform_matching(args.project_dir, rerun=True),
    )


def start_database_deep_map_command(args: argparse.Namespace) -> None:
    from database_deep_map import start_database_deep_map

    run_research_operation(
        "start_database_deep_map",
        lambda: start_database_deep_map(args.spec_file, args.project_dir),
    )


def list_database_route_modules_command(_args: argparse.Namespace) -> None:
    from database_deep_map_planner import list_database_route_modules

    run_research_operation("list_database_route_modules", list_database_route_modules)


def plan_database_deep_map_command(args: argparse.Namespace) -> None:
    from database_deep_map_planner import audit_database_deep_map_plan, build_database_deep_map_plan

    def operation() -> dict[str, Any]:
        plan = build_database_deep_map_plan(args.intake_file)
        audit = audit_database_deep_map_plan(plan)
        output_path = None
        if args.output:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            output_path = str(output)
        return {"operation": "plan_database_deep_map", "output_path": output_path, "plan": plan, "audit": audit}

    run_research_operation("plan_database_deep_map", operation)


def audit_database_deep_map_plan_command(args: argparse.Namespace) -> None:
    from database_deep_map_planner import audit_database_deep_map_plan

    run_research_operation("audit_database_deep_map_plan", lambda: audit_database_deep_map_plan(args.plan_file))


def upgrade_database_deep_map_command(args: argparse.Namespace) -> None:
    from database_deep_map import upgrade_database_deep_map

    run_research_operation("upgrade_database_deep_map", lambda: upgrade_database_deep_map(args.project_dir))


def database_deep_map_status_command(args: argparse.Namespace) -> None:
    from database_deep_map import database_deep_map_status

    run_research_operation(
        "database_deep_map_status",
        lambda: database_deep_map_status(args.project_dir),
    )


def resume_database_deep_map_command(args: argparse.Namespace) -> None:
    from database_deep_map import resume_database_deep_map

    run_research_operation(
        "resume_database_deep_map",
        lambda: resume_database_deep_map(args.project_dir),
    )


def record_database_deep_map_phase_command(args: argparse.Namespace) -> None:
    from database_deep_map import record_database_deep_map_phase

    run_research_operation(
        "record_database_deep_map_phase",
        lambda: record_database_deep_map_phase(args.project_dir, args.update_file),
    )


def record_database_deep_map_stage_command(args: argparse.Namespace) -> None:
    from database_deep_map import record_database_deep_map_stage

    run_research_operation(
        "record_database_deep_map_stage",
        lambda: record_database_deep_map_stage(args.project_dir, args.update_file),
    )


def record_database_deep_map_spine_command(args: argparse.Namespace) -> None:
    from database_deep_map import record_database_deep_map_spine

    run_research_operation(
        "record_database_deep_map_spine",
        lambda: record_database_deep_map_spine(args.project_dir, args.update_file),
    )


def record_database_deep_map_check_command(args: argparse.Namespace) -> None:
    from database_deep_map import record_database_deep_map_check

    run_research_operation(
        "record_database_deep_map_check",
        lambda: record_database_deep_map_check(args.project_dir, args.update_file),
    )


def record_database_deep_map_human_gate_command(args: argparse.Namespace) -> None:
    from database_deep_map import record_database_deep_map_human_gate

    run_research_operation(
        "record_database_deep_map_human_gate",
        lambda: record_database_deep_map_human_gate(args.project_dir, args.gate, args.decision, args.reviewer, args.notes),
    )


def audit_database_deep_map_command(args: argparse.Namespace) -> None:
    from database_deep_map import audit_database_deep_map

    run_research_operation(
        "audit_database_deep_map",
        lambda: audit_database_deep_map(args.project_dir),
    )


def complete_database_deep_map_command(args: argparse.Namespace) -> None:
    from database_deep_map import complete_database_deep_map

    run_research_operation(
        "complete_database_deep_map",
        lambda: complete_database_deep_map(args.project_dir),
    )


def stats(_args: argparse.Namespace) -> None:
    collections = {
        entity_type: load_jsonl(filename)
        for entity_type, filename in ENTITY_FILES.items()
    }
    sources = collections["source"]
    relationships = load_jsonl("relationships.jsonl")

    def frequencies(values: Iterable[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for value in values:
            counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))

    emit(
        {
            "operation": "stats",
            "registry_version": REGISTRY_VERSION,
            "counts": {
                **{
                    {
                        "institution": "institutions",
                        "source": "sources",
                        "dataset": "datasets",
                        "data_structure": "data_structures",
                        "resource": "resources",
                        "data_element": "data_elements",
                        "construct": "constructs",
                        "semantic_node": "semantic_nodes",
                        "variable": "variables",
                        "adapter": "adapters",
                        "storage": "storage_records",
                        "monitor": "monitors",
                        "source_profile": "source_profiles",
                    }[name]: len(records)
                    for name, records in collections.items()
                },
                "relationships": len(relationships),
            },
            "verification_by_entity": {
                name: verification_counts(records)
                for name, records in collections.items()
            },
            "source_classes": frequencies(
                item for source in sources for item in source["source_classes"]
            ),
            "disciplines": frequencies(
                item for source in sources for item in source["scope"]["disciplines"]
            ),
        }
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Query the local GRDR registry")
    commands = root.add_subparsers(dest="command", required=True)

    search = commands.add_parser("search-sources", help="Search source records")
    search.add_argument("--query")
    search.add_argument("--discipline")
    search.add_argument("--topic")
    search.add_argument("--source-class")
    search.add_argument(
        "--geography",
        choices=["global", "multiregional", "regional", "national", "subnational", "site_specific", "non_geographic", "mixed", "unknown"],
    )
    search.add_argument(
        "--verification",
        choices=["unverified", "partially_verified", "verified", "stale", "conflicted", "deprecated", "unavailable"],
    )
    search.add_argument("--limit", type=int, default=20)
    search.set_defaults(handler=search_sources)

    search_dataset = commands.add_parser("search-datasets", help="Search dataset records")
    search_dataset.add_argument("--query")
    search_dataset.add_argument("--discipline")
    search_dataset.add_argument("--topic")
    search_dataset.add_argument("--observation-unit")
    search_dataset.add_argument(
        "--verification",
        choices=["unverified", "partially_verified", "verified", "stale", "conflicted", "deprecated", "unavailable"],
    )
    search_dataset.add_argument("--limit", type=int, default=20)
    search_dataset.set_defaults(handler=search_datasets)

    search_variable = commands.add_parser("search-variables", help="Search variable records")
    search_variable.add_argument("--query")
    search_variable.add_argument("--construct")
    search_variable.add_argument("--dataset-id")
    search_variable.add_argument("--role")
    search_variable.add_argument("--measurement-type")
    search_variable.add_argument(
        "--verification",
        choices=["unverified", "partially_verified", "verified", "stale", "conflicted", "deprecated", "unavailable"],
    )
    search_variable.add_argument("--limit", type=int, default=20)
    search_variable.set_defaults(handler=search_variables)

    search_semantics = commands.add_parser("search-semantic-nodes", help="Search the multi-parent scientific-semantic graph")
    search_semantics.add_argument("--query")
    search_semantics.add_argument("--node-type", choices=["discipline", "subdiscipline", "research_field", "research_object", "system", "phenomenon", "process", "state", "population", "observation_unit", "analysis_unit", "application_area", "method", "other"])
    search_semantics.set_defaults(handler=search_semantic_nodes)

    get = commands.add_parser("get-source", help="Get a source and related records")
    get.add_argument("source_id")
    get.set_defaults(handler=get_source)

    get_dataset_command = commands.add_parser("get-dataset", help="Get a dataset with sources, resources, and variables")
    get_dataset_command.add_argument("dataset_id")
    get_dataset_command.set_defaults(handler=get_dataset)

    get_variable_command = commands.add_parser("get-variable", help="Get a variable with datasets and constructs")
    get_variable_command.add_argument("variable_id")
    get_variable_command.set_defaults(handler=get_variable)

    get_semantic_command = commands.add_parser("get-semantic-node", help="Get one scientific-semantic node with parents, children, and relationships")
    get_semantic_command.add_argument("semantic_node_id")
    get_semantic_command.set_defaults(handler=get_semantic_node)

    get_element_command = commands.add_parser("get-data-element", help="Get a source-native dimension, measure, identifier, or attribute")
    get_element_command.add_argument("element_id")
    get_element_command.set_defaults(handler=get_data_element)

    get_structure_command = commands.add_parser("get-data-structure", help="Get a database-internal structure with linked datasets, elements, variables, and access resources")
    get_structure_command.add_argument("data_structure_id")
    get_structure_command.set_defaults(handler=get_data_structure)

    trace = commands.add_parser("trace-provenance", help="Traverse evidence-backed registry relationships")
    trace.add_argument("entity_id")
    trace.add_argument("--depth", type=int, default=4)
    trace.set_defaults(handler=trace_provenance)

    diagnose = commands.add_parser("diagnose-coverage", help="Compare a structured research request with registered constructs and variables")
    diagnose.add_argument("request_file")
    diagnose.set_defaults(handler=diagnose_coverage)

    source_depth = commands.add_parser(
        "audit-source-depth",
        help="Audit one database across the six GRDR profiling layers",
    )
    source_depth.add_argument("source_id")
    source_depth.set_defaults(handler=audit_source_depth)

    all_source_depth = commands.add_parser(
        "audit-all-source-depth",
        help="Audit six-layer profiling depth for every registered database",
    )
    all_source_depth.set_defaults(handler=audit_all_source_depth)

    list_routes = commands.add_parser(
        "list-database-route-modules",
        help="List extensible database-shape route contracts and their completion facets",
    )
    list_routes.set_defaults(handler=list_database_route_modules_command)

    plan_deep_map = commands.add_parser(
        "plan-database-deep-map",
        help="Diagnose an open-world database intake and generate a route-contract execution plan",
    )
    plan_deep_map.add_argument("intake_file")
    plan_deep_map.add_argument("--output")
    plan_deep_map.set_defaults(handler=plan_database_deep_map_command)

    audit_deep_map_plan = commands.add_parser(
        "audit-database-deep-map-plan",
        help="Audit a generated database diagnostic and route-contract plan",
    )
    audit_deep_map_plan.add_argument("plan_file")
    audit_deep_map_plan.set_defaults(handler=audit_database_deep_map_plan_command)

    start_deep_map = commands.add_parser(
        "start-database-deep-map",
        help="Create a persistent, bounded database deep-map project and work-unit ledger",
    )
    start_deep_map.add_argument("spec_file")
    start_deep_map.add_argument("--project-dir")
    start_deep_map.set_defaults(handler=start_database_deep_map_command)

    upgrade_deep_map = commands.add_parser(
        "upgrade-database-deep-map",
        help="Upgrade an older deep-map project to the current diagnostic plan and contract-check ledger",
    )
    upgrade_deep_map.add_argument("project_dir")
    upgrade_deep_map.set_defaults(handler=upgrade_database_deep_map_command)

    deep_map_status = commands.add_parser(
        "database-deep-map-status",
        help="Report strict and mapped progress for a database deep-map project",
    )
    deep_map_status.add_argument("project_dir")
    deep_map_status.set_defaults(handler=database_deep_map_status_command)

    resume_deep_map = commands.add_parser(
        "resume-database-deep-map",
        help="Select the next required phase or work-unit stage without skipping completion gates",
    )
    resume_deep_map.add_argument("project_dir")
    resume_deep_map.set_defaults(handler=resume_database_deep_map_command)

    record_deep_map_phase = commands.add_parser(
        "record-database-deep-map-phase",
        help="Apply an evidence-backed project-phase update",
    )
    record_deep_map_phase.add_argument("project_dir")
    record_deep_map_phase.add_argument("update_file")
    record_deep_map_phase.set_defaults(handler=record_database_deep_map_phase_command)

    record_deep_map_stage = commands.add_parser(
        "record-database-deep-map-stage",
        help="Apply a counted, evidence-backed update to one work-unit stage",
    )
    record_deep_map_stage.add_argument("project_dir")
    record_deep_map_stage.add_argument("update_file")
    record_deep_map_stage.set_defaults(handler=record_database_deep_map_stage_command)

    record_deep_map_spine = commands.add_parser(
        "record-database-deep-map-spine",
        help="Record and audit one structural, disciplinary, or variable-bridge spine checkpoint.",
    )
    record_deep_map_spine.add_argument("project_dir")
    record_deep_map_spine.add_argument("update_file")
    record_deep_map_spine.set_defaults(handler=record_database_deep_map_spine_command)

    record_deep_map_check = commands.add_parser(
        "record-database-deep-map-check",
        help="Record one evidence-backed route-contract acceptance check",
    )
    record_deep_map_check.add_argument("project_dir")
    record_deep_map_check.add_argument("update_file")
    record_deep_map_check.set_defaults(handler=record_database_deep_map_check_command)

    record_deep_map_gate = commands.add_parser(
        "record-database-deep-map-human-gate",
        help="Record an explicit named human database-governance decision; never self-approve",
    )
    record_deep_map_gate.add_argument("project_dir")
    record_deep_map_gate.add_argument("gate")
    record_deep_map_gate.add_argument("--decision", choices=["approved", "rejected", "not_applicable"], required=True)
    record_deep_map_gate.add_argument("--reviewer", required=True)
    record_deep_map_gate.add_argument("--notes", required=True)
    record_deep_map_gate.set_defaults(handler=record_database_deep_map_human_gate_command)

    audit_deep_map = commands.add_parser(
        "audit-database-deep-map",
        help="Audit schemas, registry references, counts, blockers, and strict completion",
    )
    audit_deep_map.add_argument("project_dir")
    audit_deep_map.set_defaults(handler=audit_database_deep_map_command)

    complete_deep_map = commands.add_parser(
        "complete-database-deep-map",
        help="Declare bounded completion only after every strict gate passes",
    )
    complete_deep_map.add_argument("project_dir")
    complete_deep_map.set_defaults(handler=complete_database_deep_map_command)

    indicator_project = commands.add_parser(
        "audit-indicator-project",
        help="Audit literature evidence, indicator hierarchy, human gates, and variable mappings",
    )
    indicator_project.add_argument("project_dir")
    indicator_project.set_defaults(handler=audit_indicator_project)

    start_project = commands.add_parser(
        "start-research-project",
        help="Create a persisted exploratory project from an AI-generated question and indicator specification",
    )
    start_project.add_argument("spec_file")
    start_project.add_argument("--project-dir")
    start_project.set_defaults(handler=start_research_project_command)

    project_status = commands.add_parser(
        "research-project-status",
        help="Report workflow, audit, gates, mappings, and data gaps for a research project",
    )
    project_status.add_argument("project_dir")
    project_status.set_defaults(handler=research_project_status_command)

    approve_gate = commands.add_parser(
        "approve-human-gate",
        help="Record an explicit named human approval; never invoke without the reviewer's instruction",
    )
    approve_gate.add_argument("project_dir")
    approve_gate.add_argument("gate", choices=["corpus_boundary", "indicator_framework", "contested_mappings"])
    approve_gate.add_argument("--reviewer", required=True)
    approve_gate.add_argument("--notes", required=True)
    approve_gate.set_defaults(handler=approve_human_gate_command)

    resume_project = commands.add_parser(
        "resume-research-project",
        help="Advance a valid project to its next executable or human-gated step",
    )
    resume_project.add_argument("project_dir")
    resume_project.set_defaults(handler=resume_research_project_command)

    match_project = commands.add_parser(
        "match-indicators",
        help="Match every leaf indicator to exact registered constructs and variables",
    )
    match_project.add_argument("project_dir")
    match_project.set_defaults(handler=match_indicators_command)

    expand_gaps = commands.add_parser(
        "expand-from-data-gaps",
        help="Turn current-snapshot not-found mappings into bounded source-profiling leads",
    )
    expand_gaps.add_argument("project_dir")
    expand_gaps.set_defaults(handler=expand_from_data_gaps_command)

    rerun_project = commands.add_parser(
        "rerun-matching",
        help="Replace project mappings after registry expansion and retain attempt history",
    )
    rerun_project.add_argument("project_dir")
    rerun_project.set_defaults(handler=rerun_matching_command)

    adapters = commands.add_parser("list-adapters", help="List optional data-access adapters")
    adapters.add_argument("--source-id")
    adapters.add_argument("--status", choices=["operational", "degraded", "failing", "untested", "disabled", "deprecated"])
    adapters.add_argument("--storage-mode", choices=["local_snapshot", "federated_access", "controlled_access_pointer"])
    adapters.set_defaults(handler=list_adapters)

    storage = commands.add_parser("list-storage", help="List local, federated, and controlled-access holdings")
    storage.add_argument("--dataset-id")
    storage.add_argument("--mode", choices=["local_snapshot", "federated_access", "controlled_access_pointer"])
    storage.set_defaults(handler=list_storage)

    monitors = commands.add_parser("list-monitors", help="List upstream monitors")
    monitors.add_argument("--status", choices=["passing", "changed", "degraded", "failing", "never_run", "disabled"])
    monitor_enabled = monitors.add_mutually_exclusive_group()
    monitor_enabled.add_argument("--enabled", action="store_true", dest="enabled")
    monitor_enabled.add_argument("--disabled", action="store_false", dest="enabled")
    monitors.set_defaults(handler=list_monitors, enabled=None)

    show_stats = commands.add_parser("stats", help="Show registry coverage statistics")
    show_stats.set_defaults(handler=stats)
    return root


def main() -> None:
    args = parser().parse_args()
    if hasattr(args, "limit") and args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if hasattr(args, "depth") and args.depth < 1:
        raise SystemExit("--depth must be at least 1")
    args.handler(args)


if __name__ == "__main__":
    main()
