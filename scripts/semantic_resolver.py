#!/usr/bin/env python3
"""Resolve project-scoped research indicators through GRDR B semantics to A data."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import unicodedata
from typing import Any, Iterable

import distributed_runtime as distributed
import global_runtime_index as global_index
from grdr_paths import CORE_ROOT, registry_root, research_projects_root


ROOT = CORE_ROOT
REGISTRY_ROOT = registry_root()
PROJECT_ROOT = research_projects_root()
BASE_PROJECT_FILES = (
    "project.json",
    "literature.jsonl",
    "evidence_units.jsonl",
    "indicators.jsonl",
    "mappings.jsonl",
    "workflow.json",
    "data_gaps.jsonl",
)
SEMANTIC_FILES = {
    "candidates": "semantic_candidates.jsonl",
    "alignments": "semantic_alignments.jsonl",
    "paths": "semantic_paths.jsonl",
}
SCHEMAS = {
    "candidates": "semantic_candidate.schema.json",
    "alignments": "semantic_alignment.schema.json",
    "paths": "semantic_path.schema.json",
    "decisions": "semantic_alignment_decision.schema.json",
    "mappings": "indicator_mapping.schema.json",
}
RELATION_RANK = {
    "exact_match": 0,
    "close_match": 1,
    "narrower_match": 2,
    "broader_match": 3,
    "related_match": 4,
    "no_match": 5,
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
FIT_RANK = {"exact": 0, "partial": 1, "unknown": 2, "incompatible": 3}
STOPWORDS = {
    "and", "the", "for", "from", "with", "per", "total", "annual", "rate",
    "level", "use", "using", "country", "countries", "year", "years", "of",
    "in", "to", "by", "or", "a", "an", "与", "的", "及", "和", "水平", "年度",
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    result = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected JSON object")
        result.append(value)
    return result


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.write_text(
        "".join(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
            for value in values
        ),
        encoding="utf-8",
    )


def resolve_project_dir(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        candidate = PROJECT_ROOT / path
        path = candidate if candidate.exists() or len(path.parts) == 1 else ROOT / path
    return path.resolve()


def require_project(path: Path) -> None:
    missing = [name for name in BASE_PROJECT_FILES if not (path / name).is_file()]
    if missing:
        raise ValueError(f"incomplete research project {path}: missing {', '.join(missing)}")


def normalize(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(normalize(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(normalize(item) for item in value)
    return unicodedata.normalize("NFKC", str(value)).casefold()


def query_tokens(*values: Any) -> list[str]:
    found = {
        token
        for value in values
        for token in re.findall(r"[^\W_]+", normalize(value), flags=re.UNICODE)
        if len(token) >= 2 and token not in STOPWORDS
    }
    return sorted(found)


def slug(value: str, maximum: int = 44) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    result = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    return (result or "record")[:maximum].strip("-")


def fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stable_id(prefix: str, label: str, *identity: Any) -> str:
    return f"grdr:{prefix}:{slug(label)}-{fingerprint(identity)[:12]}"


def core_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def source_cards() -> list[dict[str, Any]]:
    return read_jsonl(REGISTRY_ROOT / "source_archives.jsonl")


def append_history(workflow: dict[str, Any], operation: str, summary: str) -> None:
    stamp = now()
    workflow["last_operation"] = operation
    workflow["updated_at"] = stamp
    workflow["history"].append({"timestamp": stamp, "operation": operation, "summary": summary})


def validate_records(records: Iterable[dict[str, Any]], schema_name: str, label: str) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError("jsonschema is required for GRDR semantic resolution") from exc
    schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = []
    for index, record in enumerate(records, 1):
        for error in validator.iter_errors(record):
            location = ".".join(str(part) for part in error.path) or "<record>"
            errors.append(f"{label}:{index}:{location}: {error.message}")
    if errors:
        raise ValueError("; ".join(sorted(errors)))


def ensure_semantic_files(project_dir: Path) -> None:
    for filename in SEMANTIC_FILES.values():
        path = project_dir / filename
        if not path.exists():
            write_jsonl(path, [])


def semantic_file_errors(project_dir: str | Path) -> list[str]:
    target = resolve_project_dir(project_dir)
    errors = []
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema is required for GRDR semantic-resolution audits"]
    for key, filename in SEMANTIC_FILES.items():
        path = target / filename
        if not path.is_file():
            continue
        schema = json.loads((ROOT / "schemas" / SCHEMAS[key]).read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        try:
            records = read_jsonl(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
            continue
        for index, record in enumerate(records, 1):
            for error in validator.iter_errors(record):
                location = ".".join(str(part) for part in error.path) or "<record>"
                errors.append(f"{filename}:{index}:{location}: {error.message}")
    try:
        project_id = read_json(target / "project.json")["id"]
        indicators = {
            item["id"]: item for item in read_jsonl(target / "indicators.jsonl")
        }
        candidates = read_jsonl(target / SEMANTIC_FILES["candidates"])
        alignments = read_jsonl(target / SEMANTIC_FILES["alignments"])
        paths = read_jsonl(target / SEMANTIC_FILES["paths"])
        mappings = read_jsonl(target / "mappings.jsonl")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"cannot audit semantic cross-references: {exc}")
        return sorted(set(errors))

    for label, records in (("semantic candidates", candidates), ("semantic alignments", alignments), ("semantic paths", paths)):
        ids = [item.get("id") for item in records]
        for record_id in sorted({item for item in ids if item and ids.count(item) > 1}):
            errors.append(f"{label}: duplicate id {record_id}")
        for item in records:
            if item.get("project_id") != project_id:
                errors.append(f"{label}:{item.get('id')}: project_id does not match {project_id}")
            indicator_id = item.get("indicator_id")
            if indicator_id not in indicators:
                errors.append(f"{label}:{item.get('id')}: unknown indicator_id {indicator_id}")
            elif not indicators[indicator_id].get("is_leaf"):
                errors.append(f"{label}:{item.get('id')}: semantic resolution may target leaf indicators only")

    candidate_by_id = {item["id"]: item for item in candidates if item.get("id")}
    alignment_by_id = {item["id"]: item for item in alignments if item.get("id")}
    path_by_id = {item["id"]: item for item in paths if item.get("id")}
    if alignments:
        by_indicator: dict[str, list[dict[str, Any]]] = {}
        for alignment in alignments:
            by_indicator.setdefault(alignment.get("indicator_id"), []).append(alignment)
            candidate_id = alignment.get("candidate_id")
            if candidate_id is not None:
                candidate = candidate_by_id.get(candidate_id)
                if candidate is None:
                    errors.append(f"semantic alignment:{alignment.get('id')}: unknown candidate_id {candidate_id}")
                elif candidate.get("target_id") != alignment.get("target_id"):
                    errors.append(f"semantic alignment:{alignment.get('id')}: candidate target differs from alignment target")
        for indicator_id, indicator in indicators.items():
            if not indicator.get("is_leaf"):
                continue
            primaries = [item for item in by_indicator.get(indicator_id, []) if item.get("alignment_role") == "primary"]
            if len(primaries) != 1:
                errors.append(f"indicator:{indicator_id}: exactly one primary semantic alignment is required")

    for path in paths:
        alignment = alignment_by_id.get(path.get("alignment_id"))
        if alignment is None:
            errors.append(f"semantic path:{path.get('id')}: unknown alignment_id {path.get('alignment_id')}")
        elif alignment.get("indicator_id") != path.get("indicator_id") or alignment.get("target_id") != path.get("target_id"):
            errors.append(f"semantic path:{path.get('id')}: alignment identity differs from path")

    for mapping in mappings:
        for alignment_id in mapping.get("semantic_alignment_ids", []):
            if alignment_id not in alignment_by_id:
                errors.append(f"mapping:{mapping.get('id')}: unknown semantic_alignment_id {alignment_id}")
        for path_id in mapping.get("semantic_path_ids", []):
            if path_id not in path_by_id:
                errors.append(f"mapping:{mapping.get('id')}: unknown semantic_path_id {path_id}")
    return sorted(errors)


def _verification_status(record: dict[str, Any]) -> str:
    return record.get("verification", {}).get("status", "unknown")


def _candidate_from_target(
    target_type: str,
    target: dict[str, Any],
    query_terms_value: list[str],
    via: str,
    variable_hint: str | None = None,
) -> dict[str, Any] | None:
    haystack = normalize(target)
    matched = [term for term in query_terms_value if normalize(term) in haystack]
    if not matched:
        return None
    label = target.get("preferred_label") or target.get("label") or target.get("name") or target["id"]
    label_text = normalize(label)
    exact = any(normalize(term) == label_text for term in query_terms_value)
    return {
        "target_type": target_type,
        "target_id": target["id"],
        "target_label": label,
        "target_definition": target.get("definition", ""),
        "retrieval_via": [via],
        "matched_terms": sorted(set(matched)),
        "lexical_score": float(len(matched) + (6 if exact else 0) + (1 if target_type == "construct" else 0)),
        "variable_hint_ids": [variable_hint] if variable_hint else [],
        "snapshot": None,
        "verification_status": _verification_status(target),
    }


def _central_entity_sources(
    datasets: list[dict[str, Any]],
    variables: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Resolve canonical Construct/SemanticNode membership without parsing versioned IDs."""

    dataset_sources = {
        item["id"]: set(item.get("source_ids", []))
        for item in datasets
    }
    construct_sources: dict[str, set[str]] = {}
    for variable in variables:
        source_ids = {
            source_id
            for dataset_id in variable.get("dataset_ids", [])
            for source_id in dataset_sources.get(dataset_id, set())
        }
        for construct_id in variable.get("construct_ids", []):
            construct_sources.setdefault(construct_id, set()).update(source_ids)

    semantic_sources: dict[str, set[str]] = {}
    semantic_edges: list[tuple[str, str]] = []
    for relationship in relationships:
        subject_id = relationship.get("subject_id", "")
        object_id = relationship.get("object_id", "")
        if subject_id.startswith("grdr:semantic-node:") and object_id in construct_sources:
            semantic_sources.setdefault(subject_id, set()).update(construct_sources[object_id])
        if object_id.startswith("grdr:semantic-node:") and subject_id in construct_sources:
            semantic_sources.setdefault(object_id, set()).update(construct_sources[subject_id])
        if subject_id.startswith("grdr:semantic-node:") and object_id.startswith("grdr:semantic-node:"):
            semantic_edges.append((subject_id, object_id))

    changed = True
    while changed:
        changed = False
        for left, right in semantic_edges:
            combined = semantic_sources.get(left, set()) | semantic_sources.get(right, set())
            for node_id in (left, right):
                current = semantic_sources.setdefault(node_id, set())
                if not combined.issubset(current):
                    current.update(combined)
                    changed = True
    return construct_sources, semantic_sources


