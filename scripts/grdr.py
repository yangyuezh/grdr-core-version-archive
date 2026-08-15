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
    "resource": "resources.jsonl",
    "construct": "constructs.jsonl",
    "variable": "variables.jsonl",
    "adapter": "adapters.jsonl",
    "storage": "storage.jsonl",
    "monitor": "monitors.jsonl",
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
                    "dataset_ids": item["dataset_ids"],
                    "construct_ids": item["construct_ids"],
                    "role_candidates": item["role_candidates"],
                    "observation_unit": item["observation_unit"],
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
    variables = load_jsonl("variables.jsonl")
    emit(
        {
            "operation": "get_dataset",
            "registry_version": REGISTRY_VERSION,
            "dataset": dataset,
            "sources": [sources[item] for item in dataset["source_ids"] if item in sources],
            "resources": [item for item in resources if args.dataset_id in item["dataset_ids"]],
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
    emit(
        {
            "operation": "get_variable",
            "registry_version": REGISTRY_VERSION,
            "variable": variable,
            "datasets": [datasets[item] for item in variable["dataset_ids"] if item in datasets],
            "constructs": [constructs[item] for item in variable["construct_ids"] if item in constructs],
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
                        "resource": "resources",
                        "construct": "constructs",
                        "variable": "variables",
                        "adapter": "adapters",
                        "storage": "storage_records",
                        "monitor": "monitors",
                    }[name]: len(records)
                    for name, records in collections.items()
                },
                "relationships": len(relationships),
            },
            "verification_by_entity": {
                name: frequencies(record["verification"]["status"] for record in records)
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

    get = commands.add_parser("get-source", help="Get a source and related records")
    get.add_argument("source_id")
    get.set_defaults(handler=get_source)

    get_dataset_command = commands.add_parser("get-dataset", help="Get a dataset with sources, resources, and variables")
    get_dataset_command.add_argument("dataset_id")
    get_dataset_command.set_defaults(handler=get_dataset)

    get_variable_command = commands.add_parser("get-variable", help="Get a variable with datasets and constructs")
    get_variable_command.add_argument("variable_id")
    get_variable_command.set_defaults(handler=get_variable)

    trace = commands.add_parser("trace-provenance", help="Traverse evidence-backed registry relationships")
    trace.add_argument("entity_id")
    trace.add_argument("--depth", type=int, default=4)
    trace.set_defaults(handler=trace_provenance)

    diagnose = commands.add_parser("diagnose-coverage", help="Compare a structured research request with registered constructs and variables")
    diagnose.add_argument("request_file")
    diagnose.set_defaults(handler=diagnose_coverage)

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
