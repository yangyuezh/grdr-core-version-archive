#!/usr/bin/env python3
"""Diagnose an open-world database intake and generate an auditable route plan."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "database_route_contracts.json"
SCHEMA_ROOT = ROOT / "schemas"
CRITICAL_DIMENSIONS = {
    "origin_types": "Original versus secondary production role is unresolved.",
    "production_modes": "The data-generating or production process is unresolved.",
    "structural_archetypes": "The database's internal structural archetype is unresolved.",
    "lifecycle_modes": "Snapshot, revision, append, rolling, or stream lifecycle is unresolved.",
    "versioning_models": "Version and change semantics are unresolved.",
    "access_regimes": "Access and authorization regime is unresolved.",
    "sensitivity_classes": "Sensitivity, privacy, ethics, security, or community-governance status is unresolved.",
    "scale_classes": "Scale and compute requirements are unresolved.",
}
SENSITIVE = {
    "personal", "health", "genetic", "financial", "commercially_sensitive",
    "national_security", "indigenous_or_community_governed", "confidential_business",
}
CONTROLLED_ACCESS = {"registered", "licensed", "restricted", "secure_environment", "application", "commercial"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def validate_schema(value: Any, schema_name: str, label: str) -> list[str]:
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError(
            "strict database planning requires jsonschema; install with "
            "python3 -m pip install -r requirements-validation.txt"
        ) from exc
    schema = read_json(SCHEMA_ROOT / schema_name)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = []
    for error in validator.iter_errors(value):
        location = ".".join(str(part) for part in error.path) or "<record>"
        errors.append(f"{label}:{location}: {error.message}")
    return errors


def load_contracts() -> dict[str, Any]:
    contracts = read_json(CONTRACT_PATH)
    errors = validate_schema(contracts, "database_route_contracts.schema.json", str(CONTRACT_PATH))
    route_ids = [item["id"] for item in contracts.get("route_modules", [])]
    if len(route_ids) != len(set(route_ids)):
        errors.append("route contract registry contains duplicate route IDs")
    known = set(route_ids)
    for item in contracts.get("route_modules", []):
        for fallback in item["fallback_routes"]:
            if fallback not in known:
                errors.append(f"route {item['id']} references unknown fallback {fallback}")
    if errors:
        raise ValueError("; ".join(errors))
    return contracts


def contract_index(contracts: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    value = contracts or load_contracts()
    return {item["id"]: item for item in value["route_modules"]}


def signal_values(intake: dict[str, Any], key: str) -> set[str]:
    observations = intake["observations"]
    if key == "boundary_types":
        return {intake["scope"]["boundary_type"]}
    value = observations.get(key)
    if isinstance(value, list):
        return set(value)
    if isinstance(value, str):
        return {value}
    return set()


def route_matches(intake: dict[str, Any], route: dict[str, Any]) -> bool:
    if route["id"] == "core_metadata":
        return True
    if route.get("trigger_mode") == "structural_only":
        expected = route["triggers"].get("structural_archetypes", [])
        return bool(signal_values(intake, "structural_archetypes") & set(expected))
    return any(signal_values(intake, key) & set(expected) for key, expected in route["triggers"].items())


def unresolved_dimensions(intake: dict[str, Any]) -> list[str]:
    observations = intake["observations"]
    unresolved = []
    for key, message in CRITICAL_DIMENSIONS.items():
        values = observations[key]
        if not values or set(values) <= {"unknown"}:
            unresolved.append(message)
    scope = intake["scope"]
    strategy = intake["work_unit_strategy"]
    if scope["boundary_type"] == "unknown" or not scope["boundary_statement"].strip():
        unresolved.append("A reproducible boundary statement and boundary type are missing.")
    if scope["snapshot_at"] is None:
        unresolved.append("A dated retrieval, release, or rolling-window anchor is missing.")
    if strategy["denominator_strategy"] == "unknown":
        unresolved.append("The work-unit denominator strategy is unresolved.")
    if strategy["denominator_strategy"] == "explicit_count" and strategy["expected_count"] is None:
        unresolved.append("The denominator strategy requires an expected work-unit count.")
    if set(strategy["unit_types"]) <= {"unknown"} or not strategy["identity_rule"].strip():
        unresolved.append("Work-unit type or stable identity rule is unresolved.")
    if not strategy["partition_rule"].strip() or not strategy["ordering_rule"].strip():
        unresolved.append("Work-unit partition or deterministic ordering rule is unresolved.")
    if observations["metadata_maturity"] == "unknown":
        unresolved.append("Metadata maturity and the basis for structural recovery are unresolved.")
    if set(observations["origin_types"]) & {"secondary", "hybrid"} and set(observations["provenance_roles"]) <= {"unknown"}:
        unresolved.append("A secondary or hybrid source requires its aggregation, harmonization, mirror, or federation role.")
    if not intake["evidence"]:
        unresolved.append("No evidence supports the preflight identity, diagnosis, or boundary.")
    if intake["goal"]["scope_mode"] == "exhaustive_snapshot" and strategy["denominator_strategy"] in {"not_enumerable", "rolling_window"}:
        unresolved.append("An exhaustive snapshot claim conflicts with a non-enumerable or rolling denominator.")
    return list(dict.fromkeys(unresolved))


def human_gates(intake: dict[str, Any]) -> list[dict[str, str]]:
    observations = intake["observations"]
    sensitivity = set(observations["sensitivity_classes"])
    access = set(observations["access_regimes"])
    gates: list[dict[str, str]] = []
    if sensitivity & SENSITIVE:
        gates.append({
            "gate": "privacy_ethics_and_sovereignty",
            "reason": "Sensitive, personal, health, genetic, financial, security, or community-governed data require an explicit human decision.",
            "required_before": "observation_access", "status": "pending", "reviewer": None, "decided_at": None, "notes": None,
        })
    if access & CONTROLLED_ACCESS:
        gates.append({
            "gate": "access_authorization",
            "reason": "Registration, license, application, payment, or secure-environment access cannot be inferred or self-approved by the Agent.",
            "required_before": "observation_access", "status": "pending", "reviewer": None, "decided_at": None, "notes": None,
        })
    if "indigenous_or_community_governed" in sensitivity:
        gates.append({
            "gate": "community_governance",
            "reason": "Community or Indigenous governance requirements must be resolved by the authorized rights holder.",
            "required_before": "metadata_access", "status": "pending", "reviewer": None, "decided_at": None, "notes": None,
        })
    if intake["goal"]["scope_mode"] == "question_driven":
        gates.append({
            "gate": "semantic_scope_review",
            "reason": "Question-driven completion must be reviewed as question-bounded and cannot be promoted to full-database completion.",
            "required_before": "publication", "status": "pending", "reviewer": None, "decided_at": None, "notes": None,
        })
    unique = {(item["gate"], item["required_before"]): item for item in gates}
    return list(unique.values())


def risk_flags(intake: dict[str, Any]) -> list[str]:
    observations = intake["observations"]
    risks = []
    if set(observations["lifecycle_modes"]) & {"append_only", "mutable", "rolling_window", "real_time_stream", "ephemeral"}:
        risks.append("dynamic_or_nonstationary_source")
    if set(observations["scale_classes"]) & {"large", "very_large", "unbounded_stream"}:
        risks.append("partitioning_or_compute_required")
    if observations["metadata_maturity"] in {"partial", "inferred", "undocumented", "unknown"}:
        risks.append("metadata_incomplete_or_inferred")
    if set(observations["origin_types"]) & {"secondary", "hybrid"}:
        risks.append("upstream_provenance_required")
    if set(observations["sensitivity_classes"]) & SENSITIVE:
        risks.append("sensitive_or_governed_data")
    if len(observations["languages"]) > 1 or "unknown" in observations["languages"]:
        risks.append("multilingual_or_encoding_variation")
    if set(observations["access_regimes"]) & CONTROLLED_ACCESS:
        risks.append("controlled_access")
    return risks


def merge_facets(selected_routes: list[str], routes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for route_id in selected_routes:
        for facet in routes[route_id]["facets"]:
            key = (facet["id"], facet["scope"], facet["stage"])
            if key not in merged:
                merged[key] = {**facet, "source_routes": [route_id]}
            elif route_id not in merged[key]["source_routes"]:
                merged[key]["source_routes"].append(route_id)
    return list(merged.values())


def build_database_deep_map_plan_from_intake(intake: dict[str, Any]) -> dict[str, Any]:
    errors = validate_schema(intake, "database_deep_map_intake.schema.json", "intake")
    if errors:
        raise ValueError("; ".join(errors))
    contracts = load_contracts()
    routes = contract_index(contracts)
    explicit = intake["explicit_route_modules"]
    unknown_explicit = [item for item in explicit if item not in routes]
    if unknown_explicit:
        raise ValueError("unknown explicit route modules: " + ", ".join(unknown_explicit))
    selected = []
    for route in contracts["route_modules"]:
        if route["id"] in explicit or route_matches(intake, route):
            selected.append(route["id"])
    if "core_metadata" not in selected:
        selected.insert(0, "core_metadata")
    specialized = [item for item in selected if item not in {"core_metadata", "derived_provenance", "restricted_access", "open_world_custom"}]
    observed_unknown = any(
        "unknown" in signal_values(intake, key) or "other" in signal_values(intake, key)
        for key in ("structural_archetypes", "content_modalities", "lifecycle_modes")
    )
    if (not specialized or observed_unknown) and "open_world_custom" not in selected:
        selected.append("open_world_custom")
    unresolved = unresolved_dimensions(intake)
    gates = human_gates(intake)
    prohibited = set(intake["constraints"]["prohibited_actions"])
    if "metadata_mapping" in prohibited:
        status = "blocked"
    elif unresolved:
        status = "needs_evidence"
    elif gates:
        status = "ready_with_gates"
    else:
        status = "ready"
    return {
        "schema_version": "1.0.0",
        "route_contract_version": contracts["contract_version"],
        "source": intake["source"],
        "goal": intake["goal"],
        "diagnostic_dimensions": intake["observations"],
        "scope": intake["scope"],
        "work_unit_strategy": intake["work_unit_strategy"],
        "selected_route_modules": selected,
        "required_facets": merge_facets(selected, routes),
        "unresolved_critical": unresolved,
        "human_gates": gates,
        "risk_flags": risk_flags(intake),
        "fallback_policy": {
            "unknown_structure": "Use open_world_custom; preserve observed facts; propose a reusable route only after evidence and tests.",
            "access_failure": "Continue public metadata mapping, record a typed blocker, and never infer observation availability.",
            "scale": "Partition by a stable native order or manifest; preserve counts, range boundaries, and checksums.",
            "change": "Fingerprint the bounded universe and reopen affected checks and stages when upstream structure or version changes.",
            "semantic_ambiguity": "Retain source-native elements, defer Variable or Construct promotion, and request human review when consequential.",
        },
        "plan_status": status,
        "evidence": intake["evidence"],
        "generated_at": now(),
    }


def build_database_deep_map_plan(intake_file: str | Path) -> dict[str, Any]:
    intake = read_json(Path(intake_file).expanduser().resolve())
    # Accept either a standalone intake or a start specification that embeds it.
    # This keeps planning independently testable without forcing users to split files.
    if "diagnostic_intake" in intake:
        intake = intake["diagnostic_intake"]
    return build_database_deep_map_plan_from_intake(intake)


def audit_database_deep_map_plan(plan_or_path: dict[str, Any] | str | Path) -> dict[str, Any]:
    plan = plan_or_path if isinstance(plan_or_path, dict) else read_json(Path(plan_or_path).expanduser().resolve())
    errors = validate_schema(plan, "database_deep_map_plan.schema.json", "plan")
    contracts = load_contracts()
    routes = contract_index(contracts)
    selected = plan.get("selected_route_modules", [])
    for route_id in selected:
        if route_id not in routes:
            errors.append(f"plan references unknown route module {route_id}")
    if "core_metadata" not in selected:
        errors.append("plan must include core_metadata")
    if plan.get("route_contract_version") != contracts["contract_version"]:
        errors.append("plan route_contract_version does not match the current registry")
    if not errors:
        expected = merge_facets(selected, routes)
        expected_keys = {(item["id"], item["scope"], item["stage"]) for item in expected}
        actual_keys = {(item["id"], item["scope"], item["stage"]) for item in plan["required_facets"]}
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        errors.extend(f"plan is missing required facet {item}" for item in missing)
        errors.extend(f"plan contains unexpected facet {item}" for item in extra)
    status = plan.get("plan_status")
    pending_gates = [item for item in plan.get("human_gates", []) if item.get("status") == "pending"]
    rejected_gates = [item for item in plan.get("human_gates", []) if item.get("status") == "rejected"]
    if status == "ready" and (plan.get("unresolved_critical") or pending_gates or rejected_gates):
        errors.append("ready plan cannot retain critical unresolved, pending, or rejected gates")
    if status == "ready_with_gates" and not pending_gates:
        errors.append("ready_with_gates plan requires at least one pending human gate")
    if status == "needs_evidence" and not plan.get("unresolved_critical"):
        errors.append("needs_evidence plan requires unresolved_critical items")
    return {
        "operation": "audit_database_deep_map_plan",
        "plan_status": status,
        "selected_route_modules": selected,
        "required_facet_count": len(plan.get("required_facets", [])),
        "unresolved_critical": plan.get("unresolved_critical", []),
        "human_gates": plan.get("human_gates", []),
        "errors": errors,
        "valid": not errors,
    }


def list_database_route_modules() -> dict[str, Any]:
    contracts = load_contracts()
    return {
        "operation": "list_database_route_modules",
        "contract_version": contracts["contract_version"],
        "route_modules": [
            {
                "id": item["id"],
                "label": item["label"],
                "description": item["description"],
                "module_kinds": item["module_kinds"],
                "facet_count": len(item["facets"]),
                "fallback_routes": item["fallback_routes"],
            }
            for item in contracts["route_modules"]
        ],
    }
