#!/usr/bin/env python3
"""Orchestrate GRDR research-question projects from scaffold through gap expansion."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

import distributed_runtime as distributed

from indicator_builder import audit_project


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT / "research_projects"
PROJECT_FILES = {
    "project": "project.json",
    "literature": "literature.jsonl",
    "evidence": "evidence_units.jsonl",
    "indicators": "indicators.jsonl",
    "mappings": "mappings.jsonl",
    "workflow": "workflow.json",
    "gaps": "data_gaps.jsonl",
}
SEMANTIC_PROJECT_FILES = {
    "candidates": "semantic_candidates.jsonl",
    "alignments": "semantic_alignments.jsonl",
    "paths": "semantic_paths.jsonl",
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
STOPWORDS = {
    "and", "the", "for", "from", "with", "per", "total", "annual", "rate",
    "level", "use", "using", "country", "countries", "year", "years", "of",
    "in", "to", "by", "or", "a", "an", "与", "的", "及", "和", "水平", "年度",
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    result = re.sub(r"[^a-z0-9]+", "-", normalized.casefold()).strip("-")
    if not result:
        raise ValueError(f"cannot form a stable identifier from {value!r}")
    return result


def normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold()))


def tokens(*values: str) -> list[str]:
    found = {
        token
        for value in values
        for token in normalize(value).split()
        if len(token) >= 3 and token not in STOPWORDS
    }
    return sorted(found)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n" for value in values), encoding="utf-8")


def resolve_project_dir(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        candidate = PROJECT_ROOT / path
        path = candidate if candidate.exists() or len(path.parts) == 1 else ROOT / path
    return path.resolve()


def require_project(path: Path) -> None:
    missing = [name for name in PROJECT_FILES.values() if not (path / name).is_file()]
    if missing:
        raise ValueError(f"incomplete research project {path}: missing {', '.join(missing)}")


def append_history(workflow: dict[str, Any], operation: str, summary: str) -> None:
    stamp = now()
    workflow["last_operation"] = operation
    workflow["updated_at"] = stamp
    workflow["history"].append({"timestamp": stamp, "operation": operation, "summary": summary})


def validate_auxiliary(project_dir: Path) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return []
    errors = []
    for filename, schema_name, values in [
        ("workflow.json", "research_workflow.schema.json", [read_json(project_dir / "workflow.json")]),
        ("data_gaps.jsonl", "data_gap.schema.json", read_jsonl(project_dir / "data_gaps.jsonl")),
    ]:
        schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        for index, value in enumerate(values, 1):
            for error in validator.iter_errors(value):
                location = ".".join(str(part) for part in error.path) or "<record>"
                errors.append(f"{filename}:{index}:{location}: {error.message}")
    from semantic_resolver import semantic_file_errors

    errors.extend(semantic_file_errors(project_dir))
    return sorted(errors)


def build_indicator_records(spec: dict[str, Any], project_id: str, project_slug: str) -> list[dict[str, Any]]:
    nodes = spec.get("indicators")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError("start specification requires a non-empty indicators array")
    keyed: dict[str, dict[str, Any]] = {}
    for node in nodes:
        key = node.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError("every indicator specification requires a non-empty key")
        for field in ("name", "node_type", "definition"):
            if not isinstance(node.get(field), str) or not node[field].strip():
                raise ValueError(f"indicator {key}: {field} is required")
        if key in keyed:
            raise ValueError(f"duplicate indicator key: {key}")
        keyed[key] = node
    children = {key: [] for key in keyed}
    for key, node in keyed.items():
        parent = node.get("parent_key")
        if parent is not None:
            if parent not in keyed:
                raise ValueError(f"indicator {key}: unknown parent_key {parent}")
            children[parent].append(key)
    records = []
    for key, node in keyed.items():
        leaf = not children[key]
        operational = node.get("operational_spec")
        if leaf and operational is None:
            raise ValueError(f"leaf indicator {key}: operational_spec is required")
        records.append(
            {
                "schema_version": "0.1.0",
                "id": f"grdr:research-indicator:{project_slug}-{slug(key)}",
                "project_id": project_id,
                "name": node["name"],
                "parent_indicator_id": f"grdr:research-indicator:{project_slug}-{slug(node['parent_key'])}" if node.get("parent_key") else None,
                "node_type": node["node_type"],
                "definition": node["definition"],
                "is_leaf": leaf,
                "provenance_type": "topic_scaffold",
                "evidence_unit_ids": [],
                "synonyms": node.get("synonyms", []),
                "operational_spec": operational,
                "review_status": "agent_candidate",
            }
        )
    return records


def start_research_project(spec_file: str | Path, project_dir: str | Path | None = None) -> dict[str, Any]:
    spec_path = Path(spec_file).expanduser().resolve()
    spec = read_json(spec_path)
    for field in ("title", "research_question"):
        if not isinstance(spec.get(field), str) or not spec[field].strip():
            raise ValueError(f"start specification requires a non-empty {field}")
    project_slug = slug(spec.get("project_id") or spec.get("title") or "")
    target = Path(project_dir).expanduser().resolve() if project_dir else (PROJECT_ROOT / project_slug).resolve()
    if target.exists():
        raise ValueError(f"research project already exists: {target}")
    project_id = f"grdr:research-project:{project_slug}"
    indicator_records = build_indicator_records(spec, project_id, project_slug)
    timestamp = now()
    project = {
        "schema_version": "0.1.0",
        "id": project_id,
        "title": spec["title"],
        "research_question": spec["research_question"],
        "evidence_stage": "topic_scaffold",
        "analysis_methods": spec.get("analysis_methods", ["theory_deduction"]),
        "corpus_protocol": {
            "search_strategy": None,
            "sources": [],
            "inclusion_criteria": [],
            "exclusion_criteria": [],
            "date_boundary": None,
            "languages": [],
            "saturation_rule": None,
        },
        "human_gates": {
            "corpus_boundary": {"status": "exploratory_only", "reviewer": None, "reviewed_at": None, "notes": "No literature corpus was supplied; all indicators remain a topic scaffold."},
            "indicator_framework": {"status": "pending", "reviewer": None, "reviewed_at": None, "notes": "Human approval is required before treating the framework as formal."},
            "contested_mappings": {"status": "not_required", "reviewer": None, "reviewed_at": None, "notes": "No contested mappings have been generated."},
        },
        "agent_provenance": {"executor": "ai_agent", "model": spec.get("model"), "workflow_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip()},
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    workflow = {
        "schema_version": "0.1.0",
        "project_id": project_id,
        "workflow_status": "initialized",
        "current_step": "indicator_scaffold",
        "matching_attempt": 0,
        "gap_expansion_round": 0,
        "last_operation": "start-research-project",
        "next_actions": ["resume-research-project"],
        "history": [{"timestamp": timestamp, "operation": "start-research-project", "summary": f"Created topic scaffold with {len(indicator_records)} indicator nodes."}],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    target.mkdir(parents=True)
    write_json(target / "project.json", project)
    write_jsonl(target / "literature.jsonl", [])
    write_jsonl(target / "evidence_units.jsonl", [])
    write_jsonl(target / "indicators.jsonl", indicator_records)
    write_jsonl(target / "mappings.jsonl", [])
    write_json(target / "workflow.json", workflow)
    write_jsonl(target / "data_gaps.jsonl", [])
    for filename in SEMANTIC_PROJECT_FILES.values():
        write_jsonl(target / filename, [])
    audit = audit_project(target, ROOT)
    auxiliary_errors = validate_auxiliary(target)
    if audit["errors"] or auxiliary_errors:
        raise ValueError("created project failed validation: " + "; ".join([*audit["errors"], *auxiliary_errors]))
    return {
        "operation": "start_research_project",
        "project_id": project_id,
        "project_dir": str(target),
        "evidence_stage": "topic_scaffold",
        "indicator_nodes": len(indicator_records),
        "leaf_indicators": sum(1 for item in indicator_records if item["is_leaf"]),
        "next_actions": workflow["next_actions"],
        "warnings": ["This is an exploratory topic scaffold, not a literature-grounded or human-approved indicator framework."],
    }


def resume_research_project(project_dir: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    project = read_json(target / "project.json")
    workflow = read_json(target / "workflow.json")
    indicators = read_jsonl(target / "indicators.jsonl")
    mappings = read_jsonl(target / "mappings.jsonl")
    gaps = read_jsonl(target / "data_gaps.jsonl")
    semantic_candidates = read_jsonl(target / SEMANTIC_PROJECT_FILES["candidates"]) if (target / SEMANTIC_PROJECT_FILES["candidates"]).is_file() else []
    semantic_alignments = read_jsonl(target / SEMANTIC_PROJECT_FILES["alignments"]) if (target / SEMANTIC_PROJECT_FILES["alignments"]).is_file() else []
    semantic_paths = read_jsonl(target / SEMANTIC_PROJECT_FILES["paths"]) if (target / SEMANTIC_PROJECT_FILES["paths"]).is_file() else []
    audit = audit_project(target, ROOT)
    if audit["errors"]:
        workflow["workflow_status"] = "blocked"
        workflow["current_step"] = "indicator_scaffold"
        workflow["next_actions"] = ["repair-project-records"]
        summary = f"Blocked by {len(audit['errors'])} audit errors."
    elif not indicators:
        workflow["workflow_status"] = "blocked"
        workflow["current_step"] = "indicator_scaffold"
        workflow["next_actions"] = ["build-indicator-scaffold"]
        summary = "Blocked because no indicator nodes exist."
    elif project["evidence_stage"] != "topic_scaffold" and project["human_gates"]["indicator_framework"]["status"] != "approved":
        workflow["workflow_status"] = "awaiting_human"
        workflow["current_step"] = "human_gate"
        workflow["next_actions"] = ["approve-human-gate indicator_framework"]
        summary = "Formal project is waiting for indicator-framework approval."
    elif mappings and any(item["status"] in {"open", "expansion_planned"} for item in gaps):
        workflow["workflow_status"] = "ready_to_match"
        workflow["current_step"] = "rematching"
        workflow["next_actions"] = ["prepare-semantic-candidates --replace"]
        summary = "Gap expansion records exist; rebuild semantic recall against the updated distributed registry before rematching."
    elif not semantic_candidates:
        workflow["workflow_status"] = "ready_to_match"
        workflow["current_step"] = "matching"
        workflow["next_actions"] = ["prepare-semantic-candidates"]
        summary = "Project is ready for full-text B candidate recall."
    elif not semantic_alignments:
        workflow["workflow_status"] = "ready_to_match"
        workflow["current_step"] = "matching"
        workflow["next_actions"] = ["align-research-indicators"]
        summary = "Semantic candidates exist; the Agent must persist one R→B decision for every leaf indicator."
    elif not semantic_paths and any(item["mapping_relation"] != "no_match" for item in semantic_alignments):
        workflow["workflow_status"] = "ready_to_match"
        workflow["current_step"] = "matching"
        workflow["next_actions"] = ["traverse-semantic-paths"]
        summary = "R→B alignments exist; traverse the stored graph to A variables and data structures."
    elif mappings:
        workflow["workflow_status"] = "completed"
        workflow["current_step"] = "completed"
        workflow["next_actions"] = ["research-project-status"]
        summary = "All current leaf indicators have mapping outcomes, complete semantic artifacts, and no open data gaps."
    else:
        workflow["workflow_status"] = "ready_to_match"
        workflow["current_step"] = "matching"
        workflow["next_actions"] = ["match-indicators"]
        summary = "The persisted semantic graph is ready for variable-fit matching."
    append_history(workflow, "resume-research-project", summary)
    write_json(target / "workflow.json", workflow)
    return {
        "operation": "resume_research_project",
        "project_id": project["id"],
        "workflow_status": workflow["workflow_status"],
        "current_step": workflow["current_step"],
        "next_actions": workflow["next_actions"],
        "audit_errors": audit["errors"],
        "summary": summary,
    }


def approve_human_gate(project_dir: str | Path, gate: str, reviewer: str, notes: str) -> dict[str, Any]:
    if gate not in {"corpus_boundary", "indicator_framework", "contested_mappings"}:
        raise ValueError(f"unknown human gate: {gate}")
    if not reviewer.strip() or not notes.strip():
        raise ValueError("human approval requires non-empty reviewer and notes")
    target = resolve_project_dir(project_dir)
    require_project(target)
    project = read_json(target / "project.json")
    workflow = read_json(target / "workflow.json")
    timestamp = now()
    project["human_gates"][gate] = {"status": "approved", "reviewer": reviewer, "reviewed_at": timestamp, "notes": notes}
    project["updated_at"] = timestamp
    if gate == "indicator_framework" and project["evidence_stage"] != "topic_scaffold":
        indicators = read_jsonl(target / "indicators.jsonl")
        for indicator in indicators:
            indicator["review_status"] = "approved_for_mapping" if indicator["is_leaf"] else "human_reviewed"
        write_jsonl(target / "indicators.jsonl", indicators)
        if project["evidence_stage"] == "indicator_synthesized":
            project["evidence_stage"] = "human_reviewed"
    if gate == "contested_mappings":
        mappings = read_jsonl(target / "mappings.jsonl")
        for mapping in mappings:
            if mapping["mapping_status"] in {"proxy_candidate", "definition_conflict"}:
                mapping["review_status"] = "human_approved"
        write_jsonl(target / "mappings.jsonl", mappings)
        alignment_path = target / SEMANTIC_PROJECT_FILES["alignments"]
        if alignment_path.is_file():
            alignments = read_jsonl(alignment_path)
            for alignment in alignments:
                if alignment.get("human_review_required"):
                    alignment["review_status"] = "human_approved"
            write_jsonl(alignment_path, alignments)
    write_json(target / "project.json", project)
    workflow["workflow_status"] = "initialized"
    workflow["current_step"] = "human_gate"
    workflow["next_actions"] = ["resume-research-project"]
    append_history(workflow, "approve-human-gate", f"Human reviewer {reviewer} approved {gate}.")
    write_json(target / "workflow.json", workflow)
    return {"operation": "approve_human_gate", "project_id": project["id"], "gate": gate, "status": "approved", "reviewer": reviewer, "reviewed_at": timestamp, "next_actions": workflow["next_actions"]}


def fit_value(required: str | None, actual: str | None) -> str:
    if not required or not actual:
        return "unknown"
    left, right = normalize(required), normalize(actual)
    unknown_markers = (
        "source specific", "unknown", "unspecified", "not specified", "varies",
        "dataset specific", "present in the selected source native series",
    )
    if any(marker in left or marker in right for marker in unknown_markers):
        return "unknown"
    if left == right or left in right or right in left:
        return "exact"
    left_tokens, right_tokens = set(left.split()), set(right.split())
    return "partial" if left_tokens.intersection(right_tokens) else "incompatible"


def registry_records(name: str) -> list[dict[str, Any]]:
    records = read_jsonl(ROOT / "registry" / name)
    entity_type = name.removesuffix(".jsonl")
    if entity_type in {"sources", "datasets", "constructs", "variables"}:
        cards = read_jsonl(ROOT / "registry" / "source_archives.jsonl")
        records.extend(distributed.distributed_entity_records(cards, entity_type))
    return list({item["id"]: item for item in records}.values())


def indicator_names(indicator: dict[str, Any]) -> set[str]:
    return {normalize(indicator["name"]), *(normalize(item) for item in indicator.get("synonyms", []))}


def choose_variable(indicator: dict[str, Any], variables: list[dict[str, Any]]) -> dict[str, Any]:
    names = indicator_names(indicator)
    return sorted(
        variables,
        key=lambda item: (
            0 if normalize(item["label"]) in names or normalize(item["name"]) in names else 1,
            VERIFICATION_RANK.get(item["verification"]["status"], 99),
            item["id"],
        ),
    )[0]


def perform_matching(
    project_dir: str | Path,
    rerun: bool = False,
    elements_root: str | Path | None = None,
) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    semantic_alignment_path = target / SEMANTIC_PROJECT_FILES["alignments"]
    if semantic_alignment_path.is_file() and read_jsonl(semantic_alignment_path):
        from semantic_resolver import perform_semantic_matching

        return perform_semantic_matching(target, rerun=rerun, elements_root=elements_root)
    project = read_json(target / "project.json")
    workflow = read_json(target / "workflow.json")
    indicators = read_jsonl(target / "indicators.jsonl")
    existing_mappings = read_jsonl(target / "mappings.jsonl")
    constructs = registry_records("constructs.jsonl")
    variables = registry_records("variables.jsonl")
    if rerun and not existing_mappings:
        raise ValueError("rerun-matching requires a previous matching attempt; use match-indicators first")
    if not rerun and existing_mappings:
        raise ValueError("project already has mappings; use rerun-matching to replace them")
    if project["evidence_stage"] != "topic_scaffold" and project["human_gates"]["indicator_framework"]["status"] != "approved":
        raise ValueError("formal matching requires explicit human approval of indicator_framework")
    construct_aliases: dict[str, set[str]] = {
        item["id"]: {normalize(item["name"]), *(normalize(alias) for alias in item.get("aliases", []))}
        for item in constructs
    }
    new_mappings = []
    outcome_counts: dict[str, int] = {}
    for indicator in [item for item in indicators if item["is_leaf"]]:
        names = indicator_names(indicator)
        matched_construct_ids = {cid for cid, aliases in construct_aliases.items() if names.intersection(aliases)}
        candidate_variables = [item for item in variables if matched_construct_ids.intersection(item["construct_ids"])]
        project_slug = project["id"].rsplit(":", 1)[-1]
        indicator_slug = indicator["id"].rsplit(":", 1)[-1]
        if indicator_slug.startswith(f"{project_slug}-"):
            indicator_slug = indicator_slug[len(project_slug) + 1 :]
        mapping_id = f"grdr:indicator-mapping:{project_slug}-{indicator_slug}"
        spec = indicator.get("operational_spec") or {}
        if candidate_variables:
            variable = choose_variable(indicator, candidate_variables)
            status = "direct_match"
            variable_ids = [variable["id"]]
            fit = {
                "construct": "exact",
                "population": fit_value(spec.get("population"), variable.get("population")),
                "unit": fit_value(spec.get("unit"), variable.get("unit")),
                "time": fit_value(spec.get("temporal_scope"), variable.get("temporal_resolution")),
                "space": fit_value(spec.get("spatial_scope"), variable.get("spatial_resolution")),
            }
            snapshot = variable.get("_grdr_snapshot")
            note = "Exact normalized construct identity; other fit dimensions are reported independently."
            if snapshot:
                note += f" Variable is supplied by distributed snapshot {snapshot['source_id']}@{snapshot['snapshot_id']}."
        else:
            status = "not_found_registry_snapshot"
            variable_ids = []
            fit = {"construct": "unknown", "population": "unknown", "unit": "unknown", "time": "unknown", "space": "unknown"}
            note = "No exact construct-to-variable chain exists in the current GRDR snapshot; this is a registry gap, not proof of external absence."
        new_mappings.append(
            {
                "schema_version": "0.1.0", "id": mapping_id, "project_id": project["id"],
                "indicator_id": indicator["id"], "mapping_status": status, "variable_ids": variable_ids,
                "transformation": None, "fit": fit, "human_review_required": False,
                "review_status": "not_required", "notes": note,
            }
        )
        outcome_counts[status] = outcome_counts.get(status, 0) + 1
    write_jsonl(target / "mappings.jsonl", new_mappings)
    mapping_status_by_indicator = {item["indicator_id"]: item["mapping_status"] for item in new_mappings}
    gaps = read_jsonl(target / "data_gaps.jsonl")
    for gap in gaps:
        if mapping_status_by_indicator.get(gap["indicator_id"]) == "not_found_registry_snapshot":
            gap["status"] = "expansion_planned"
        elif gap["indicator_id"] in mapping_status_by_indicator:
            gap["status"] = "resolved"
        gap["updated_at"] = now()
    write_jsonl(target / "data_gaps.jsonl", gaps)
    workflow["matching_attempt"] += 1
    workflow["workflow_status"] = "matched"
    workflow["current_step"] = "gap_analysis"
    workflow["next_actions"] = ["expand-from-data-gaps"] if outcome_counts.get("not_found_registry_snapshot") else ["research-project-status"]
    operation = "rerun-matching" if rerun else "match-indicators"
    append_history(workflow, operation, f"Matched {len(new_mappings)} leaf indicators: {json.dumps(outcome_counts, sort_keys=True)}.")
    write_json(target / "workflow.json", workflow)
    return {
        "operation": operation.replace("-", "_"), "project_id": project["id"],
        "matching_attempt": workflow["matching_attempt"], "mapping_count": len(new_mappings),
        "outcomes": dict(sorted(outcome_counts.items())), "mappings": new_mappings,
        "exploratory": project["evidence_stage"] == "topic_scaffold",
        "formal_evidence_ready": audit_project(target, ROOT)["formal_evidence_ready"],
        "next_actions": workflow["next_actions"],
    }


def search_candidates(indicator: dict[str, Any], limit: int = 5) -> tuple[list[str], list[str], list[str]]:
    terms = tokens(indicator["name"], indicator["definition"], *indicator.get("synonyms", []))
    datasets = registry_records("datasets.jsonl")
    sources = registry_records("sources.jsonl")

    def rank(records: list[dict[str, Any]]) -> list[str]:
        scored = []
        for record in records:
            haystack = normalize(json.dumps(record, ensure_ascii=False, sort_keys=True))
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((-score, VERIFICATION_RANK.get(record["verification"]["status"], 99), record["id"]))
        return [item[2] for item in sorted(scored)[:limit]]

    dataset_ids = rank(datasets)
    datasets_by_id = {item["id"]: item for item in datasets}
    source_ids = []
    for dataset_id in dataset_ids:
        for source_id in datasets_by_id[dataset_id]["source_ids"]:
            if source_id not in source_ids:
                source_ids.append(source_id)
    if not source_ids:
        source_ids = rank(sources)
    return terms, source_ids[:limit], dataset_ids


def expand_from_data_gaps(project_dir: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    project = read_json(target / "project.json")
    workflow = read_json(target / "workflow.json")
    indicators = {item["id"]: item for item in read_jsonl(target / "indicators.jsonl")}
    mappings = read_jsonl(target / "mappings.jsonl")
    if not mappings:
        raise ValueError("expand-from-data-gaps requires mapping outcomes; use match-indicators first")
    existing = {item["indicator_id"]: item for item in read_jsonl(target / "data_gaps.jsonl")}
    gaps = []
    for mapping in mappings:
        if mapping["mapping_status"] != "not_found_registry_snapshot":
            continue
        indicator = indicators[mapping["indicator_id"]]
        terms, source_ids, dataset_ids = search_candidates(indicator)
        project_slug = project["id"].rsplit(":", 1)[-1]
        indicator_slug = indicator["id"].rsplit(":", 1)[-1]
        if indicator_slug.startswith(f"{project_slug}-"):
            indicator_slug = indicator_slug[len(project_slug) + 1 :]
        gap_id = f"grdr:data-gap:{project_slug}-{indicator_slug}"
        created_at = existing.get(indicator["id"], {}).get("created_at", now())
        actions = ["deepen_existing_source"] if source_ids or dataset_ids else ["discover_new_source"]
        if not source_ids and not dataset_ids:
            actions.append("collect_primary_data")
        gaps.append(
            {
                "schema_version": "0.1.0", "id": gap_id, "project_id": project["id"],
                "indicator_id": indicator["id"], "status": "expansion_planned",
                "gap_type": "variable_not_registered", "requirement": indicator.get("operational_spec") or {},
                "search_terms": terms or [normalize(indicator["name"])],
                "candidate_source_ids": source_ids, "candidate_dataset_ids": dataset_ids,
                "recommended_actions": actions, "created_at": created_at, "updated_at": now(),
            }
        )
    write_jsonl(target / "data_gaps.jsonl", gaps)
    workflow["gap_expansion_round"] += 1
    workflow["workflow_status"] = "expansion_planned" if gaps else "completed"
    workflow["current_step"] = "source_expansion" if gaps else "completed"
    workflow["next_actions"] = ["deepen-candidate-sources", "resume-research-project", "rerun-matching"] if gaps else ["research-project-status"]
    append_history(workflow, "expand-from-data-gaps", f"Created {len(gaps)} bounded data-gap expansion records.")
    write_json(target / "workflow.json", workflow)
    auxiliary_errors = validate_auxiliary(target)
    if auxiliary_errors:
        raise ValueError("gap expansion failed validation: " + "; ".join(auxiliary_errors))
    return {
        "operation": "expand_from_data_gaps", "project_id": project["id"],
        "gap_expansion_round": workflow["gap_expansion_round"], "gap_count": len(gaps),
        "gaps": gaps, "next_actions": workflow["next_actions"],
        "warning": "Candidate sources and datasets are search leads for further profiling, not proof that compatible variables exist.",
    }


def research_project_status(project_dir: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    project = read_json(target / "project.json")
    workflow = read_json(target / "workflow.json")
    mappings = read_jsonl(target / "mappings.jsonl")
    gaps = read_jsonl(target / "data_gaps.jsonl")
    semantic_candidates = read_jsonl(target / SEMANTIC_PROJECT_FILES["candidates"]) if (target / SEMANTIC_PROJECT_FILES["candidates"]).is_file() else []
    semantic_alignments = read_jsonl(target / SEMANTIC_PROJECT_FILES["alignments"]) if (target / SEMANTIC_PROJECT_FILES["alignments"]).is_file() else []
    semantic_paths = read_jsonl(target / SEMANTIC_PROJECT_FILES["paths"]) if (target / SEMANTIC_PROJECT_FILES["paths"]).is_file() else []
    audit = audit_project(target, ROOT)
    auxiliary_errors = validate_auxiliary(target)
    outcomes: dict[str, int] = {}
    for mapping in mappings:
        status = mapping["mapping_status"]
        outcomes[status] = outcomes.get(status, 0) + 1
    leaves = audit.get("counts", {}).get("leaf_indicators", 0)
    matched = sum(count for status, count in outcomes.items() if status != "not_found_registry_snapshot")
    return {
        "operation": "research_project_status",
        "project_id": project["id"], "project_dir": str(target), "title": project["title"],
        "research_question": project["research_question"], "evidence_stage": project["evidence_stage"],
        "workflow_status": workflow["workflow_status"], "current_step": workflow["current_step"],
        "matching_attempt": workflow["matching_attempt"], "gap_expansion_round": workflow["gap_expansion_round"],
        "counts": {
            **audit.get("counts", {}),
            "semantic_candidates": len(semantic_candidates),
            "semantic_alignments": len(semantic_alignments),
            "semantic_paths": len(semantic_paths),
            "open_data_gaps": sum(1 for item in gaps if item["status"] in {"open", "expansion_planned"}),
        },
        "mapping_outcomes": dict(sorted(outcomes.items())),
        "leaf_match_coverage": {"matched": matched, "total": leaves, "ratio": (matched / leaves) if leaves else 0.0},
        "human_gates": project["human_gates"],
        "formal_evidence_ready": audit.get("formal_evidence_ready", False),
        "mapping_ready": audit.get("mapping_ready", False),
        "exploratory_matching_complete": bool(mappings) and len(mappings) == leaves and not audit.get("errors"),
        "audit_errors": [*audit.get("errors", []), *auxiliary_errors],
        "audit_warnings": audit.get("warnings", []),
        "next_actions": workflow["next_actions"],
        "last_operation": workflow["last_operation"],
    }