def central_semantic_candidates(
    query_terms_value: list[str],
    limit: int,
    *,
    exclude_source_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    constructs = {item["id"]: item for item in read_jsonl(REGISTRY_ROOT / "constructs.jsonl")}
    semantic_nodes = read_jsonl(REGISTRY_ROOT / "semantic_nodes.jsonl")
    variables = read_jsonl(REGISTRY_ROOT / "variables.jsonl")
    datasets = read_jsonl(REGISTRY_ROOT / "datasets.jsonl")
    relationships = read_jsonl(REGISTRY_ROOT / "relationships.jsonl")
    excluded = exclude_source_ids or set()
    construct_sources, semantic_sources = _central_entity_sources(datasets, variables, relationships)
    candidates: dict[str, dict[str, Any]] = {}

    def excluded_target(target_type: str, target_id: str) -> bool:
        memberships = construct_sources if target_type == "construct" else semantic_sources
        return bool(memberships.get(target_id, set()) & excluded)

    def merge(item: dict[str, Any] | None) -> None:
        if not item or excluded_target(item["target_type"], item["target_id"]):
            return
        current = candidates.get(item["target_id"])
        if current is None:
            candidates[item["target_id"]] = item
            return
        current["retrieval_via"] = sorted(set(current["retrieval_via"]) | set(item["retrieval_via"]))
        current["matched_terms"] = sorted(set(current["matched_terms"]) | set(item["matched_terms"]))
        current["variable_hint_ids"] = sorted(set(current["variable_hint_ids"]) | set(item["variable_hint_ids"]))
        current["lexical_score"] = max(current["lexical_score"], item["lexical_score"])

    for construct in constructs.values():
        merge(_candidate_from_target("construct", construct, query_terms_value, "construct_text"))
    for node in semantic_nodes:
        merge(_candidate_from_target("semantic_node", node, query_terms_value, "semantic_node_text"))
    for variable in variables:
        matched = [term for term in query_terms_value if normalize(term) in normalize(variable)]
        if not matched:
            continue
        for construct_id in variable.get("construct_ids", []):
            if construct_id in constructs:
                construct = constructs[construct_id]
                label = construct.get("label") or construct.get("name") or construct["id"]
                merge(
                    {
                        "target_type": "construct",
                        "target_id": construct["id"],
                        "target_label": label,
                        "target_definition": construct.get("definition", ""),
                        "retrieval_via": ["variable_text"],
                        "matched_terms": sorted(set(matched)),
                        "lexical_score": float(len(matched) + 2),
                        "variable_hint_ids": [variable["id"]],
                        "snapshot": None,
                        "verification_status": _verification_status(construct),
                    }
                )
    return sorted(
        candidates.values(),
        key=lambda item: (-item["lexical_score"], item["target_type"] != "construct", VERIFICATION_RANK.get(item["verification_status"], 99), item["target_label"].casefold()),
    )[:limit]


def _load_query_overrides(path: str | Path | None, leaves: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    if path is None:
        return {}
    records = read_jsonl(Path(path).expanduser().resolve())
    overrides: dict[str, list[str]] = {}
    for index, item in enumerate(records, 1):
        if set(item) != {"indicator_id", "query_terms"}:
            raise ValueError(f"semantic query override {index}: expected only indicator_id and query_terms")
        indicator_id = item["indicator_id"]
        terms = item["query_terms"]
        if indicator_id not in leaves:
            raise ValueError(f"semantic query override {index}: unknown leaf indicator {indicator_id}")
        if not isinstance(terms, list) or not terms or not all(isinstance(term, str) and term.strip() for term in terms):
            raise ValueError(f"semantic query override {index}: query_terms must be a non-empty string array")
        overrides[indicator_id] = list(dict.fromkeys(term.strip() for term in terms))
    return overrides


def prepare_semantic_candidates(
    project_dir: str | Path,
    query_file: str | Path | None = None,
    *,
    limit: int = 25,
    elements_root: str | Path | None = None,
    snapshot_policy: str = "latest_callable",
    replace: bool = False,
) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    ensure_semantic_files(target)
    candidate_path = target / SEMANTIC_FILES["candidates"]
    if read_jsonl(candidate_path) and not replace:
        raise ValueError("semantic candidates already exist; use --replace to rebuild the recall snapshot")
    project = read_json(target / "project.json")
    workflow = read_json(target / "workflow.json")
    leaves = {item["id"]: item for item in read_jsonl(target / "indicators.jsonl") if item["is_leaf"]}
    overrides = _load_query_overrides(query_file, leaves)
    cards = source_cards()
    if snapshot_policy not in {"latest_callable", "history"}:
        raise ValueError("snapshot_policy must be 'latest_callable' or 'history'")
    use_global_index = global_index.cards_match_external_registry(cards)
    if use_global_index:
        try:
            callable_source_ids = global_index.callable_source_ids(cards, elements_root)
        except (OSError, ValueError, sqlite3.Error, json.JSONDecodeError):
            use_global_index = False
    if not use_global_index:
        callable_source_ids = {
            card["source_id"]
            for card, _snapshot in distributed.available_runtimes(cards, elements_root)
        }
    timestamp = now()
    all_records = []
    counts: dict[str, int] = {}
    for indicator_id, indicator in sorted(leaves.items()):
        terms = overrides.get(indicator_id)
        if terms is None:
            terms = query_tokens(indicator["name"], indicator["definition"], indicator.get("synonyms", []))
            phrases = [indicator["name"], *indicator.get("synonyms", [])]
            terms = list(dict.fromkeys([*(item.strip() for item in phrases if item.strip()), *terms]))
        if not terms:
            raise ValueError(f"leaf indicator has no usable semantic query terms: {indicator_id}")
        if use_global_index:
            recalled = global_index.search_semantic_candidates(
                cards,
                terms,
                elements_root,
                limit=limit,
                snapshot_policy=snapshot_policy,
            )
        else:
            distributed_recalled = distributed.distributed_semantic_candidates(
                cards, terms, elements_root, limit=limit
            )
            central_recalled = central_semantic_candidates(
                terms,
                limit,
                exclude_source_ids=callable_source_ids if snapshot_policy == "latest_callable" else None,
            )
            distributed_target_ids = {item["target_id"] for item in distributed_recalled}
            recalled = [
                *distributed_recalled,
                *(item for item in central_recalled if item["target_id"] not in distributed_target_ids),
            ]
        deduped: dict[tuple[str, str | None, str | None], dict[str, Any]] = {}
        for item in recalled:
            snapshot = item.get("snapshot") or {}
            key = (item["target_id"], snapshot.get("source_id"), snapshot.get("snapshot_id"))
            current = deduped.get(key)
            if current is None or item["lexical_score"] > current["lexical_score"]:
                deduped[key] = item
        ordered = sorted(
            deduped.values(),
            key=lambda item: (
                -item["lexical_score"],
                item["target_type"] != "construct",
                VERIFICATION_RANK.get(item["verification_status"], 99),
                item.get("snapshot") is None,
                item["target_label"].casefold(),
            ),
        )[:limit]
        for rank, item in enumerate(ordered, 1):
            identity = (project["id"], indicator_id, item["target_id"], item.get("snapshot"))
            all_records.append(
                {
                    "schema_version": "1.0.0",
                    "id": stable_id("semantic-candidate", f"{project['id'].rsplit(':', 1)[-1]}-{indicator_id.rsplit(':', 1)[-1]}", *identity),
                    "project_id": project["id"],
                    "indicator_id": indicator_id,
                    **item,
                    "retrieval_via": sorted(item["retrieval_via"]),
                    "query_terms": terms,
                    "matched_terms": sorted(item["matched_terms"]),
                    "variable_hint_ids": sorted(item["variable_hint_ids"]),
                    "rank": rank,
                    "created_at": timestamp,
                }
            )
        counts[indicator_id] = len(ordered)
    validate_records(all_records, SCHEMAS["candidates"], SEMANTIC_FILES["candidates"])
    write_jsonl(candidate_path, all_records)
    write_jsonl(target / SEMANTIC_FILES["alignments"], [])
    write_jsonl(target / SEMANTIC_FILES["paths"], [])
    append_history(
        workflow,
        "prepare-semantic-candidates",
        f"Recalled {len(all_records)} B candidates for {len(leaves)} leaf indicators under snapshot policy {snapshot_policy}.",
    )
    workflow["workflow_status"] = "ready_to_match"
    workflow["current_step"] = "matching"
    workflow["next_actions"] = ["align-research-indicators"]
    write_json(target / "workflow.json", workflow)
    return {
        "operation": "prepare_semantic_candidates",
        "project_id": project["id"],
        "candidate_count": len(all_records),
        "candidate_counts_by_indicator": counts,
        "snapshot_policy": snapshot_policy,
        "discovery_engine": "global_index" if use_global_index else "legacy_distributed_scan",
        "callable_source_count": len(callable_source_ids),
        "candidate_file": str(candidate_path),
        "next_actions": workflow["next_actions"],
        "warning": "Candidate recall is not a semantic decision; the Agent must compare definitions and evidence before alignment.",
    }


def record_semantic_alignments(
    project_dir: str | Path,
    decision_file: str | Path,
    *,
    replace: bool = False,
) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    ensure_semantic_files(target)
    alignment_path = target / SEMANTIC_FILES["alignments"]
    if read_jsonl(alignment_path) and not replace:
        raise ValueError("semantic alignments already exist; use --replace to record a revised decision set")
    project = read_json(target / "project.json")
    workflow = read_json(target / "workflow.json")
    leaves = {item["id"]: item for item in read_jsonl(target / "indicators.jsonl") if item["is_leaf"]}
    candidates = read_jsonl(target / SEMANTIC_FILES["candidates"])
    if not any(item.get("operation") == "prepare-semantic-candidates" for item in workflow.get("history", [])):
        raise ValueError("semantic candidate recall has not been run; use prepare-semantic-candidates first")
    candidate_index: dict[tuple[str, str], dict[str, Any]] = {}
    for item in candidates:
        key = (item["indicator_id"], item["target_id"])
        current = candidate_index.get(key)
        if current is None or item["rank"] < current["rank"]:
            candidate_index[key] = item
    decisions = read_jsonl(Path(decision_file).expanduser().resolve())
    validate_records(decisions, SCHEMAS["decisions"], "semantic alignment decision")
    if not decisions:
        raise ValueError("semantic alignment decision file is empty")
    by_indicator: dict[str, list[dict[str, Any]]] = {}
    for item in decisions:
        if item["indicator_id"] not in leaves:
            raise ValueError(f"semantic decision references unknown leaf indicator: {item['indicator_id']}")
        by_indicator.setdefault(item["indicator_id"], []).append(item)
    for indicator_id in leaves:
        decisions_for_indicator = by_indicator.get(indicator_id, [])
        primaries = [item for item in decisions_for_indicator if item["alignment_role"] == "primary"]
        if len(primaries) != 1:
            raise ValueError(f"{indicator_id}: exactly one primary semantic decision is required")
        if primaries[0]["mapping_relation"] == "no_match" and len(decisions_for_indicator) != 1:
            raise ValueError(f"{indicator_id}: no_match cannot be combined with other semantic decisions")
        components = [item for item in decisions_for_indicator if item["alignment_role"] == "component"]
        if components and len(components) < 2:
            raise ValueError(f"{indicator_id}: component alignment requires at least two component decisions")

    timestamp = now()
    alignments = []
    for decision in decisions:
        indicator = leaves[decision["indicator_id"]]
        candidate = None
        if decision["mapping_relation"] != "no_match":
            candidate = candidate_index.get((decision["indicator_id"], decision["target_id"]))
            if candidate is None:
                raise ValueError(
                    f"{decision['indicator_id']}: target {decision['target_id']} is absent from its candidate snapshot; rebuild recall with expanded Agent query terms"
                )
            if candidate["target_type"] != decision["target_type"]:
                raise ValueError(f"{decision['indicator_id']}: target_type differs from recalled candidate")
        review_required = (
            decision["mapping_relation"] not in {"exact_match", "no_match"}
            or decision["target_type"] == "semantic_node"
        )
        identity = (
            project["id"], decision["indicator_id"], decision["target_id"],
            decision["mapping_relation"], decision["alignment_role"],
        )
        alignments.append(
            {
                "schema_version": "1.0.0",
                "id": stable_id("semantic-alignment", f"{project['id'].rsplit(':', 1)[-1]}-{decision['indicator_id'].rsplit(':', 1)[-1]}", *identity),
                "project_id": project["id"],
                "indicator_id": decision["indicator_id"],
                "candidate_id": candidate["id"] if candidate else None,
                "target_type": decision["target_type"],
                "target_id": decision["target_id"],
                "mapping_relation": decision["mapping_relation"],
                "alignment_role": decision["alignment_role"],
                "confidence": decision["confidence"],
                "rationale": decision["rationale"],
                "indicator_evidence_unit_ids": indicator.get("evidence_unit_ids", []),
                "target_snapshot": candidate.get("snapshot") if candidate else None,
                "human_review_required": review_required,
                "review_status": "agent_candidate" if review_required else "not_required",
                "agent_provenance": {
                    "executor": "ai_agent",
                    "model": project.get("agent_provenance", {}).get("model"),
                    "method": "evidence_constrained_semantic_alignment",
                    "core_version": core_version(),
                },
                "created_at": timestamp,
            }
        )
    validate_records(alignments, SCHEMAS["alignments"], SEMANTIC_FILES["alignments"])
    write_jsonl(alignment_path, sorted(alignments, key=lambda item: (item["indicator_id"], item["alignment_role"], item["id"])))
    write_jsonl(target / SEMANTIC_FILES["paths"], [])
    append_history(workflow, "align-research-indicators", f"Persisted {len(alignments)} evidence-constrained R→B alignment decisions.")
    workflow["workflow_status"] = "ready_to_match"
    workflow["current_step"] = "matching"
    workflow["next_actions"] = ["traverse-semantic-paths"]
    write_json(target / "workflow.json", workflow)
    return {
        "operation": "align_research_indicators",
        "project_id": project["id"],
        "alignment_count": len(alignments),
        "contested_alignment_count": sum(1 for item in alignments if item["human_review_required"]),
        "alignment_file": str(alignment_path),
        "next_actions": workflow["next_actions"],
    }


def _central_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE records (id TEXT PRIMARY KEY, entity_type TEXT, label TEXT, search_text TEXT, payload_json TEXT);
        CREATE TABLE relationships (id TEXT PRIMARY KEY, subject_id TEXT, predicate TEXT, object_id TEXT, payload_json TEXT);
        """
    )
    collection_names = (
        "semantic_nodes", "constructs", "variables", "data_elements", "data_structures", "datasets", "sources"
    )
    for collection in collection_names:
        for item in read_jsonl(REGISTRY_ROOT / f"{collection}.jsonl"):
            label = item.get("preferred_label") or item.get("label") or item.get("name") or item["id"]
            connection.execute(
                "INSERT INTO records VALUES (?, ?, ?, ?, ?)",
                (item["id"], collection, label, normalize(item), json.dumps(item, ensure_ascii=False)),
            )
    for item in read_jsonl(REGISTRY_ROOT / "relationships.jsonl"):
        connection.execute(
            "INSERT INTO relationships VALUES (?, ?, ?, ?, ?)",
            (item["id"], item["subject_id"], item["predicate"], item["object_id"], json.dumps(item, ensure_ascii=False)),
        )
    connection.commit()
    return connection


def traverse_semantic_paths(
    project_dir: str | Path,
    *,
    elements_root: str | Path | None = None,
    limit_per_alignment: int = 100,
    replace: bool = False,
) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    ensure_semantic_files(target)
    path_file = target / SEMANTIC_FILES["paths"]
    if read_jsonl(path_file) and not replace:
        raise ValueError("semantic paths already exist; use --replace to rebuild graph traversal")
    project = read_json(target / "project.json")
    workflow = read_json(target / "workflow.json")
    alignments = read_jsonl(target / SEMANTIC_FILES["alignments"])
    if not alignments:
        raise ValueError("no semantic alignments exist; run align-research-indicators first")
    cards = source_cards()
    paths = []
    missing_alignment_ids = []
    central = None
    try:
        for alignment in alignments:
            if alignment["mapping_relation"] == "no_match":
                continue
            snapshot = alignment.get("target_snapshot")
            if snapshot:
                raw_paths = distributed.distributed_semantic_paths(
                    cards,
                    alignment["target_id"],
                    alignment["target_type"],
                    elements_root,
                    source_id=snapshot["source_id"],
                    snapshot_id=snapshot["snapshot_id"],
                    limit=limit_per_alignment,
                )
            else:
                central = central or _central_connection()
                raw_paths = distributed.semantic_paths_in_connection(
                    central,
                    alignment["target_id"],
                    alignment["target_type"],
                    limit=limit_per_alignment,
                )
                for item in raw_paths:
                    item["_grdr_snapshot"] = None
                    item["callable"] = False
            if not raw_paths:
                missing_alignment_ids.append(alignment["id"])
            for raw in raw_paths:
                snapshot_ref = raw.get("_grdr_snapshot") or {}
                logical = {
                    "project_id": project["id"],
                    "indicator_id": alignment["indicator_id"],
                    "alignment_id": alignment["id"],
                    "target_id": alignment["target_id"],
                    "construct_id": raw["construct_id"],
                    "variable_id": raw["variable_id"],
                    "snapshot": snapshot_ref,
                    "edges": raw["edges"],
                }
                path_fingerprint = fingerprint(logical)
                paths.append(
                    {
                        "schema_version": "1.0.0",
                        "id": stable_id("semantic-path", f"{project['id'].rsplit(':', 1)[-1]}-{alignment['indicator_id'].rsplit(':', 1)[-1]}", path_fingerprint),
                        "path_fingerprint": path_fingerprint,
                        "project_id": project["id"],
                        "indicator_id": alignment["indicator_id"],
                        "alignment_id": alignment["id"],
                        "mapping_relation": alignment["mapping_relation"],
                        "alignment_role": alignment["alignment_role"],
                        "target_type": alignment["target_type"],
                        "target_id": alignment["target_id"],
                        "semantic_node_ids": raw["semantic_node_ids"],
                        "construct_id": raw["construct_id"],
                        "variable_id": raw["variable_id"],
                        "data_element_ids": raw["data_element_ids"],
                        "data_structure_ids": raw["data_structure_ids"],
                        "dataset_ids": raw["dataset_ids"],
                        "source_id": snapshot_ref.get("source_id"),
                        "snapshot_id": snapshot_ref.get("snapshot_id"),
                        "release": snapshot_ref.get("release"),
                        "edges": raw["edges"],
                        "callable": raw.get("callable", False),
                        "verification_status": raw["verification_status"],
                    }
                )
    finally:
        if central is not None:
            central.close()
    unique = {item["path_fingerprint"]: item for item in paths}
    paths = sorted(unique.values(), key=lambda item: (item["indicator_id"], RELATION_RANK[item["mapping_relation"]], VERIFICATION_RANK.get(item["verification_status"], 99), item["variable_id"]))
    validate_records(paths, SCHEMAS["paths"], SEMANTIC_FILES["paths"])
    write_jsonl(path_file, paths)
    append_history(workflow, "traverse-semantic-paths", f"Materialized {len(paths)} R→B→A paths; {len(missing_alignment_ids)} alignments had no variable path.")
    workflow["workflow_status"] = "ready_to_match"
    workflow["current_step"] = "matching"
    workflow["next_actions"] = ["rerun-matching"] if read_jsonl(target / "mappings.jsonl") else ["match-indicators"]
    write_json(target / "workflow.json", workflow)
    return {
        "operation": "traverse_semantic_paths",
        "project_id": project["id"],
        "path_count": len(paths),
        "unresolved_alignment_ids": missing_alignment_ids,
        "path_file": str(path_file),
        "next_actions": workflow["next_actions"],
    }


def fit_value(required: str | None, actual: str | None) -> str:
    if not required or not actual:
        return "unknown"
    left, right = normalize(required), normalize(actual)
    unknown_markers = (
        "source-specific", "source specific", "unknown", "unspecified", "not specified", "varies",
        "dataset-specific", "dataset specific", "present in the selected source-native series",
    )
    if any(marker in left or marker in right for marker in unknown_markers):
        return "unknown"
    if left == right or left in right or right in left:
        return "exact"
    left_tokens, right_tokens = set(query_tokens(left)), set(query_tokens(right))
    return "partial" if left_tokens.intersection(right_tokens) else "incompatible"


def _resolve_variable(variable_id: str, elements_root: str | Path | None) -> dict[str, Any] | None:
    central = {item["id"]: item for item in read_jsonl(REGISTRY_ROOT / "variables.jsonl")}
    if variable_id in central:
        return {"variable": central[variable_id], "snapshot": None}
    return distributed.resolve_distributed_variable(source_cards(), variable_id, elements_root)


def _variable_fit(indicator: dict[str, Any], variable: dict[str, Any], relation: str) -> dict[str, str]:
    spec = indicator.get("operational_spec") or {}
    return {
        "construct": "exact" if relation == "exact_match" else "partial",
        "population": fit_value(spec.get("population"), variable.get("population")),
        "unit": fit_value(spec.get("unit"), variable.get("unit")),
        "time": fit_value(spec.get("temporal_scope"), variable.get("temporal_resolution")),
        "space": fit_value(spec.get("spatial_scope"), variable.get("spatial_resolution")),
    }


def _aggregate_fit(values: Iterable[dict[str, str]]) -> dict[str, str]:
    values = list(values)
    if not values:
        return {key: "unknown" for key in ("construct", "population", "unit", "time", "space")}
    return {
        key: max((item[key] for item in values), key=lambda value: FIT_RANK[value])
        for key in ("construct", "population", "unit", "time", "space")
    }


def perform_semantic_matching(
    project_dir: str | Path,
    *,
    rerun: bool = False,
    elements_root: str | Path | None = None,
) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    ensure_semantic_files(target)
    project = read_json(target / "project.json")
    workflow = read_json(target / "workflow.json")
    indicators = {item["id"]: item for item in read_jsonl(target / "indicators.jsonl") if item["is_leaf"]}
    existing_mappings = read_jsonl(target / "mappings.jsonl")
    alignments = read_jsonl(target / SEMANTIC_FILES["alignments"])
    paths = read_jsonl(target / SEMANTIC_FILES["paths"])
    if not alignments:
        raise ValueError("semantic matching requires persisted alignments; run align-research-indicators first")
    if rerun and not existing_mappings:
        raise ValueError("rerun-matching requires a previous matching attempt; use match-indicators first")
    if not rerun and existing_mappings:
        raise ValueError("project already has mappings; use rerun-matching to replace them")
    if project["evidence_stage"] != "topic_scaffold" and project["human_gates"]["indicator_framework"]["status"] != "approved":
        raise ValueError("formal matching requires explicit human approval of indicator_framework")
    by_indicator_alignments: dict[str, list[dict[str, Any]]] = {}
    by_alignment_paths: dict[str, list[dict[str, Any]]] = {}
    for item in alignments:
        by_indicator_alignments.setdefault(item["indicator_id"], []).append(item)
    for item in paths:
        by_alignment_paths.setdefault(item["alignment_id"], []).append(item)

    mappings = []
    outcome_counts: dict[str, int] = {}
    for indicator_id, indicator in sorted(indicators.items()):
        indicator_alignments = by_indicator_alignments.get(indicator_id, [])
        primary = next((item for item in indicator_alignments if item["alignment_role"] == "primary"), None)
        components = [item for item in indicator_alignments if item["alignment_role"] == "component"]
        selected_alignments = components if components else ([primary] if primary else [])
        selected_paths = []
        fits = []
        for alignment in selected_alignments:
            if not alignment or alignment["mapping_relation"] == "no_match":
                continue
            candidates = []
            for path in by_alignment_paths.get(alignment["id"], []):
                resolved = _resolve_variable(path["variable_id"], elements_root)
                if not resolved:
                    continue
                fit = _variable_fit(indicator, resolved["variable"], alignment["mapping_relation"])
                candidates.append((path, resolved["variable"], fit))
            if candidates:
                best = sorted(
                    candidates,
                    key=lambda item: (
                        sum(FIT_RANK[value] for value in item[2].values()),
                        VERIFICATION_RANK.get(item[0]["verification_status"], 99),
                        item[0]["variable_id"],
                    ),
                )[0]
                selected_paths.append(best[0])
                fits.append(best[2])
        variable_ids = [item["variable_id"] for item in selected_paths]
        alignment_ids = list(
            dict.fromkeys(
                item["id"] for item in ([primary] if primary else []) + components if item
            )
        )
        path_ids = [item["id"] for item in selected_paths]
        aggregate_fit = _aggregate_fit(fits)
        relations = [item["mapping_relation"] for item in selected_alignments if item]
        spec = indicator.get("operational_spec") or {}
        semantic_node_route = any(item.get("target_type") == "semantic_node" for item in selected_alignments if item)
        contested_relation = any(item.get("human_review_required") for item in selected_alignments if item)
        if not variable_ids:
            status = "not_found_registry_snapshot"
            transformation = None
            note = "No evidence-backed R→B→A variable path exists in the current GRDR snapshot; this is a registry gap, not proof of external absence."
        elif components:
            status = "composite_required"
            transformation = "Combine the selected component variables according to the approved operational specification; record the reproducible formula before analysis."
            note = "Multiple component alignments were traversed through persisted semantic paths."
        elif "incompatible" in aggregate_fit.values() or ((relations and relations[0] != "exact_match" or semantic_node_route) and not spec.get("proxy_allowed", False)):
            status = "definition_conflict"
            transformation = None
            note = "The semantic path exists, but at least one required fit dimension conflicts or the operational specification forbids a non-exact measure."
        elif (relations and relations[0] != "exact_match") or semantic_node_route or contested_relation:
            status = "proxy_candidate"
            transformation = None
            note = f"The selected B alignment is {relations[0] if relations else 'contested'}; human review is required before treating the variable as an empirical proxy."
        else:
            status = "direct_match"
            transformation = None
            note = "An exact R→B alignment reaches a callable variable through the persisted B→A graph; remaining fit dimensions are reported independently."
        mapping_slug = indicator_id.rsplit(":", 1)[-1]
        if mapping_slug.startswith(project["id"].rsplit(":", 1)[-1] + "-"):
            mapping_slug = mapping_slug[len(project["id"].rsplit(":", 1)[-1]) + 1 :]
        human_review_required = status in {"proxy_candidate", "definition_conflict"}
        mappings.append(
            {
                "schema_version": "0.1.0",
                "id": f"grdr:indicator-mapping:{project['id'].rsplit(':', 1)[-1]}-{mapping_slug}",
                "project_id": project["id"],
                "indicator_id": indicator_id,
                "mapping_status": status,
                "variable_ids": variable_ids,
                "semantic_alignment_ids": alignment_ids,
                "semantic_path_ids": path_ids,
                "transformation": transformation,
                "fit": aggregate_fit,
                "human_review_required": human_review_required,
                "review_status": "agent_candidate" if human_review_required else "not_required",
                "notes": note,
            }
        )
        outcome_counts[status] = outcome_counts.get(status, 0) + 1
    validate_records(mappings, SCHEMAS["mappings"], "mappings.jsonl")
    write_jsonl(target / "mappings.jsonl", mappings)
    mapping_status_by_indicator = {item["indicator_id"]: item["mapping_status"] for item in mappings}
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
    append_history(workflow, operation, f"Resolved {len(mappings)} leaf indicators through persisted R→B→A paths: {json.dumps(outcome_counts, sort_keys=True)}.")
    write_json(target / "workflow.json", workflow)
    return {
        "operation": operation.replace("-", "_"),
        "matching_mode": "semantic_graph",
        "project_id": project["id"],
        "matching_attempt": workflow["matching_attempt"],
        "mapping_count": len(mappings),
        "outcomes": dict(sorted(outcome_counts.items())),
        "mappings": mappings,
        "exploratory": project["evidence_stage"] == "topic_scaffold",
        "next_actions": workflow["next_actions"],
    }


def explain_indicator_match(project_dir: str | Path, indicator_id: str) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    ensure_semantic_files(target)
    indicators = {item["id"]: item for item in read_jsonl(target / "indicators.jsonl")}
    if indicator_id not in indicators:
        raise ValueError(f"unknown research indicator: {indicator_id}")
    return {
        "operation": "explain_indicator_match",
        "project_id": read_json(target / "project.json")["id"],
        "indicator": indicators[indicator_id],
        "candidate_recall": [item for item in read_jsonl(target / SEMANTIC_FILES["candidates"]) if item["indicator_id"] == indicator_id],
        "semantic_alignments": [item for item in read_jsonl(target / SEMANTIC_FILES["alignments"]) if item["indicator_id"] == indicator_id],
        "semantic_paths": [item for item in read_jsonl(target / SEMANTIC_FILES["paths"]) if item["indicator_id"] == indicator_id],
        "mapping": next((item for item in read_jsonl(target / "mappings.jsonl") if item["indicator_id"] == indicator_id), None),
    }


def fetch_indicator_data(
    project_dir: str | Path,
    indicator_id: str,
    *,
    variable_id: str | None = None,
    elements_root: str | Path | None = None,
    extra_args: Iterable[str] = (),
    seal_data_snapshot: bool = False,
    route_policy: str = "latest",
) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    mappings = {item["indicator_id"]: item for item in read_jsonl(target / "mappings.jsonl")}
    mapping = mappings.get(indicator_id)
    if mapping is None:
        raise ValueError(f"indicator has no mapping outcome: {indicator_id}")
    from research_project import mapping_snapshot_issues

    snapshot_issues = mapping_snapshot_issues(target, indicator_id=indicator_id)
    if snapshot_issues:
        issue = snapshot_issues[0]
        raise ValueError(
            "indicator mapping is stale: "
            f"{issue['source_id']} moved from {issue['mapped_snapshot_id']} "
            f"to {issue['latest_snapshot_id'] or 'no registered latest snapshot'}; "
            "run prepare-semantic-candidates --replace, rebuild alignment and paths, then rerun-matching"
        )
    if mapping["mapping_status"] == "not_found_registry_snapshot":
        raise ValueError(f"indicator has no callable variable in the current snapshot: {indicator_id}")
    if mapping["human_review_required"] and mapping["review_status"] != "human_approved":
        raise ValueError("contested mapping must receive explicit human approval before data invocation")
    selected = variable_id
    if selected is None:
        if len(mapping["variable_ids"]) != 1:
            raise ValueError("mapping resolves to multiple variables; select --variable-id explicitly")
        selected = mapping["variable_ids"][0]
    if selected not in mapping["variable_ids"]:
        raise ValueError(f"variable is not part of the indicator mapping: {selected}")
    if seal_data_snapshot:
        result = distributed.research_project_data_snapshot(
            source_cards(), selected, target, elements_root, extra_args, route_policy
        )
    else:
        result = distributed.invoke_source_runtime(
            source_cards(), selected, "fetch-variable", elements_root, extra_args, route_policy
        )
    return {
        "operation": "fetch_indicator_data",
        "project_id": read_json(target / "project.json")["id"],
        "indicator_id": indicator_id,
        "mapping_id": mapping["id"],
        "semantic_alignment_ids": mapping.get("semantic_alignment_ids", []),
        "semantic_path_ids": mapping.get("semantic_path_ids", []),
        "variable_id": selected,
        "source_call": result,
    }
