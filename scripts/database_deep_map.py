#!/usr/bin/env python3
"""Persistent, auditable workflow for deep-mapping one database into GRDR."""

from __future__ import annotations

import datetime as dt
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from typing import Any

from database_deep_map_planner import (
    audit_database_deep_map_plan,
    build_database_deep_map_plan_from_intake,
    contract_index,
    load_contracts,
    merge_facets,
)
from grdr_paths import CORE_ROOT, deep_map_projects_root, registry_root


ROOT = CORE_ROOT
PROJECT_ROOT = deep_map_projects_root()
REGISTRY_ROOT = registry_root()
PROJECT_FILE = "project.json"
UNIT_FILE = "units.jsonl"
CHECK_FILE = "checks.jsonl"
REPORT_FILE = "README.md"
STAGING_DIR = "staging"
STAGING_MANIFEST_FILE = "staging_manifest.json"
ARCHIVE_PACKAGE_FILE = "archive_package.json"
ARCHIVE_RECEIPT_FILE = "archive_receipt.json"
PHASES = ["identity", "classification", "boundary", "inventory", "deep_mapping", "validation", "completion_audit"]
EARLY_PHASES = ["identity", "classification", "boundary", "inventory"]
UNIT_STAGES = ["dataset", "data_structure", "data_element", "variable", "construct", "access"]
SPINES = ["structural", "disciplinary", "variable_bridge"]
SPINE_CHECK_STAGES = {
    "structural_spine": "structural",
    "disciplinary_spine": "disciplinary",
    "variable_bridge": "variable_bridge",
}
SPINE_PREREQUISITES = {
    "structural": ("dataset", "data_structure", "data_element", "variable"),
    "disciplinary": ("variable", "construct"),
    "variable_bridge": ("data_element", "variable", "construct"),
}
CLOSED_STATES = {"verified_complete", "not_applicable"}
MAPPED_STATES = {"mapped_complete", *CLOSED_STATES}
ACTIVE_STATES = {"not_started", "enumerating", "in_progress", "blocked"}
CHECK_CLOSED_STATES = {"passed", "not_applicable"}
CHECK_ACTIVE_STATES = {"not_started", "in_progress", "blocked", "failed", "needs_human_review"}
STAGE_PREFIXES = {
    "dataset": "grdr:dataset:",
    "data_structure": "grdr:data-structure:",
    "data_element": "grdr:data-element:",
    "variable": "grdr:variable:",
    "construct": "grdr:construct:",
    "access": "grdr:resource:",
}
REGISTRY_FILES = [
    "institutions.jsonl", "sources.jsonl", "datasets.jsonl", "data_structures.jsonl",
    "resources.jsonl", "data_elements.jsonl", "variables.jsonl", "constructs.jsonl",
    "relationships.jsonl", "adapters.jsonl", "storage.jsonl", "monitors.jsonl",
    "source_profiles.jsonl",
    "semantic_nodes.jsonl",
]
REGISTRY_SCHEMAS = {
    "institutions.jsonl": "institution.schema.json",
    "sources.jsonl": "source.schema.json",
    "datasets.jsonl": "dataset.schema.json",
    "data_structures.jsonl": "data_structure.schema.json",
    "resources.jsonl": "resource.schema.json",
    "data_elements.jsonl": "data_element.schema.json",
    "variables.jsonl": "variable.schema.json",
    "constructs.jsonl": "construct.schema.json",
    "relationships.jsonl": "relationship.schema.json",
    "adapters.jsonl": "adapter.schema.json",
    "storage.jsonl": "storage.schema.json",
    "monitors.jsonl": "monitor.schema.json",
    "source_profiles.jsonl": "source_profile.schema.json",
    "semantic_nodes.jsonl": "semantic_node.schema.json",
}
REGISTRY_PREFIXES = {
    "grdr:institution:": "institutions.jsonl",
    "grdr:source-profile:": "source_profiles.jsonl",
    "grdr:source:": "sources.jsonl",
    "grdr:dataset:": "datasets.jsonl",
    "grdr:data-structure:": "data_structures.jsonl",
    "grdr:resource:": "resources.jsonl",
    "grdr:data-element:": "data_elements.jsonl",
    "grdr:variable:": "variables.jsonl",
    "grdr:construct:": "constructs.jsonl",
    "grdr:relationship:": "relationships.jsonl",
    "grdr:adapter:": "adapters.jsonl",
    "grdr:storage:": "storage.jsonl",
    "grdr:monitor:": "monitors.jsonl",
    "grdr:semantic-node:": "semantic_nodes.jsonl",
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    result = re.sub(r"[^a-z0-9]+", "-", normalized.casefold()).strip("-")
    if not result:
        raise ValueError(f"cannot form a stable identifier from {value!r}")
    return result


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_jsonl_selected(path: Path, record_ids: set[str]) -> dict[str, dict[str, Any]]:
    """Read only requested registry records without materializing the whole collection."""
    if not record_ids or not path.is_file():
        return {}
    selected: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            record_id = record.get("id")
            if record_id in record_ids:
                selected[record_id] = record
                if len(selected) == len(record_ids):
                    break
    return selected


def write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    atomic_write_text(path, "".join(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n" for value in values))


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def fingerprint(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def pipeline_contract() -> dict[str, Any]:
    return {
        "contract_version": "4.2.0",
        "steps": [
            {
                "step": "plan",
                "skill": "grdr-plan-database-deep-map",
                "output": "locked_deep_map_project",
            },
            {
                "step": "execute",
                "skill": "grdr-execute-database-deep-map",
                "output": "sealed_deep_map_execution",
            },
            {
                "step": "storage",
                "skill": "grdr-store-database-deep-map",
                "output": "versioned_database_snapshot",
            },
        ],
        "step_isolation": True,
        "staged_before_storage": True,
        "canonical_writes_storage_only": True,
        "one_repository_per_source": True,
        "one_release_per_snapshot": True,
        "knowledge_agent_github_release_required": True,
        "optional_local_cache": True,
        "observation_location_manifest": True,
        "immutable_core": True,
        "external_state_required": True,
        "fingerprinted_handoffs": True,
    }


def plan_lock_payload(plan: dict[str, Any]) -> dict[str, Any]:
    gates = [
        {key: gate.get(key) for key in ("gate", "reason", "required_before")}
        for gate in plan.get("human_gates", [])
    ]
    return {
        key: plan.get(key)
        for key in (
            "route_contract_version", "source", "goal", "diagnostic_dimensions", "scope",
            "work_unit_strategy", "selected_route_modules", "required_facets", "unresolved_critical",
            "risk_flags", "fallback_policy",
        )
    } | {"human_gate_definitions": gates}


def unit_manifest_payload(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "id", "sequence", "upstream_id", "dataset_id", "unit_type", "disciplines", "origin_type",
        "structural_archetypes", "content_modalities", "lifecycle_modes", "versioning_model",
        "sensitivity_classes", "route_modules", "required_stages",
    )
    return [
        {key: unit.get(key) for key in fields}
        for unit in sorted(units, key=lambda item: (item["sequence"], item["id"]))
    ]


def execution_contract() -> dict[str, Any]:
    return {
        "contract_version": "4.0.0",
        "unknown_database_diagnosis": True,
        "scope_lock": True,
        "deterministic_queue": True,
        "checkpoint_resume": True,
        "deviation_rejection": True,
        "dual_spine_completion": True,
        "evidence_only_completion": True,
        "external_blocker_transparency": True,
        "staging_only_execution": True,
        "storage_only_external_state_write": True,
        "immutable_core": True,
    }


def build_locks(project: dict[str, Any], units: list[dict[str, Any]], timestamp: str) -> dict[str, str]:
    return {
        "plan_fingerprint": fingerprint(plan_lock_payload(project["diagnostic_plan"])),
        "scope_fingerprint": fingerprint(project["scope"]),
        "unit_manifest_fingerprint": fingerprint(unit_manifest_payload(units)),
        "locked_at": timestamp,
    }


def render_report(project: dict[str, Any], audit: dict[str, Any]) -> str:
    progress = audit["progress"]
    next_target = audit.get("next_target")
    if next_target:
        target_checks = next_target.get("required_checks", [])
        next_target_text = (
            f"- 精确目标：`{next_target.get('upstream_id') or next_target.get('phase') or next_target.get('facet_id')}` / "
            f"`{next_target.get('stage') or next_target.get('phase')}`\n"
            f"- 工作单元：`{next_target.get('unit_id', 'project')}`\n"
            f"- 路线：{', '.join(next_target.get('route_modules', [])) or '项目阶段核验'}\n"
            f"- 当前状态：`{next_target['state']}`\n"
            f"- 阶段内检查点：{next_target.get('checkpoint') or '尚未登记'}\n"
            f"- 本目标路线验收项：{len(target_checks)}"
        )
    else:
        next_target_text = "- 当前没有可执行的工作单元目标；请检查审计错误或项目级完成门槛。"
    stage_rows = []
    for name in UNIT_STAGES:
        item = audit["stage_summary"][name]
        stage_rows.append(
            f"| `{name}` | {item['required_units']} | {item['mapped_units']} | "
            f"{item['verified_or_not_applicable_units']} | {item['blocked_units']} |"
        )
    spine_rows = []
    for name in SPINES:
        item = audit["spine_summary"][name]
        spine_rows.append(
            f"| `{name}` | {item['required_units']} | {item['mapped_units']} | "
            f"{item['verified_or_not_applicable_units']} | {item['blocked_units']} |"
        )
    blockers = []
    for phase, value in project["phase_states"].items():
        blockers.extend(f"- 项目阶段 `{phase}`：{item['type']} — {item['notes']}" for item in value["blockers"])
    return f"""# {project['title']}

<!-- Generated by scripts/database_deep_map.py. Edit project.json and units.jsonl through GRDR commands. -->

- 项目：`{project['id']}`
- 数据库：`{project['source_id']}`
- 工作状态：`{project['workflow_status']}`
- 当前阶段：`{project['current_phase']}`
- 范围模式：`{project['diagnostic_plan']['goal']['scope_mode']}`
- 完成声明：`{project['diagnostic_plan']['goal']['completion_claim']}`
- 边界：{project['scope']['boundary_statement']}
- 快照：`{project['scope']['snapshot_at']}`
- 工作单元：{progress['work_units']} / {progress['expected_work_units']}
- 映射进度：**{progress['mapping_percentage']}%**
- 严格完成度：**{progress['strict_completion_percentage']}%**
- 路线契约验收：**{progress['contract_check_percentage']}%**（{progress['closed_contract_checks']} / {progress['required_contract_checks']}）
- 双主干与桥梁严格完成度：**{progress['dual_spine_percentage']}%**（{progress['closed_spines']} / {progress['required_spines']}）
- 全部阶段及双主干完成的工作单元：{progress['fully_closed_work_units']} / {progress['work_units']}
- 可进入 Step 3 Storage：`{str(audit['execution_ready_for_storage']).lower()}`
- 可声明完成：`{str(audit['completion_ready']).lower()}`
- 三步生产线：`plan → execute → storage`
- 当前暂存记录：{audit['staging']['record_count']}（状态：`{audit['staging']['state']}`）
- 中央入库包：`{str(audit['staging']['archive_package_present']).lower()}`；中央入库回执：`{str(audit['staging']['archive_receipt_present']).lower()}`；完整Storage回执：`{str(audit['staging']['storage_receipt_present']).lower()}`
- 执行契约：`{project['execution_contract']['contract_version']}`（全部硬约束：`{str(all(value is True for key, value in project['execution_contract'].items() if key != 'contract_version')).lower()}`）
- 计划锁：`{project['locks']['plan_fingerprint']}`
- 范围锁：`{project['locks']['scope_fingerprint']}`
- 工作单元清单锁：`{project['locks']['unit_manifest_fingerprint']}`

“映射进度”包括已经完成映射但仍待充分核验的阶段；“严格完成度”只计入 `verified_complete` 或有证据的 `not_applicable`。严格阶段达到100%仍不够：路线契约验收、诊断计划、人工门槛、阻塞和审计也必须全部闭合，项目才能完成。

执行计划、范围和工作单元清单均由机器指纹锁定。任何静默改动都会使审计失败，必须通过显式升级重新规划。

## 数据库类型与路线

- 诊断计划：`{project['diagnostic_plan']['plan_status']}`
- 路线契约版本：`{project['diagnostic_plan']['route_contract_version']}`
- 学科：{', '.join(project['database_profile']['disciplines'])}
- 数据来源：`{project['database_profile']['origin_type']}`
- 来源角色：`{project['database_profile']['provenance_role']}`
- 生产方式：{', '.join(project['database_profile']['production_modes'])}
- 结构类型：{', '.join(project['database_profile']['structural_archetypes'])}
- 执行路线：{', '.join(project['database_profile']['route_modules'])}
- 访问制度：`{project['database_profile']['access_regime']}`
- 风险标记：{', '.join(project['diagnostic_plan']['risk_flags']) or '无'}
- 未解决关键维度：{len(project['diagnostic_plan']['unresolved_critical'])}
- 人工门槛：{len([item for item in project['diagnostic_plan']['human_gates'] if item['status'] == 'pending'])} 个待决

## 分阶段进度

| 阶段 | 必需单元 | 已映射 | 已严格闭合 | 阻塞 |
|---|---:|---:|---:|---:|
{chr(10).join(stage_rows)}

## 两根主干与变量桥梁

| 主干/桥梁 | 必需单元 | 已映射 | 已严格闭合 | 阻塞 |
|---|---:|---:|---:|---:|
{chr(10).join(spine_rows)}

## 下一步

{next_target_text}

{chr(10).join(f'- `{item}`' for item in project['next_actions']) or '- 无'}

## 阻塞

{chr(10).join(blockers) or '- 项目级无阻塞；工作单元阻塞见 `units.jsonl` 和状态命令。'}

## 审计

- 错误数：{len(audit['errors'])}
- 警告数：{len(audit['warnings'])}
- 状态命令：`python3 scripts/grdr.py database-deep-map-status {Path(audit['project_dir']).name}`
"""


def sync_report(target: Path, project: dict[str, Any], audit: dict[str, Any]) -> None:
    atomic_write_text(target / REPORT_FILE, render_report(project, audit))


def resolve_project_dir(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        candidate = PROJECT_ROOT / path
        path = candidate if candidate.exists() or len(path.parts) == 1 else ROOT / path
    return path.resolve()


def require_project(path: Path) -> None:
    missing = [name for name in (PROJECT_FILE, UNIT_FILE, CHECK_FILE) if not (path / name).is_file()]
    if missing:
        raise ValueError(f"incomplete database deep-map project {path}: missing {', '.join(missing)}")


def canonical_collections() -> dict[str, list[dict[str, Any]]]:
    return {
        filename: read_jsonl(REGISTRY_ROOT / filename)
        for filename in REGISTRY_FILES
    }


def completed_distributed_archive_exists(source_id: str) -> bool:
    path = REGISTRY_ROOT / "source_archives.jsonl"
    return path.is_file() and any(
        item.get("source_id") == source_id and item.get("status") == "complete"
        for item in read_jsonl(path)
    )


def empty_staging_manifest(project: dict[str, Any], timestamp: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "project_id": project["id"],
        "source_id": project["source_id"],
        "state": "open",
        "records": [],
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def ensure_staging_manifest(target: Path, project: dict[str, Any]) -> dict[str, Any]:
    path = target / STAGING_MANIFEST_FILE
    if path.is_file():
        return read_json(path)
    manifest = empty_staging_manifest(project, now())
    write_json(path, manifest)
    return manifest


def staged_collections(target: Path) -> dict[str, list[dict[str, Any]]]:
    directory = target / STAGING_DIR
    return {
        filename: read_jsonl(directory / filename) if (directory / filename).is_file() else []
        for filename in REGISTRY_FILES
    }


def merged_collections(target: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    canonical = canonical_collections()
    if target is None:
        return canonical
    staged = staged_collections(target)
    merged: dict[str, list[dict[str, Any]]] = {}
    for filename in REGISTRY_FILES:
        by_id = {record["id"]: record for record in canonical[filename]}
        order = [record["id"] for record in canonical[filename]]
        for record in staged[filename]:
            if record["id"] not in by_id:
                order.append(record["id"])
            by_id[record["id"]] = record
        merged[filename] = [by_id[record_id] for record_id in order]
    return merged


def registry_index(target: Path | None = None) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for collection in merged_collections(target).values():
        for record in collection:
            records[record["id"]] = record
    return records


def registry_index_for_ids(
    record_ids: set[str],
    target: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Resolve a bounded record set, with staged records overriding canonical ones."""
    wanted = {item for item in record_ids if isinstance(item, str) and item}
    records: dict[str, dict[str, Any]] = {}
    if target is not None:
        directory = target / STAGING_DIR
        for filename in REGISTRY_FILES:
            records.update(read_jsonl_selected(directory / filename, wanted - set(records)))
    for filename in REGISTRY_FILES:
        records.update(read_jsonl_selected(REGISTRY_ROOT / filename, wanted - set(records)))
    return records


def registry_file_for_record(record: dict[str, Any]) -> str:
    record_id = record.get("id")
    if not isinstance(record_id, str):
        raise ValueError("staged record requires a canonical id")
    for prefix, filename in REGISTRY_PREFIXES.items():
        if record_id.startswith(prefix):
            return filename
    raise ValueError(f"unsupported staged canonical id type: {record_id}")


def read_record_batch(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    stripped = raw.strip()
    if not stripped:
        raise ValueError("staged record batch is empty")
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        values = [json.loads(line) for line in raw.splitlines() if line.strip()]
    else:
        values = parsed if isinstance(parsed, list) else [parsed]
    if not isinstance(values, list) or not all(isinstance(item, dict) for item in values):
        raise ValueError("staged record batch must be a JSON object, JSON array, or JSONL objects")
    record_ids = [item.get("id") for item in values]
    seen: set[Any] = set()
    duplicates: set[Any] = set()
    for record_id in record_ids:
        if record_id in seen:
            duplicates.add(record_id)
        else:
            seen.add(record_id)
    duplicates = sorted(duplicates, key=str)
    if duplicates:
        raise ValueError("staged record batch contains duplicate IDs: " + ", ".join(duplicates))
    return values


def collection_name(filename: str) -> str:
    return filename.removesuffix(".jsonl")


def referenced_registry_ids(record: dict[str, Any]) -> set[str]:
    """Return canonical entity IDs referenced anywhere in one registry record.

    The schemas evolve, so the closure walker deliberately follows every
    recognized GRDR entity identifier instead of maintaining a second fragile
    list of foreign-key field names.  The record's own ID is not a reference.
    """

    references: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str) and any(value.startswith(prefix) for prefix in REGISTRY_PREFIXES):
            references.add(value)

    visit(record)
    references.discard(record.get("id"))
    return references


def staged_registry_closure(target: Path) -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
    """Build only the staged records and their transitive canonical references."""

    from validate_registry import collection_paths, validate_integrity, validate_with_jsonschema

    staged = staged_collections(target)
    staged_records = [record for records in staged.values() for record in records]
    errors = validate_with_jsonschema({
        collection_name(filename): records
        for filename, records in staged.items()
        if records
    })
    staged_ids = [record.get("id") for record in staged_records]
    if len(staged_ids) != len(set(staged_ids)):
        errors.append("staging files contain duplicate canonical IDs")

    closure = {
        record["id"]: record
        for record in staged_records
        if isinstance(record.get("id"), str)
    }
    attempted: set[str] = set(closure)
    frontier = {
        reference
        for record in closure.values()
        for reference in referenced_registry_ids(record)
    } - attempted
    while frontier:
        resolved = registry_index_for_ids(frontier, target)
        closure.update(resolved)
        attempted.update(frontier)
        frontier = {
            reference
            for record in resolved.values()
            for reference in referenced_registry_ids(record)
        } - attempted

    collection_names = collection_paths(REGISTRY_ROOT)
    collections = {name: [] for name in collection_names}
    for record in closure.values():
        try:
            filename = registry_file_for_record(record)
        except ValueError:
            continue
        collections[collection_name(filename)].append(record)
    errors.extend(validate_integrity(collections))

    # A source may have only one current profile.  This constraint is keyed by
    # source_id rather than record ID, so check the small canonical profile file
    # explicitly without materializing unrelated registry collections.
    staged_profiles = staged.get("source_profiles.jsonl", [])
    staged_profile_ids = {record["id"] for record in staged_profiles}
    source_to_profile: dict[str, str] = {}
    for profile in staged_profiles:
        source_id = profile.get("source_id")
        if source_id in source_to_profile:
            errors.append(f"{profile.get('id')}: duplicate current profile for {source_id}")
        source_to_profile[source_id] = profile.get("id")
    profile_path = REGISTRY_ROOT / "source_profiles.jsonl"
    if source_to_profile and profile_path.is_file():
        with profile_path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                if not raw.strip():
                    continue
                profile = json.loads(raw)
                if profile.get("id") in staged_profile_ids:
                    continue
                source_id = profile.get("source_id")
                if source_id in source_to_profile:
                    errors.append(
                        f"{source_to_profile[source_id]}: duplicate current profile for {source_id}"
                    )
    return collections, errors


def validate_merged_registry(target: Path) -> list[str]:
    """Validate a prospective transaction without loading the historical registry.

    Unchanged canonical state has already passed global validation.  Therefore a
    new transaction needs schema validation for staged records plus referential
    validation for the staged transitive closure only.  Runtime and memory now
    scale with the incoming database rather than every database ever registered.
    """

    _collections, errors = staged_registry_closure(target)
    return errors


def write_streamed_registry_merge(
    canonical_path: Path,
    output_path: Path,
    changed_records: dict[str, dict[str, Any]],
) -> None:
    """Write one prospective registry file while retaining at most new rows in memory."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    with output_path.open("w", encoding="utf-8") as output:
        if canonical_path.is_file():
            with canonical_path.open("r", encoding="utf-8") as canonical:
                for raw in canonical:
                    if not raw.strip():
                        continue
                    record = json.loads(raw)
                    record_id = record.get("id")
                    replacement = changed_records.get(record_id)
                    if replacement is None:
                        output.write(raw if raw.endswith("\n") else raw + "\n")
                    else:
                        output.write(json.dumps(replacement, ensure_ascii=False, separators=(",", ":")) + "\n")
                        seen.add(record_id)
        for record_id, record in changed_records.items():
            if record_id not in seen:
                output.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        output.flush()
        os.fsync(output.fileno())


def execution_ledger_fingerprint(units: list[dict[str, Any]], checks: list[dict[str, Any]]) -> str:
    return fingerprint({"units": units, "checks": checks})


def staging_manifest_fingerprint(manifest: dict[str, Any]) -> str:
    return fingerprint({
        key: value
        for key, value in manifest.items()
        if key not in {"state", "updated_at"}
    })


def archive_package_payload(
    project: dict[str, Any],
    units: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    manifest: dict[str, Any],
    timestamp: str,
) -> dict[str, Any]:
    counts = {
        filename: sum(item["registry_file"] == filename for item in manifest["records"])
        for filename in REGISTRY_FILES
    }
    package = {
        "schema_version": "1.0.0",
        "project_id": project["id"],
        "source_id": project["source_id"],
        "plan_fingerprint": project["locks"]["plan_fingerprint"],
        "scope_fingerprint": project["locks"]["scope_fingerprint"],
        "unit_manifest_fingerprint": project["locks"]["unit_manifest_fingerprint"],
        "execution_ledger_fingerprint": execution_ledger_fingerprint(units, checks),
        "staging_manifest_fingerprint": staging_manifest_fingerprint(manifest),
        "record_count": len(manifest["records"]),
        "collection_counts": {key: value for key, value in counts.items() if value},
        "prepared_at": timestamp,
    }
    package["package_fingerprint"] = fingerprint(package)
    return package


def archive_receipt_is_valid(target: Path, project: dict[str, Any]) -> bool:
    package_path = target / ARCHIVE_PACKAGE_FILE
    receipt_path = target / ARCHIVE_RECEIPT_FILE
    if not package_path.is_file() or not receipt_path.is_file():
        return False
    try:
        package = read_json(package_path)
        receipt = read_json(receipt_path)
        units = read_jsonl(target / UNIT_FILE)
        checks = read_jsonl(target / CHECK_FILE)
        manifest = read_json(target / STAGING_MANIFEST_FILE)
        return (
            not validate_schema(package, "database_deep_map_archive_package.schema.json", ARCHIVE_PACKAGE_FILE)
            and not validate_schema(receipt, "database_deep_map_archive_receipt.schema.json", ARCHIVE_RECEIPT_FILE)
            and package.get("project_id") == project["id"]
            and package.get("source_id") == project["source_id"]
            and receipt.get("project_id") == project["id"]
            and receipt.get("source_id") == project["source_id"]
            and receipt.get("package_fingerprint") == package.get("package_fingerprint")
            and package.get("plan_fingerprint") == project["locks"]["plan_fingerprint"]
            and package.get("scope_fingerprint") == project["locks"]["scope_fingerprint"]
            and package.get("unit_manifest_fingerprint") == project["locks"]["unit_manifest_fingerprint"]
            and package.get("execution_ledger_fingerprint") == execution_ledger_fingerprint(units, checks)
            and package.get("staging_manifest_fingerprint") == staging_manifest_fingerprint(manifest)
            and receipt.get("receipt_fingerprint")
            == fingerprint({key: value for key, value in receipt.items() if key != "receipt_fingerprint"})
        )
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def evidence_from(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "url": item["url"],
            "title": item["title"],
            "evidence_type": item["evidence_type"],
            "supports": item["supports"],
            "retrieved_at": item["retrieved_at"],
        }
        for item in record.get("evidence", [])
    ]


def empty_stage(timestamp: str) -> dict[str, Any]:
    return {
        "state": "not_started", "expected_count": None, "registered_ids": [],
        "verified_count": 0, "completion_basis": None, "evidence": [],
        "blockers": [], "notes": None, "updated_at": timestamp,
    }


def empty_spine(timestamp: str) -> dict[str, Any]:
    return {
        "state": "not_started",
        "expected_node_count": None,
        "node_ids": [],
        "verified_node_count": 0,
        "expected_edge_count": None,
        "edge_ids": [],
        "verified_edge_count": 0,
        "root_node_ids": [],
        "leaf_node_ids": [],
        "topology_fingerprint": None,
        "topology_fingerprint_version": "topology-v2",
        "completion_basis": None,
        "evidence": [],
        "blockers": [],
        "checkpoint": {
            "enumeration_rule": None,
            "completed_native_count": 0,
            "last_native_id": None,
            "next_native_id": None,
            "snapshot": None,
            "cursor_checksum": None,
        },
        "updated_at": timestamp,
    }


def phase_state(state: str, timestamp: str, basis: str | None = None, evidence: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "state": state, "completion_basis": basis, "evidence": evidence or [],
        "blockers": [], "updated_at": timestamp,
    }


def expected_check_specs(project: dict[str, Any], units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = []
    selected = set(project["diagnostic_plan"]["selected_route_modules"])
    for facet in project["diagnostic_plan"]["required_facets"]:
        source_routes = set(facet["source_routes"])
        if facet["scope"] == "project":
            applicable = sorted(source_routes & selected)
            if applicable:
                specs.append({**facet, "unit_id": None, "route_modules": applicable})
            continue
        for unit in units:
            applicable = sorted(source_routes & set(unit["route_modules"]))
            if applicable:
                specs.append({**facet, "unit_id": unit["id"], "route_modules": applicable})
    return specs


def check_identifier(project: dict[str, Any], spec: dict[str, Any]) -> str:
    project_slug = project["id"].rsplit(":", 1)[-1]
    unit_slug = spec["unit_id"].rsplit(":", 1)[-1] if spec["unit_id"] else "project"
    native_id = f"{project_slug}-{unit_slug}-{spec['id']}"
    return f"grdr:deep-map-check:{slug(native_id)}"


def materialize_checks(project: dict[str, Any], units: list[dict[str, Any]], timestamp: str) -> list[dict[str, Any]]:
    checks = []
    for facet in expected_check_specs(project, units):
        checks.append({
            "schema_version": "1.0.0",
            "id": check_identifier(project, facet),
            "project_id": project["id"],
            "unit_id": facet["unit_id"],
            "route_modules": facet["route_modules"],
            "facet_id": facet["id"],
            "scope": facet["scope"],
            "stage": facet["stage"],
            "requirement": facet["requirement"],
            "required": True,
            "state": "not_started",
            "completion_basis": None,
            "evidence": [],
            "blockers": [],
            "notes": None,
            "created_at": timestamp,
            "updated_at": timestamp,
        })
    return checks


def check_errors(check: dict[str, Any], project: dict[str, Any], unit_ids: set[str], route_ids: set[str]) -> list[str]:
    errors = []
    label = check.get("id", "check")
    if check.get("project_id") != project["id"]:
        errors.append(f"{label}: project_id does not match {project['id']}")
    if check["scope"] == "project" and check["unit_id"] is not None:
        errors.append(f"{label}: project-scoped check cannot reference a unit")
    if check["scope"] == "unit" and check["unit_id"] not in unit_ids:
        errors.append(f"{label}: unknown or missing unit_id {check['unit_id']}")
    for route_id in check["route_modules"]:
        if route_id not in route_ids:
            errors.append(f"{label}: unknown route module {route_id}")
    if check["state"] in CHECK_CLOSED_STATES:
        if not check["completion_basis"] or not check["evidence"]:
            errors.append(f"{label}: a passed or not-applicable check requires completion_basis and evidence")
    if check["state"] in {"blocked", "failed", "needs_human_review"} and not check["blockers"]:
        errors.append(f"{label}: {check['state']} requires at least one typed blocker")
    return errors


def route_blockers_from_stage(blockers: list[dict[str, Any]]) -> list[dict[str, str]]:
    recoverability = {
        "access": "alternative_route", "authentication": "requires_authorization",
        "payment": "requires_authorization", "license": "requires_authorization",
        "privacy": "requires_human_decision", "ethics": "requires_human_decision",
        "technical": "retryable", "scale": "alternative_route",
        "missing_metadata": "upstream_only", "schema_drift": "alternative_route",
        "semantic_ambiguity": "requires_human_decision", "quality": "upstream_only",
        "other": "unknown",
    }
    return [
        {
            "type": item["type"], "scope": "stage",
            "recoverability": recoverability.get(item["type"], "unknown"),
            "resolution": f"Resolve the inherited {item['type']} blocker before closing this route obligation.",
            "notes": item["notes"],
        }
        for item in blockers
    ]


def synchronize_blocked_stage_checks(units: list[dict[str, Any]], checks: list[dict[str, Any]], timestamp: str) -> int:
    blocked_stages = {
        (unit["id"], stage_name): stage
        for unit in units
        for stage_name, stage in unit["stages"].items()
        if stage["state"] == "blocked"
    }
    changed = 0
    for check in checks:
        stage = blocked_stages.get((check["unit_id"], check["stage"]))
        if stage is None or check["state"] not in {"not_started", "in_progress"}:
            continue
        check.update({
            "state": "blocked", "completion_basis": None, "evidence": [],
            "blockers": route_blockers_from_stage(stage["blockers"]),
            "notes": "Inherited from the blocked work-unit stage; resolve each route obligation explicitly.",
            "updated_at": timestamp,
        })
        changed += 1
    return changed


def unit_gate_state(unit: dict[str, Any], stage: str) -> str:
    if stage in SPINE_CHECK_STAGES:
        return unit["spines"][SPINE_CHECK_STAGES[stage]]["state"]
    return unit["stages"][stage]["state"]


def append_history(project: dict[str, Any], operation: str, summary: str) -> None:
    timestamp = now()
    project["history"].append({"timestamp": timestamp, "operation": operation, "summary": summary})
    project["updated_at"] = timestamp


@lru_cache(maxsize=None)
def schema_validator(schema_name: str) -> Any:
    try:
        import jsonschema
    except ImportError as exc:
        raise RuntimeError(
            "strict database deep-map validation requires jsonschema; install with "
            "python3 -m pip install -r requirements-validation.txt"
        ) from exc
    schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())


def validate_schema(value: Any, schema_name: str, label: str) -> list[str]:
    validator = schema_validator(schema_name)
    errors = []
    for error in validator.iter_errors(value):
        location = ".".join(str(part) for part in error.path) or "<record>"
        errors.append(f"{label}:{location}: {error.message}")
    return errors


def stage_errors(unit: dict[str, Any], stage_name: str, stage: dict[str, Any], known_ids: set[str]) -> list[str]:
    errors = []
    label = f"{unit['id']}:{stage_name}"
    registered = stage["registered_ids"]
    expected = stage["expected_count"]
    verified = stage["verified_count"]
    prefix = STAGE_PREFIXES[stage_name]
    if verified > len(registered):
        errors.append(f"{label}: verified_count exceeds registered count")
    for record_id in registered:
        if not record_id.startswith(prefix):
            errors.append(f"{label}: {record_id} has the wrong entity type")
        if record_id not in known_ids:
            errors.append(f"{label}: unknown canonical registry id {record_id}")
    if stage["state"] in {"mapped_complete", "verified_complete"}:
        if expected is None:
            errors.append(f"{label}: a complete state requires a known expected_count")
        elif expected != len(registered):
            errors.append(f"{label}: expected_count={expected} but registered_ids={len(registered)}")
        if not stage["completion_basis"] or not stage["evidence"]:
            errors.append(f"{label}: a complete state requires completion_basis and evidence")
    if stage["state"] == "verified_complete" and expected is not None and verified != expected:
        errors.append(f"{label}: verified_complete requires verified_count == expected_count")
    if stage["state"] == "not_applicable":
        if expected != 0 or registered:
            errors.append(f"{label}: not_applicable requires expected_count=0 and no registered IDs")
        if not stage["completion_basis"] or not stage["evidence"]:
            errors.append(f"{label}: not_applicable requires evidence and a reason")
    if stage["state"] == "blocked" and not stage["blockers"]:
        errors.append(f"{label}: blocked state requires at least one blocker")
    if stage_name == "dataset" and unit.get("dataset_id") and registered and unit["dataset_id"] not in registered:
        errors.append(f"{label}: dataset_id is not included in registered_ids")
    return errors


def spine_topology_fingerprint(spine: dict[str, Any], records: dict[str, dict[str, Any]]) -> str:
    """Fingerprint graph topology without serializing complete scientific records.

    Definitions, evidence, Codelists, and other record payloads are already bound by
    the staging manifest. A spine checkpoint only needs to bind node identity, edge
    identity and endpoints, plus its declared roots and leaves.
    """
    edges = [
        {
            "id": item,
            "subject_id": records[item].get("subject_id"),
            "predicate": records[item].get("predicate"),
            "object_id": records[item].get("object_id"),
        }
        for item in sorted(spine["edge_ids"])
        if item in records
    ]
    return fingerprint({
        "format": "topology-v2",
        "node_ids": sorted(item for item in spine["node_ids"] if item in records),
        "edges": edges,
        "roots": sorted(spine["root_node_ids"]),
        "leaves": sorted(spine["leaf_node_ids"]),
    })


def legacy_spine_topology_fingerprint(spine: dict[str, Any], records: dict[str, dict[str, Any]]) -> str:
    """Retain read compatibility for pre-4.5.4 unversioned checkpoints."""
    nodes = [records[item] for item in sorted(spine["node_ids"]) if item in records]
    edges = [records[item] for item in sorted(spine["edge_ids"]) if item in records]
    return fingerprint({
        "nodes": nodes,
        "edges": edges,
        "roots": sorted(spine["root_node_ids"]),
        "leaves": sorted(spine["leaf_node_ids"]),
    })


def checkpoint_checksum(checkpoint: dict[str, Any]) -> str:
    return fingerprint({key: checkpoint.get(key) for key in (
        "enumeration_rule", "completed_native_count", "last_native_id", "next_native_id", "snapshot",
    )})


def spine_errors(
    unit: dict[str, Any],
    spine_name: str,
    spine: dict[str, Any],
    records: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    label = f"{unit['id']}:{spine_name}_spine"
    allowed_prefixes = {
        "structural": ("grdr:dataset:", "grdr:data-structure:", "grdr:data-element:", "grdr:variable:"),
        "disciplinary": ("grdr:semantic-node:", "grdr:construct:"),
        "variable_bridge": ("grdr:data-structure:", "grdr:data-element:", "grdr:variable:", "grdr:construct:", "grdr:semantic-node:"),
    }[spine_name]
    node_ids = spine["node_ids"]
    node_id_set = set(node_ids)
    edge_ids = spine["edge_ids"]
    expected_nodes = spine["expected_node_count"]
    expected_edges = spine["expected_edge_count"]
    for node_id in node_ids:
        if not node_id.startswith(allowed_prefixes):
            errors.append(f"{label}: disallowed node type {node_id}")
        if node_id not in records:
            errors.append(f"{label}: unknown canonical node {node_id}")
            continue
        record = records[node_id]
        if node_id.startswith("grdr:dataset:") and unit.get("dataset_id") and node_id != unit["dataset_id"]:
            errors.append(f"{label}: dataset node {node_id} does not match the work unit dataset")
        if node_id.startswith(("grdr:data-structure:", "grdr:data-element:", "grdr:variable:")):
            dataset_ids = set(record.get("dataset_ids", []))
            if unit.get("dataset_id") and unit["dataset_id"] not in dataset_ids:
                errors.append(f"{label}: node {node_id} does not belong to the work unit dataset")
    for edge_id in edge_ids:
        record = records.get(edge_id)
        if record is None or not edge_id.startswith("grdr:relationship:"):
            errors.append(f"{label}: unknown canonical relationship {edge_id}")
            continue
        if record.get("subject_id") not in node_id_set or record.get("object_id") not in node_id_set:
            errors.append(f"{label}: edge {edge_id} has an endpoint outside the declared spine nodes")
    for boundary_name in ("root_node_ids", "leaf_node_ids"):
        unknown = sorted(set(spine[boundary_name]) - node_id_set)
        if unknown:
            errors.append(f"{label}: {boundary_name} contains nodes outside node_ids: {', '.join(unknown)}")
    actual_verified_nodes = sum(
        records.get(item, {}).get("verification", {}).get("status") == "verified"
        for item in node_ids
    )
    actual_verified_edges = sum(
        records.get(item, {}).get("verification", {}).get("status") == "verified"
        for item in edge_ids
    )
    if spine["verified_node_count"] != actual_verified_nodes:
        errors.append(f"{label}: verified_node_count does not match canonical verification states")
    if spine["verified_edge_count"] != actual_verified_edges:
        errors.append(f"{label}: verified_edge_count does not match canonical verification states")
    if spine["state"] in {"mapped_complete", "verified_complete"}:
        prerequisite_stages = SPINE_PREREQUISITES[spine_name]
        open_prerequisites = [
            name for name in prerequisite_stages
            if unit["stages"][name]["state"] not in MAPPED_STATES
        ]
        if open_prerequisites:
            errors.append(f"{label}: cannot close before mapped prerequisite stages: {', '.join(open_prerequisites)}")
        if expected_nodes is None or expected_edges is None:
            errors.append(f"{label}: complete spine requires known node and edge denominators")
        if expected_nodes != len(node_ids):
            errors.append(f"{label}: expected_node_count={expected_nodes} but node_ids={len(node_ids)}")
        if expected_edges != len(edge_ids):
            errors.append(f"{label}: expected_edge_count={expected_edges} but edge_ids={len(edge_ids)}")
        if not node_ids or not spine["root_node_ids"] or not spine["leaf_node_ids"]:
            errors.append(f"{label}: complete spine requires nodes, roots, and leaves")
        required_prefixes = {
            "structural": ("grdr:dataset:", "grdr:data-structure:", "grdr:data-element:", "grdr:variable:"),
            "disciplinary": ("grdr:semantic-node:", "grdr:construct:"),
            "variable_bridge": ("grdr:variable:", "grdr:construct:"),
        }[spine_name]
        missing_types = [prefix for prefix in required_prefixes if not any(item.startswith(prefix) for item in node_ids)]
        if missing_types:
            errors.append(f"{label}: complete spine lacks required canonical node types: {', '.join(missing_types)}")
        if spine_name == "variable_bridge" and not edge_ids:
            errors.append(f"{label}: the variable bridge requires at least one canonical relationship")
        adjacency = {item: set() for item in node_ids}
        for edge_id in edge_ids:
            edge = records.get(edge_id, {})
            subject = edge.get("subject_id"); object_id = edge.get("object_id")
            if subject in adjacency and object_id in adjacency:
                adjacency[subject].add(object_id); adjacency[object_id].add(subject)
        reachable = set(spine["root_node_ids"])
        pending = list(reachable)
        while pending:
            current = pending.pop()
            for neighbor in adjacency.get(current, set()) - reachable:
                reachable.add(neighbor); pending.append(neighbor)
        disconnected = sorted(node_id_set - reachable)
        if disconnected:
            errors.append(f"{label}: nodes are disconnected from declared roots: {', '.join(disconnected)}")
        if not spine["completion_basis"] or not spine["evidence"]:
            errors.append(f"{label}: complete spine requires completion_basis and evidence")
        checkpoint = spine["checkpoint"]
        if not checkpoint["enumeration_rule"] or checkpoint["snapshot"] is None:
            errors.append(f"{label}: complete spine requires a dated deterministic enumeration rule")
        if checkpoint["next_native_id"] is not None:
            errors.append(f"{label}: complete spine requires next_native_id=null")
        if expected_nodes is not None and checkpoint["completed_native_count"] != expected_nodes:
            errors.append(f"{label}: completed_native_count must equal expected_node_count")
        if checkpoint["cursor_checksum"] != checkpoint_checksum(checkpoint):
            errors.append(f"{label}: checkpoint cursor checksum is missing or stale")
        expected_fingerprint = (
            spine_topology_fingerprint(spine, records)
            if spine.get("topology_fingerprint_version") == "topology-v2"
            else legacy_spine_topology_fingerprint(spine, records)
        )
        if spine["topology_fingerprint"] != expected_fingerprint:
            errors.append(f"{label}: topology fingerprint is missing or stale")
    if spine["state"] == "verified_complete":
        if expected_nodes is not None and spine["verified_node_count"] != expected_nodes:
            errors.append(f"{label}: verified_complete requires every node verified")
        if expected_edges is not None and spine["verified_edge_count"] != expected_edges:
            errors.append(f"{label}: verified_complete requires every edge verified")
    if spine["state"] == "not_applicable":
        if expected_nodes != 0 or expected_edges != 0 or node_ids or edge_ids:
            errors.append(f"{label}: not_applicable requires zero denominators and no nodes or edges")
        if not spine["completion_basis"] or not spine["evidence"]:
            errors.append(f"{label}: not_applicable requires evidence")
    if spine["state"] == "blocked" and not spine["blockers"]:
        errors.append(f"{label}: blocked spine requires at least one blocker")
    return errors


def phase_errors(project: dict[str, Any], name: str, value: dict[str, Any]) -> list[str]:
    errors = []
    label = f"{project['id']}:{name}"
    if value["state"] in {"mapped_complete", "verified_complete", "not_applicable"}:
        if not value["completion_basis"] or not value["evidence"]:
            errors.append(f"{label}: closed or mapped phase requires completion_basis and evidence")
    if value["state"] == "blocked" and not value["blockers"]:
        errors.append(f"{label}: blocked phase requires at least one blocker")
    return errors


def staging_errors(
    target: Path,
    project: dict[str, Any],
    manifest: dict[str, Any],
    *,
    canonical: dict[str, dict[str, Any]] | None = None,
    staged: dict[str, list[dict[str, Any]]] | None = None,
) -> list[str]:
    errors = validate_schema(
        manifest,
        "database_deep_map_staging_manifest.schema.json",
        STAGING_MANIFEST_FILE,
    )
    if manifest.get("project_id") != project["id"]:
        errors.append("staging manifest project_id does not match the project")
    if manifest.get("source_id") != project["source_id"]:
        errors.append("staging manifest source_id does not match the project")
    staged = staged if staged is not None else staged_collections(target)
    staged_by_id = {
        record["id"]: (filename, record)
        for filename, records in staged.items()
        for record in records
    }
    canonical = canonical if canonical is not None else registry_index_for_ids(set(staged_by_id))
    distributed_archive_present = completed_distributed_archive_exists(project["source_id"])
    manifest_ids = [item["id"] for item in manifest.get("records", [])]
    if len(manifest_ids) != len(set(manifest_ids)):
        errors.append("staging manifest contains duplicate record IDs")
    if set(manifest_ids) != set(staged_by_id):
        missing = sorted(set(staged_by_id) - set(manifest_ids))
        extra = sorted(set(manifest_ids) - set(staged_by_id))
        if missing:
            errors.append("staging manifest omits staged IDs: " + ", ".join(missing))
        if extra:
            errors.append("staging manifest references missing staged IDs: " + ", ".join(extra))
    for item in manifest.get("records", []):
        staged_item = staged_by_id.get(item["id"])
        if staged_item is None:
            continue
        filename, record = staged_item
        if item["registry_file"] != filename:
            errors.append(f"{item['id']}: staging manifest registry_file does not match its file")
        if item["staged_fingerprint"] != fingerprint(record):
            errors.append(f"{item['id']}: staged fingerprint is stale")
        canonical_record = canonical.get(item["id"])
        if manifest.get("state") == "archived":
            if canonical_record != record and not (canonical_record is None and distributed_archive_present):
                errors.append(f"{item['id']}: archived staged record no longer matches canonical state")
        else:
            expected_base = fingerprint(canonical_record) if canonical_record is not None else None
            if item["base_fingerprint"] != expected_base:
                errors.append(f"{item['id']}: staging base fingerprint no longer matches canonical state")
            expected_action = (
                "create" if canonical_record is None
                else "unchanged" if canonical_record == record
                else "update"
            )
            if item["action"] != expected_action:
                errors.append(f"{item['id']}: staging action should be {expected_action}, not {item['action']}")
        errors.extend(validate_schema(record, REGISTRY_SCHEMAS[filename], f"staging/{filename}:{item['id']}"))
    return errors


def audit_database_deep_map(project_dir: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    require_project(target)
    project = read_json(target / PROJECT_FILE)
    units = read_jsonl(target / UNIT_FILE)
    checks = read_jsonl(target / CHECK_FILE)
    manifest_path = target / STAGING_MANIFEST_FILE
    manifest = read_json(manifest_path) if manifest_path.is_file() else empty_staging_manifest(project, project["created_at"])
    contracts = load_contracts()
    route_ids = set(contract_index(contracts))
    staged = staged_collections(target)
    staged_ids = {
        record["id"]
        for collection in staged.values()
        for record in collection
    }
    referenced_ids = {project["source_id"], *staged_ids}
    for unit in units:
        if unit.get("dataset_id"):
            referenced_ids.add(unit["dataset_id"])
        for stage in unit["stages"].values():
            referenced_ids.update(stage["registered_ids"])
        for spine in unit["spines"].values():
            referenced_ids.update(spine["node_ids"])
            referenced_ids.update(spine["edge_ids"])
    canonical_records = registry_index_for_ids(referenced_ids)
    known_records = dict(canonical_records)
    for collection in staged.values():
        known_records.update({record["id"]: record for record in collection})
    known_ids = set(known_records)
    errors = validate_schema(project, "database_deep_map_project.schema.json", PROJECT_FILE)
    if not manifest_path.is_file():
        errors.append(f"missing required {STAGING_MANIFEST_FILE}")
    else:
        errors.extend(
            staging_errors(
                target,
                project,
                manifest,
                canonical=canonical_records,
                staged=staged,
            )
        )
    plan_audit = audit_database_deep_map_plan(project.get("diagnostic_plan", {}))
    errors.extend(f"diagnostic_plan: {item}" for item in plan_audit["errors"])
    warnings = []
    seen_units, seen_upstream = set(), set()
    for index, unit in enumerate(units, 1):
        errors.extend(validate_schema(unit, "database_deep_map_unit.schema.json", f"{UNIT_FILE}:{index}"))
        if unit["id"] in seen_units:
            errors.append(f"duplicate work-unit id {unit['id']}")
        if unit["upstream_id"] in seen_upstream:
            errors.append(f"duplicate upstream work-unit id {unit['upstream_id']}")
        seen_units.add(unit["id"]); seen_upstream.add(unit["upstream_id"])
        if unit["project_id"] != project["id"]:
            errors.append(f"{unit['id']}: project_id does not match {project['id']}")
        if unit.get("dataset_id") and unit["dataset_id"] not in known_ids:
            errors.append(f"{unit['id']}: unknown dataset_id {unit['dataset_id']}")
        for route_id in unit["route_modules"]:
            if route_id not in route_ids:
                errors.append(f"{unit['id']}: unknown route module {route_id}")
            if route_id not in project["diagnostic_plan"]["selected_route_modules"]:
                errors.append(f"{unit['id']}: route module {route_id} is absent from the project diagnostic plan")
        for stage_name, stage in unit["stages"].items():
            errors.extend(stage_errors(unit, stage_name, stage, known_ids))
        for spine_name, spine in unit["spines"].items():
            errors.extend(spine_errors(unit, spine_name, spine, known_records))
    unit_ids = {item["id"] for item in units}
    seen_checks: set[str] = set()
    actual_check_keys: set[tuple[str | None, str]] = set()
    for index, check in enumerate(checks, 1):
        errors.extend(validate_schema(check, "database_deep_map_check.schema.json", f"{CHECK_FILE}:{index}"))
        if check["id"] in seen_checks:
            errors.append(f"duplicate check id {check['id']}")
        seen_checks.add(check["id"])
        key = (check["unit_id"], check["facet_id"])
        if key in actual_check_keys:
            errors.append(f"duplicate route-contract check {key}")
        actual_check_keys.add(key)
        errors.extend(check_errors(check, project, unit_ids, route_ids))
    expected_specs = expected_check_specs(project, units) if not plan_audit["errors"] else []
    expected_check_map = {(item["unit_id"], item["id"]): item for item in expected_specs}
    expected_check_keys = {(item["unit_id"], item["id"]) for item in expected_specs}
    for key in sorted(expected_check_keys - actual_check_keys, key=str):
        errors.append(f"missing required route-contract check {key}")
    for key in sorted(actual_check_keys - expected_check_keys, key=str):
        errors.append(f"unexpected route-contract check {key}")
    unit_by_id = {item["id"]: item for item in units}
    for check in checks:
        key = (check["unit_id"], check["facet_id"])
        expected_check = expected_check_map.get(key)
        if expected_check is None:
            continue
        for field in ("scope", "stage", "requirement", "route_modules"):
            if check[field] != expected_check[field]:
                errors.append(f"{check['id']}: {field} differs from the active route contract")
        if check["unit_id"] is not None and check["state"] in CHECK_CLOSED_STATES:
            stage_state = unit_gate_state(unit_by_id[check["unit_id"]], check["stage"])
            if stage_state not in MAPPED_STATES:
                errors.append(f"{check['id']}: cannot close before its {check['stage']} stage is mapped")
    expected_units = project["scope"]["expected_work_unit_count"]
    if expected_units is not None and expected_units != len(units):
        errors.append(f"project expected_work_unit_count={expected_units} but units={len(units)}")
    if project["phase_states"]["inventory"]["state"] in MAPPED_STATES and expected_units is None:
        errors.append("inventory cannot be complete while expected_work_unit_count is unknown")
    if project["source_id"] not in known_ids:
        errors.append(f"unknown source_id {project['source_id']}")
    expected_locks = build_locks(project, units, project.get("locks", {}).get("locked_at", project["created_at"]))
    for lock_name in ("plan_fingerprint", "scope_fingerprint", "unit_manifest_fingerprint"):
        if project.get("locks", {}).get(lock_name) != expected_locks[lock_name]:
            errors.append(f"execution lock mismatch: {lock_name}; regenerate and re-audit through the upgrade command")
    for name, value in project["phase_states"].items():
        errors.extend(phase_errors(project, name, value))

    required_entries = [(unit, stage) for unit in units for stage in unit["required_stages"]]
    total = len(required_entries)
    closed = sum(unit["stages"][stage]["state"] in CLOSED_STATES for unit, stage in required_entries)
    mapped = sum(unit["stages"][stage]["state"] in MAPPED_STATES for unit, stage in required_entries)
    blocked = sum(unit["stages"][stage]["state"] == "blocked" for unit, stage in required_entries)
    stage_summary = {}
    for name in UNIT_STAGES:
        records = [unit["stages"][name] for unit in units if name in unit["required_stages"]]
        stage_summary[name] = {
            "required_units": len(records),
            "mapped_units": sum(item["state"] in MAPPED_STATES for item in records),
            "verified_or_not_applicable_units": sum(item["state"] in CLOSED_STATES for item in records),
            "blocked_units": sum(item["state"] == "blocked" for item in records),
            "state_counts": {state: sum(item["state"] == state for item in records) for state in sorted({item["state"] for item in records})},
        }
    fully_mapped_units = sum(
        all(unit["stages"][name]["state"] in MAPPED_STATES for name in unit["required_stages"])
        and all(unit["spines"][name]["state"] in MAPPED_STATES for name in SPINES)
        for unit in units
    )
    fully_closed_units = sum(
        all(unit["stages"][name]["state"] in CLOSED_STATES for name in unit["required_stages"])
        and all(unit["spines"][name]["state"] in CLOSED_STATES for name in SPINES)
        for unit in units
    )
    required_spines = [(unit, name) for unit in units for name in SPINES]
    mapped_spines = sum(unit["spines"][name]["state"] in MAPPED_STATES for unit, name in required_spines)
    closed_spines = sum(unit["spines"][name]["state"] in CLOSED_STATES for unit, name in required_spines)
    blocked_spines = sum(unit["spines"][name]["state"] == "blocked" for unit, name in required_spines)
    spine_summary = {
        name: {
            "required_units": len(units),
            "mapped_units": sum(unit["spines"][name]["state"] in MAPPED_STATES for unit in units),
            "verified_or_not_applicable_units": sum(unit["spines"][name]["state"] in CLOSED_STATES for unit in units),
            "blocked_units": sum(unit["spines"][name]["state"] == "blocked" for unit in units),
        }
        for name in SPINES
    }
    required_checks = [item for item in checks if item["required"]]
    closed_checks = sum(item["state"] in CHECK_CLOSED_STATES for item in required_checks)
    blocked_checks = sum(item["state"] == "blocked" for item in required_checks)
    failed_checks = sum(item["state"] == "failed" for item in required_checks)
    human_checks = sum(item["state"] == "needs_human_review" for item in required_checks)
    core_phases_closed = all(project["phase_states"][name]["state"] in CLOSED_STATES for name in EARLY_PHASES)
    unresolved_gates = [
        item for item in project["diagnostic_plan"]["human_gates"]
        if item["status"] in {"pending", "rejected"}
    ]
    plan_ready = project["diagnostic_plan"]["plan_status"] == "ready" and not project["diagnostic_plan"]["unresolved_critical"]
    execution_ready_for_storage = (
        not errors and plan_ready and not unresolved_gates
        and core_phases_closed and total > 0 and closed == total and blocked == 0
        and required_spines and closed_spines == len(required_spines) and blocked_spines == 0
        and required_checks and closed_checks == len(required_checks)
        and blocked_checks == failed_checks == human_checks == 0
    )
    canonical_archive_complete = archive_receipt_is_valid(target, project)
    try:
        from database_storage import storage_receipt_is_valid
        storage_complete = storage_receipt_is_valid(target, project)
    except (ImportError, RuntimeError, ValueError, OSError):
        storage_complete = False
    completion_ready = execution_ready_for_storage and canonical_archive_complete and storage_complete
    if project["workflow_status"] == "complete" and not completion_ready:
        errors.append("project is marked complete but the strict Plan → Execute → Storage contract is not satisfied")
    if mapped == total and closed < total:
        warnings.append("All required unit stages are mapped, but one or more still lack full verification.")
    if expected_units is None:
        warnings.append("The work-unit universe is not fixed; no percentage can represent bounded completeness.")
    if project["diagnostic_plan"]["plan_status"] == "needs_evidence":
        warnings.append("Diagnostic plan retains critical unresolved dimensions; classification or boundary work must continue.")
    if unresolved_gates:
        warnings.append("Diagnostic plan retains human gates; protected operations and final completion remain unavailable.")
    queue = [] if errors or project["workflow_status"] in {"ready_for_storage", "complete"} else action_queue(project, units, checks)
    if queue:
        effective_next_actions = [queue[0]["command"]]
    elif project["workflow_status"] == "complete":
        effective_next_actions = ["database-storage-status"]
    elif canonical_archive_complete and execution_ready_for_storage:
        effective_next_actions = ["prepare-database-storage"]
    elif (target / ARCHIVE_PACKAGE_FILE).is_file() and execution_ready_for_storage:
        effective_next_actions = ["archive-database-deep-map"]
    elif execution_ready_for_storage:
        effective_next_actions = ["prepare-database-deep-map-storage"]
    else:
        effective_next_actions = project["next_actions"]
    return {
        "operation": "audit_database_deep_map", "project_id": project["id"], "project_dir": str(target), "title": project["title"],
        "source_id": project["source_id"], "workflow_status": project["workflow_status"],
        "current_phase": project["current_phase"], "scope": project["scope"],
        "execution_contract": project["execution_contract"], "execution_locks": project["locks"],
        "pipeline_contract": project["pipeline_contract"],
        "staging": {
            "state": manifest["state"],
            "record_count": len(manifest["records"]),
            "manifest_fingerprint": staging_manifest_fingerprint(manifest),
            "archive_package_present": (target / ARCHIVE_PACKAGE_FILE).is_file(),
            "archive_receipt_present": (target / ARCHIVE_RECEIPT_FILE).is_file(),
            "storage_receipt_present": (target / "storage_receipt.json").is_file(),
        },
        "database_profile": project["database_profile"],
        "diagnostic_plan": {
            "plan_status": project["diagnostic_plan"]["plan_status"],
            "route_contract_version": project["diagnostic_plan"]["route_contract_version"],
            "selected_route_modules": project["diagnostic_plan"]["selected_route_modules"],
            "unresolved_critical": project["diagnostic_plan"]["unresolved_critical"],
            "human_gates": project["diagnostic_plan"]["human_gates"],
            "risk_flags": project["diagnostic_plan"]["risk_flags"],
        },
        "progress": {
            "work_units": len(units), "expected_work_units": expected_units,
            "fully_mapped_work_units": fully_mapped_units, "fully_closed_work_units": fully_closed_units,
            "required_unit_stages": total, "mapped_unit_stages": mapped, "closed_unit_stages": closed,
            "blocked_unit_stages": blocked,
            "mapping_percentage": round((mapped / total) * 100, 2) if total else 0.0,
            "strict_completion_percentage": round((closed / total) * 100, 2) if total else 0.0,
            "required_contract_checks": len(required_checks), "closed_contract_checks": closed_checks,
            "blocked_contract_checks": blocked_checks, "failed_contract_checks": failed_checks,
            "human_review_contract_checks": human_checks,
            "contract_check_percentage": round((closed_checks / len(required_checks)) * 100, 2) if required_checks else 0.0,
            "required_spines": len(required_spines), "mapped_spines": mapped_spines,
            "closed_spines": closed_spines, "blocked_spines": blocked_spines,
            "dual_spine_percentage": round((closed_spines / len(required_spines)) * 100, 2) if required_spines else 0.0,
        },
        "stage_summary": stage_summary, "spine_summary": spine_summary,
        "phase_states": project["phase_states"],
        "execution_ready_for_storage": execution_ready_for_storage,
        "execution_ready_for_archive": execution_ready_for_storage,
        "canonical_archive_complete": canonical_archive_complete,
        "archive_complete": canonical_archive_complete,
        "storage_complete": storage_complete,
        "completion_ready": completion_ready,
        "errors": errors, "warnings": warnings, "next_target": queue[0] if queue else None,
        "queue_preview": queue[:10], "next_actions": effective_next_actions,
        "report_path": str(target / REPORT_FILE),
    }


def validate_update(value: dict[str, Any], schema_name: str, label: str) -> None:
    errors = validate_schema(value, schema_name, label)
    if errors:
        raise ValueError("; ".join(errors))


def build_unit(spec: dict[str, Any], project: dict[str, Any], timestamp: str, records: dict[str, dict[str, Any]], sequence: int) -> dict[str, Any]:
    upstream_id = str(spec["upstream_id"])
    unit_id = f"grdr:deep-map-unit:{project['id'].rsplit(':', 1)[-1]}-{slug(upstream_id)}"
    stages = {name: empty_stage(timestamp) for name in UNIT_STAGES}
    dataset_id = spec.get("dataset_id")
    if dataset_id:
        if dataset_id not in records:
            raise ValueError(f"unit {upstream_id}: unknown dataset_id {dataset_id}")
        dataset = records[dataset_id]
        verified = dataset.get("verification", {}).get("status") == "verified"
        stages["dataset"] = {
            "state": "verified_complete" if verified else "mapped_complete",
            "expected_count": 1, "registered_ids": [dataset_id], "verified_count": 1 if verified else 0,
            "completion_basis": "One canonical Dataset record resolves this upstream work unit.",
            "evidence": evidence_from(dataset), "blockers": [],
            "notes": "Dataset identity is registered; verification state follows the canonical record.", "updated_at": timestamp,
        }
    dimensions = project["diagnostic_plan"]["diagnostic_dimensions"]
    routes = list(dict.fromkeys(["core_metadata", *(spec.get("route_modules") or project["database_profile"]["route_modules"])]))
    return {
        "schema_version": "2.0.0", "id": unit_id, "project_id": project["id"], "sequence": spec.get("sequence", sequence),
        "upstream_id": upstream_id, "label": spec["label"], "dataset_id": dataset_id,
        "unit_type": spec.get("unit_type") or project["diagnostic_plan"]["work_unit_strategy"]["unit_types"][0],
        "disciplines": spec.get("disciplines") or project["database_profile"]["disciplines"],
        "origin_type": spec.get("origin_type") or project["database_profile"]["origin_type"],
        "structural_archetypes": spec.get("structural_archetypes") or project["database_profile"]["structural_archetypes"],
        "content_modalities": spec.get("content_modalities") or dimensions["content_modalities"],
        "lifecycle_modes": spec.get("lifecycle_modes") or dimensions["lifecycle_modes"],
        "versioning_model": spec.get("versioning_model") or dimensions["versioning_models"][0],
        "sensitivity_classes": spec.get("sensitivity_classes") or dimensions["sensitivity_classes"],
        "route_modules": routes,
        "required_stages": spec.get("required_stages") or UNIT_STAGES,
        "stages": stages,
        "spines": {name: empty_spine(timestamp) for name in SPINES},
        "created_at": timestamp, "updated_at": timestamp,
    }


def start_database_deep_map(spec_file: str | Path, project_dir: str | Path | None = None) -> dict[str, Any]:
    spec = read_json(Path(spec_file).expanduser().resolve())
    for field in ("source_id", "title", "database_profile", "scope", "units"):
        if field not in spec:
            raise ValueError(f"start specification requires {field}")
    required_record_ids = {
        spec["source_id"],
        *(
            item["dataset_id"]
            for item in spec["units"]
            if item.get("dataset_id")
        ),
    }
    records = registry_index_for_ids(required_record_ids)
    source = records.get(spec["source_id"])
    if source is None or not spec["source_id"].startswith("grdr:source:"):
        raise ValueError(f"unknown canonical source_id {spec['source_id']}")
    project_slug = slug(spec.get("project_slug") or spec["source_id"].rsplit(":", 1)[-1])
    target = Path(project_dir).expanduser().resolve() if project_dir else (PROJECT_ROOT / project_slug).resolve()
    if target.exists():
        raise ValueError(f"database deep-map project already exists: {target}")
    timestamp = now()
    project_id = f"grdr:deep-map-project:{project_slug}"
    source_evidence = evidence_from(source)
    boundary_evidence = spec.get("boundary_evidence", [])
    if "diagnostic_plan" in spec:
        diagnostic_plan = spec["diagnostic_plan"]
    elif "diagnostic_intake" in spec:
        diagnostic_plan = build_database_deep_map_plan_from_intake(spec["diagnostic_intake"])
    else:
        raise ValueError("start specification requires diagnostic_intake or diagnostic_plan")
    plan_audit = audit_database_deep_map_plan(diagnostic_plan)
    if plan_audit["errors"]:
        raise ValueError("diagnostic plan failed audit: " + "; ".join(plan_audit["errors"]))
    if diagnostic_plan["source"].get("source_id") not in {None, spec["source_id"]}:
        raise ValueError("diagnostic plan source_id does not match start specification")
    if diagnostic_plan["plan_status"] not in {"ready", "ready_with_gates"}:
        details = "; ".join(diagnostic_plan["unresolved_critical"]) or diagnostic_plan["plan_status"]
        raise ValueError(f"diagnostic plan is not executable; resolve the preflight diagnosis first: {details}")
    if spec["scope"]["mode"] != diagnostic_plan["goal"]["scope_mode"]:
        raise ValueError("start scope mode does not match the diagnostic plan")
    if spec["scope"]["boundary_type"] != diagnostic_plan["scope"]["boundary_type"]:
        raise ValueError("start boundary type does not match the diagnostic plan")
    plan_expected = diagnostic_plan["work_unit_strategy"]["expected_count"]
    if plan_expected is not None and spec["scope"]["expected_work_unit_count"] != plan_expected:
        raise ValueError("start expected work-unit count does not match the diagnostic plan")
    project = {
        "schema_version": "4.2.0", "id": project_id, "source_id": spec["source_id"], "title": spec["title"],
        "database_profile": {**spec["database_profile"], "route_modules": diagnostic_plan["selected_route_modules"]},
        "diagnostic_plan": diagnostic_plan, "scope": spec["scope"],
        "pipeline_contract": pipeline_contract(),
        "execution_contract": execution_contract(),
        "phase_states": {
            "identity": phase_state("verified_complete" if source["verification"]["status"] == "verified" else "mapped_complete", timestamp, "Canonical GRDR Source identity and official evidence are registered.", source_evidence),
            "classification": phase_state("in_progress" if diagnostic_plan["unresolved_critical"] else "mapped_complete", timestamp, None if diagnostic_plan["unresolved_critical"] else "Open-world diagnostic dimensions, route contracts, risk flags, and human gates were generated and audited.", [] if diagnostic_plan["unresolved_critical"] else (diagnostic_plan["evidence"] or source_evidence)),
            "boundary": phase_state("mapped_complete", timestamp, spec["scope"]["boundary_statement"], boundary_evidence),
            "inventory": phase_state("in_progress", timestamp),
            "deep_mapping": phase_state("in_progress", timestamp),
            "validation": phase_state("not_started", timestamp),
            "completion_audit": phase_state("not_started", timestamp),
        },
        "workflow_status": "in_progress", "current_phase": "inventory",
        "next_actions": ["database-deep-map-status", "resume-database-deep-map"],
        "history": [{"timestamp": timestamp, "operation": "start-database-deep-map", "summary": "Created persistent database deep-map project and initial work-unit ledger."}],
        "created_at": timestamp, "updated_at": timestamp,
    }
    units = [build_unit(item, project, timestamp, records, index) for index, item in enumerate(spec["units"], 1)]
    project["locks"] = build_locks(project, units, timestamp)
    checks = materialize_checks(project, units, timestamp)
    expected = project["scope"]["expected_work_unit_count"]
    if expected is not None and expected == len(units) and boundary_evidence:
        project["phase_states"]["inventory"] = phase_state("mapped_complete", timestamp, f"The bounded inventory contains {len(units)} work units, matching the declared expected count.", boundary_evidence)
        project["current_phase"] = "deep_mapping"
    target.mkdir(parents=True)
    write_json(target / PROJECT_FILE, project); write_jsonl(target / UNIT_FILE, units); write_jsonl(target / CHECK_FILE, checks)
    write_json(target / STAGING_MANIFEST_FILE, empty_staging_manifest(project, timestamp))
    audit = audit_database_deep_map(target)
    if audit["errors"]:
        raise ValueError("created project failed audit: " + "; ".join(audit["errors"]))
    sync_report(target, project, audit)
    return {"operation": "start_database_deep_map", "project_id": project_id, "project_dir": str(target), "work_units": len(units), "audit": audit}


def infer_content_modalities(archetypes: list[str]) -> list[str]:
    mapping = {
        "statistical_cube": "multidimensional", "relational_database": "tabular",
        "flat_table_collection": "tabular", "json_or_xml_api": "tabular",
        "survey_microdata": "tabular", "questionnaire_or_instrument": "document",
        "administrative_event_system": "event", "geospatial_vector": "geospatial_vector",
        "geospatial_raster": "geospatial_raster", "scientific_array": "multidimensional",
        "sensor_time_series": "time_series", "biological_sequence_or_structure": "sequence",
        "knowledge_graph": "graph", "document_corpus": "text",
        "image_audio_video_collection": "composite",
    }
    result = list(dict.fromkeys(mapping[item] for item in archetypes if item in mapping))
    return result or ["composite"]


def normalize_pipeline_workflow(project: dict[str, Any]) -> None:
    if project.get("workflow_status") in {"ready_for_completion", "ready_for_archive", "complete"}:
        if project.get("workflow_status") == "complete" and not project.get("next_actions") == ["database-storage-status"]:
            project["phase_states"]["completion_audit"] = phase_state("in_progress", now())
        project["workflow_status"] = "ready_for_storage"
        project["current_phase"] = "storage"
        project["next_actions"] = ["prepare-database-storage", "database-storage-status"]


def upgrade_database_deep_map(project_dir: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    for name in (PROJECT_FILE, UNIT_FILE):
        if not (target / name).is_file():
            raise ValueError(f"cannot upgrade incomplete project; missing {name}")
    project = read_json(target / PROJECT_FILE)
    units = read_jsonl(target / UNIT_FILE)
    contracts = load_contracts()
    current_contract_version = contracts["contract_version"]
    if (
        project.get("schema_version") == "2.0.0"
        and project.get("diagnostic_plan", {}).get("route_contract_version") == current_contract_version
        and (target / CHECK_FILE).is_file()
    ):
        original_project = json.loads(json.dumps(project))
        timestamp = now()
        project["schema_version"] = "4.2.0"
        project["pipeline_contract"] = pipeline_contract()
        project["execution_contract"] = execution_contract()
        normalize_pipeline_workflow(project)
        append_history(project, "upgrade-database-deep-map", "Fixed the database factory as locked Plan, staged Execute, and versioned Storage steps.")
        write_json(target / PROJECT_FILE, project)
        write_json(target / STAGING_MANIFEST_FILE, empty_staging_manifest(project, timestamp))
        audit = audit_database_deep_map(target)
        if audit["errors"]:
            write_json(target / PROJECT_FILE, original_project)
            (target / STAGING_MANIFEST_FILE).unlink(missing_ok=True)
            raise ValueError("three-step pipeline upgrade failed audit: " + "; ".join(audit["errors"]))
        sync_report(target, project, audit)
        return {"operation": "upgrade_database_deep_map", "status": "upgraded_to_three_step_pipeline", "audit": audit}
    if (
        project.get("schema_version") in {"3.0.0", "3.2.0", "4.0.0", "4.1.0", "4.2.0"}
        and project.get("diagnostic_plan", {}).get("route_contract_version") == current_contract_version
        and (target / CHECK_FILE).is_file()
    ):
        if project.get("schema_version") != "4.2.0" or project.get("pipeline_contract") != pipeline_contract():
            project["schema_version"] = "4.2.0"
            project["pipeline_contract"] = pipeline_contract()
            project["execution_contract"] = execution_contract()
            normalize_pipeline_workflow(project)
            append_history(project, "upgrade-database-deep-map", "Replaced the Archive-only third step with the complete Storage contract.")
            write_json(target / PROJECT_FILE, project)
        if not (target / STAGING_MANIFEST_FILE).is_file():
            write_json(target / STAGING_MANIFEST_FILE, empty_staging_manifest(project, now()))
        checks = read_jsonl(target / CHECK_FILE)
        original_checks = json.loads(json.dumps(checks))
        original_project = json.loads(json.dumps(project))
        timestamp = now()
        synchronized = synchronize_blocked_stage_checks(units, checks, timestamp)
        if synchronized:
            write_jsonl(target / CHECK_FILE, checks)
            append_history(project, "reconcile-database-deep-map-blockers", f"Propagated {synchronized} blocked stage obligations into route checks.")
            write_json(target / PROJECT_FILE, project)
            audit = audit_database_deep_map(target)
            if audit["errors"]:
                write_jsonl(target / CHECK_FILE, original_checks)
                write_json(target / PROJECT_FILE, original_project)
                raise ValueError("current-project blocker reconciliation failed audit: " + "; ".join(audit["errors"]))
            sync_report(target, project, audit)
            return {"operation": "upgrade_database_deep_map", "status": "reconciled", "synchronized_checks": synchronized, "audit": audit}
        return {"operation": "upgrade_database_deep_map", "status": "already_current", "audit": audit_database_deep_map(target)}
    if project.get("schema_version") in {"1.1.0", "2.0.0"} and (target / CHECK_FILE).is_file():
        original_project = json.loads(json.dumps(project))
        original_units = json.loads(json.dumps(units))
        old_checks = read_jsonl(target / CHECK_FILE)
        original_checks = json.loads(json.dumps(old_checks))
        timestamp = now()
        selected = list(dict.fromkeys(["core_metadata", *project["diagnostic_plan"]["selected_route_modules"]]))
        routes = contract_index(contracts)
        unknown_routes = [item for item in selected if item not in routes]
        if unknown_routes:
            raise ValueError("cannot upgrade; project references removed route modules: " + ", ".join(unknown_routes))
        project["diagnostic_plan"]["route_contract_version"] = current_contract_version
        project["diagnostic_plan"]["selected_route_modules"] = selected
        project["diagnostic_plan"]["required_facets"] = merge_facets(selected, routes)
        project["diagnostic_plan"]["generated_at"] = timestamp
        project["database_profile"]["route_modules"] = selected
        project["schema_version"] = "4.2.0"
        project["pipeline_contract"] = pipeline_contract()
        project["execution_contract"] = execution_contract()
        normalize_pipeline_workflow(project)
        for unit in units:
            unit["schema_version"] = "2.0.0"
            unit["route_modules"] = list(dict.fromkeys(["core_metadata", *unit["route_modules"]]))
            unit.setdefault("spines", {name: empty_spine(timestamp) for name in SPINES})
            for name in SPINES:
                unit["spines"].setdefault(name, empty_spine(timestamp))
            unit["updated_at"] = timestamp
        checks = materialize_checks(project, units, timestamp)
        old_by_key = {(item["unit_id"], item["facet_id"]): item for item in old_checks}
        for check in checks:
            old = old_by_key.get((check["unit_id"], check["facet_id"]))
            if old and old["stage"] == check["stage"] and old["requirement"] == check["requirement"]:
                for key in ("state", "completion_basis", "evidence", "blockers", "notes", "created_at"):
                    check[key] = old[key]
                check["updated_at"] = timestamp
        synchronize_blocked_stage_checks(units, checks, timestamp)
        project["locks"] = build_locks(project, units, timestamp)
        append_history(project, "upgrade-database-deep-map", "Upgraded to the locked dual-spine execution contract and current route checks.")
        write_json(target / PROJECT_FILE, project); write_jsonl(target / UNIT_FILE, units); write_jsonl(target / CHECK_FILE, checks)
        write_json(target / STAGING_MANIFEST_FILE, empty_staging_manifest(project, timestamp))
        audit = audit_database_deep_map(target)
        if audit["errors"]:
            write_json(target / PROJECT_FILE, original_project); write_jsonl(target / UNIT_FILE, original_units); write_jsonl(target / CHECK_FILE, original_checks)
            raise ValueError("dual-spine upgrade failed audit: " + "; ".join(audit["errors"]))
        sync_report(target, project, audit)
        return {"operation": "upgrade_database_deep_map", "status": "upgraded_to_dual_spine", "check_count": len(checks), "audit": audit}
    original_project = json.loads(json.dumps(project))
    original_units = json.loads(json.dumps(units))
    records = registry_index_for_ids({project["source_id"]}, target)
    source = records.get(project["source_id"])
    if source is None:
        raise ValueError(f"cannot upgrade; unknown source {project['source_id']}")
    scope_mode = project["scope"]["mode"]
    claim_map = {
        "representative_chain": "representative_only", "question_driven": "question_fit",
        "priority_catalog": "bounded_partition", "catalog_level": "catalog_only",
        "exhaustive_snapshot": "exhaustive_snapshot", "rolling_window": "rolling_current",
        "bounded_partition": "bounded_partition",
    }
    profile = project["database_profile"]
    plan_evidence = project["phase_states"]["classification"]["evidence"] or evidence_from(source)
    intake = {
        "schema_version": "1.0.0",
        "source": {"source_id": project["source_id"], "name": source["name"], "url": source["canonical_url"]},
        "goal": {"scope_mode": scope_mode, "completion_claim": claim_map[scope_mode], "research_question": None},
        "observations": {
            "disciplines": profile["disciplines"], "origin_types": [profile["origin_type"]],
            "provenance_roles": [profile["provenance_role"]], "production_modes": profile["production_modes"],
            "structural_archetypes": profile["structural_archetypes"],
            "content_modalities": infer_content_modalities(profile["structural_archetypes"]),
            "lifecycle_modes": ["versioned_release"], "versioning_models": ["dated_release"],
            "access_regimes": [profile["access_regime"]], "sensitivity_classes": ["public"],
            "scale_classes": ["large" if len(units) > 20 else "medium"],
            "metadata_maturity": "machine_readable" if "api_schema" in profile["route_modules"] or "sdmx_cube" in profile["route_modules"] else "human_documented",
            "languages": ["en"],
        },
        "scope": {"boundary_type": project["scope"]["boundary_type"], "boundary_statement": project["scope"]["boundary_statement"], "snapshot_at": project["scope"]["snapshot_at"]},
        "work_unit_strategy": {
            "unit_types": ["dataset"], "identity_rule": "Preserve the bounded upstream dataset or collection identifier.",
            "partition_rule": "One bounded upstream dataset or equivalent collection per work unit.",
            "ordering_rule": project["scope"]["enumeration_method"],
            "denominator_strategy": "explicit_count" if project["scope"]["expected_work_unit_count"] is not None else "unknown",
            "expected_count": project["scope"]["expected_work_unit_count"],
        },
        "constraints": {"authorized_access": ["public_metadata"], "prohibited_actions": [], "compute_limit": None, "notes": "Migrated from GRDR deep-map schema 1.0.0."},
        "explicit_route_modules": [item for item in profile["route_modules"] if item != "other"],
        "evidence": plan_evidence,
    }
    diagnostic_plan = build_database_deep_map_plan_from_intake(intake)
    project["schema_version"] = "4.2.0"
    project["diagnostic_plan"] = diagnostic_plan
    project["database_profile"]["route_modules"] = diagnostic_plan["selected_route_modules"]
    project["pipeline_contract"] = pipeline_contract()
    project["execution_contract"] = execution_contract()
    normalize_pipeline_workflow(project)
    timestamp = now()
    for unit in units:
        unit["schema_version"] = "2.0.0"
        unit["unit_type"] = "dataset"
        unit["content_modalities"] = infer_content_modalities(unit["structural_archetypes"])
        unit["lifecycle_modes"] = ["versioned_release"]
        unit["versioning_model"] = "dated_release"
        unit["sensitivity_classes"] = ["public"]
        unit["route_modules"] = list(dict.fromkeys(["core_metadata", *unit["route_modules"]]))
        unit["spines"] = {name: empty_spine(timestamp) for name in SPINES}
        unit["updated_at"] = timestamp
    checks = materialize_checks(project, units, timestamp)
    synchronize_blocked_stage_checks(units, checks, timestamp)
    boundary_evidence = project["phase_states"]["boundary"]["evidence"] or evidence_from(source)
    for check in checks:
        if check["facet_id"] == "core.boundary_denominator" and project["phase_states"]["boundary"]["state"] == "verified_complete" and project["phase_states"]["inventory"]["state"] == "verified_complete":
            check.update({"state": "passed", "completion_basis": "The dated boundary and work-unit denominator were verified before migration.", "evidence": boundary_evidence, "updated_at": timestamp})
    project["locks"] = build_locks(project, units, timestamp)
    write_json(target / PROJECT_FILE, project); write_jsonl(target / UNIT_FILE, units); write_jsonl(target / CHECK_FILE, checks)
    write_json(target / STAGING_MANIFEST_FILE, empty_staging_manifest(project, timestamp))
    audit = audit_database_deep_map(target)
    if audit["errors"]:
        write_json(target / PROJECT_FILE, original_project); write_jsonl(target / UNIT_FILE, original_units)
        (target / CHECK_FILE).unlink(missing_ok=True)
        raise ValueError("upgraded project failed audit: " + "; ".join(audit["errors"]))
    append_history(project, "upgrade-database-deep-map", "Upgraded to open-world diagnostic plan and route-contract checks.")
    write_json(target / PROJECT_FILE, project)
    audit = audit_database_deep_map(target); sync_report(target, project, audit)
    return {"operation": "upgrade_database_deep_map", "status": "upgraded", "check_count": len(checks), "audit": audit}


def record_database_deep_map_phase(project_dir: str | Path, update_file: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir); require_project(target)
    update = read_json(Path(update_file).expanduser().resolve())
    validate_update(update, "database_deep_map_phase_update.schema.json", "phase_update")
    if update["state"] in {"mapped_complete", "verified_complete", "not_applicable"} and (not update["completion_basis"] or not update["evidence"]):
        raise ValueError("complete or not-applicable phase update requires completion_basis and evidence")
    if update["state"] == "blocked" and not update["blockers"]:
        raise ValueError("blocked phase update requires blockers")
    project = read_json(target / PROJECT_FILE); original_project = json.loads(json.dumps(project)); timestamp = now()
    project["phase_states"][update["phase"]] = {**{key: update[key] for key in ("state", "completion_basis", "evidence", "blockers")}, "updated_at": timestamp}
    project["workflow_status"] = "blocked" if update["state"] == "blocked" else "in_progress"
    project["current_phase"] = update["phase"]
    project["next_actions"] = ["resume-database-deep-map"]
    append_history(project, "record-database-deep-map-phase", f"Set {update['phase']} to {update['state']}.")
    write_json(target / PROJECT_FILE, project)
    audit = audit_database_deep_map(target)
    if audit["errors"]:
        write_json(target / PROJECT_FILE, original_project)
        raise ValueError("phase update failed audit: " + "; ".join(audit["errors"]))
    sync_report(target, project, audit)
    return {"operation": "record_database_deep_map_phase", "phase": update["phase"], "state": update["state"], "audit": audit}


def record_database_deep_map_stage(project_dir: str | Path, update_file: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir); require_project(target)
    update = read_json(Path(update_file).expanduser().resolve())
    validate_update(update, "database_deep_map_stage_update.schema.json", "stage_update")
    units = read_jsonl(target / UNIT_FILE); original_units = json.loads(json.dumps(units)); by_id = {item["id"]: item for item in units}
    checks = read_jsonl(target / CHECK_FILE); original_checks = json.loads(json.dumps(checks))
    unit = by_id.get(update["unit_id"])
    if unit is None:
        raise ValueError(f"unknown unit_id {update['unit_id']}")
    timestamp = now()
    unit["stages"][update["stage"]] = {**{key: update[key] for key in ("state", "expected_count", "registered_ids", "verified_count", "completion_basis", "evidence", "blockers", "notes")}, "updated_at": timestamp}
    unit["updated_at"] = timestamp
    synchronize_blocked_stage_checks(units, checks, timestamp)
    write_jsonl(target / UNIT_FILE, units); write_jsonl(target / CHECK_FILE, checks)
    project = read_json(target / PROJECT_FILE); original_project = json.loads(json.dumps(project))
    project["workflow_status"] = "blocked" if update["state"] == "blocked" else "in_progress"
    project["current_phase"] = "deep_mapping"; project["next_actions"] = ["resume-database-deep-map"]
    append_history(project, "record-database-deep-map-stage", f"Set {unit['upstream_id']} / {update['stage']} to {update['state']}.")
    write_json(target / PROJECT_FILE, project)
    audit = audit_database_deep_map(target)
    if audit["errors"]:
        write_jsonl(target / UNIT_FILE, original_units)
        write_jsonl(target / CHECK_FILE, original_checks)
        write_json(target / PROJECT_FILE, original_project)
        raise ValueError("stage update failed audit: " + "; ".join(audit["errors"]))
    sync_report(target, project, audit)
    return {"operation": "record_database_deep_map_stage", "unit_id": unit["id"], "stage": update["stage"], "state": update["state"], "audit": audit}


def record_database_deep_map_spine(project_dir: str | Path, update_file: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir); require_project(target)
    update = read_json(Path(update_file).expanduser().resolve())
    validate_update(update, "database_deep_map_spine_update.schema.json", "spine_update")
    units = read_jsonl(target / UNIT_FILE); original_units = json.loads(json.dumps(units))
    checks = read_jsonl(target / CHECK_FILE); original_checks = json.loads(json.dumps(checks))
    unit = next((item for item in units if item["id"] == update["unit_id"]), None)
    if unit is None:
        raise ValueError(f"unknown unit_id {update['unit_id']}")
    requested_ids = set([*update["node_ids"], *update["edge_ids"]])
    records = registry_index_for_ids(requested_ids, target)
    unknown_ids = [item for item in [*update["node_ids"], *update["edge_ids"]] if item not in records]
    if unknown_ids:
        raise ValueError("spine update references unknown canonical IDs: " + ", ".join(sorted(unknown_ids)))
    timestamp = now()
    spine = {key: update[key] for key in (
        "state", "expected_node_count", "node_ids", "verified_node_count",
        "expected_edge_count", "edge_ids", "verified_edge_count", "root_node_ids",
        "leaf_node_ids", "topology_fingerprint", "completion_basis", "evidence", "blockers", "checkpoint",
    )}
    spine["topology_fingerprint_version"] = "topology-v2"
    spine["verified_node_count"] = sum(
        records[item].get("verification", {}).get("status") == "verified"
        for item in spine["node_ids"]
    )
    spine["verified_edge_count"] = sum(
        records[item].get("verification", {}).get("status") == "verified"
        for item in spine["edge_ids"]
    )
    if spine["checkpoint"]["enumeration_rule"] and spine["checkpoint"]["snapshot"]:
        spine["checkpoint"]["cursor_checksum"] = checkpoint_checksum(spine["checkpoint"])
    if spine["state"] in {"mapped_complete", "verified_complete"}:
        spine["topology_fingerprint"] = spine_topology_fingerprint(spine, records)
    spine["updated_at"] = timestamp
    unit["spines"][update["spine"]] = spine
    unit["updated_at"] = timestamp
    check_stage = next(key for key, value in SPINE_CHECK_STAGES.items() if value == update["spine"])
    if update["state"] == "blocked":
        for check in checks:
            if check["unit_id"] == unit["id"] and check["stage"] == check_stage and check["state"] in {"not_started", "in_progress"}:
                check.update({
                    "state": "blocked", "completion_basis": None, "evidence": [],
                    "blockers": route_blockers_from_stage(update["blockers"]),
                    "notes": f"Inherited from the blocked {update['spine']} spine.", "updated_at": timestamp,
                })
    write_jsonl(target / UNIT_FILE, units); write_jsonl(target / CHECK_FILE, checks)
    project = read_json(target / PROJECT_FILE); original_project = json.loads(json.dumps(project))
    project["workflow_status"] = "blocked" if update["state"] == "blocked" else "in_progress"
    project["current_phase"] = "deep_mapping"; project["next_actions"] = ["resume-database-deep-map"]
    append_history(project, "record-database-deep-map-spine", f"Set {unit['upstream_id']} / {update['spine']} spine to {update['state']}.")
    write_json(target / PROJECT_FILE, project)
    audit = audit_database_deep_map(target)
    if audit["errors"]:
        write_jsonl(target / UNIT_FILE, original_units); write_jsonl(target / CHECK_FILE, original_checks)
        write_json(target / PROJECT_FILE, original_project)
        raise ValueError("spine update failed audit: " + "; ".join(audit["errors"]))
    sync_report(target, project, audit)
    return {"operation": "record_database_deep_map_spine", "unit_id": unit["id"], "spine": update["spine"], "state": update["state"], "audit": audit}


def record_database_deep_map_check(project_dir: str | Path, update_file: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir); require_project(target)
    update = read_json(Path(update_file).expanduser().resolve())
    validate_update(update, "database_deep_map_check_update.schema.json", "check_update")
    if update["state"] in CHECK_CLOSED_STATES and (not update["completion_basis"] or not update["evidence"]):
        raise ValueError("passed or not-applicable check update requires completion_basis and evidence")
    if update["state"] in {"blocked", "failed", "needs_human_review"} and not update["blockers"]:
        raise ValueError(f"{update['state']} check update requires typed blockers")
    checks = read_jsonl(target / CHECK_FILE); original_checks = json.loads(json.dumps(checks))
    by_id = {item["id"]: item for item in checks}
    check = by_id.get(update["check_id"])
    if check is None:
        raise ValueError(f"unknown check_id {update['check_id']}")
    timestamp = now()
    for key in ("state", "completion_basis", "evidence", "blockers", "notes"):
        check[key] = update[key]
    check["updated_at"] = timestamp
    write_jsonl(target / CHECK_FILE, checks)
    project = read_json(target / PROJECT_FILE); original_project = json.loads(json.dumps(project))
    if update["state"] in {"blocked", "failed"}:
        project["workflow_status"] = "blocked"
    elif update["state"] == "needs_human_review":
        project["workflow_status"] = "needs_human_review"
    else:
        project["workflow_status"] = "in_progress"
    project["current_phase"] = "deep_mapping"
    project["next_actions"] = ["database-deep-map-status"]
    append_history(project, "record-database-deep-map-check", f"Set {check['facet_id']} to {update['state']}.")
    write_json(target / PROJECT_FILE, project)
    audit = audit_database_deep_map(target)
    if audit["errors"]:
        write_jsonl(target / CHECK_FILE, original_checks)
        write_json(target / PROJECT_FILE, original_project)
        raise ValueError("check update failed audit: " + "; ".join(audit["errors"]))
    sync_report(target, project, audit)
    return {"operation": "record_database_deep_map_check", "check_id": check["id"], "facet_id": check["facet_id"], "state": check["state"], "audit": audit}


def record_database_deep_map_human_gate(
    project_dir: str | Path,
    gate_id: str,
    decision: str,
    reviewer: str,
    notes: str,
) -> dict[str, Any]:
    if decision not in {"approved", "rejected", "not_applicable"}:
        raise ValueError("human-gate decision must be approved, rejected, or not_applicable")
    if not reviewer.strip() or not notes.strip():
        raise ValueError("human-gate decision requires reviewer and notes")
    target = resolve_project_dir(project_dir); require_project(target)
    project = read_json(target / PROJECT_FILE); original_project = json.loads(json.dumps(project))
    gate = next((item for item in project["diagnostic_plan"]["human_gates"] if item["gate"] == gate_id), None)
    if gate is None:
        raise ValueError(f"unknown human gate {gate_id}")
    timestamp = now()
    gate.update({"status": decision, "reviewer": reviewer, "decided_at": timestamp, "notes": notes})
    gates = project["diagnostic_plan"]["human_gates"]
    if any(item["status"] == "rejected" for item in gates):
        project["diagnostic_plan"]["plan_status"] = "blocked"
        project["workflow_status"] = "blocked"
    elif any(item["status"] == "pending" for item in gates):
        project["diagnostic_plan"]["plan_status"] = "ready_with_gates"
        project["workflow_status"] = "needs_human_review"
    elif project["diagnostic_plan"]["unresolved_critical"]:
        project["diagnostic_plan"]["plan_status"] = "needs_evidence"
        project["workflow_status"] = "in_progress"
    else:
        project["diagnostic_plan"]["plan_status"] = "ready"
        project["workflow_status"] = "in_progress"
    project["next_actions"] = ["database-deep-map-status"]
    append_history(project, "record-database-deep-map-human-gate", f"Human reviewer {reviewer} recorded {decision} for {gate_id}.")
    write_json(target / PROJECT_FILE, project)
    audit = audit_database_deep_map(target)
    if audit["errors"]:
        write_json(target / PROJECT_FILE, original_project)
        raise ValueError("human-gate update failed audit: " + "; ".join(audit["errors"]))
    sync_report(target, project, audit)
    return {"operation": "record_database_deep_map_human_gate", "gate": gate_id, "decision": decision, "reviewer": reviewer, "audit": audit}


def stage_database_deep_map_records(project_dir: str | Path, records_file: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir); require_project(target)
    project = read_json(target / PROJECT_FILE); original_project = json.loads(json.dumps(project))
    manifest = ensure_staging_manifest(target, project); original_manifest = json.loads(json.dumps(manifest))
    if manifest["state"] != "open" or (target / ARCHIVE_PACKAGE_FILE).exists():
        raise ValueError("execution staging is sealed; create a new bounded pass instead of changing an archive handoff")
    batch = read_record_batch(Path(records_file).expanduser().resolve())
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in batch:
        filename = registry_file_for_record(record)
        errors = validate_schema(record, REGISTRY_SCHEMAS[filename], f"staged_record:{record.get('id')}")
        if errors:
            raise ValueError("; ".join(errors))
        grouped.setdefault(filename, []).append(record)
    original_files: dict[str, list[dict[str, Any]] | None] = {}
    directory = target / STAGING_DIR
    canonical = registry_index_for_ids({record["id"] for record in batch})
    manifest_by_id = {item["id"]: item for item in manifest["records"]}
    timestamp = now()
    for filename, records in grouped.items():
        path = directory / filename
        current = read_jsonl(path) if path.is_file() else []
        original_files[filename] = json.loads(json.dumps(current)) if path.is_file() else None
        by_id = {item["id"]: item for item in current}
        order = [item["id"] for item in current]
        for record in records:
            record_id = record["id"]
            if record_id not in by_id:
                order.append(record_id)
            by_id[record_id] = record
            canonical_record = canonical.get(record_id)
            existing_manifest = manifest_by_id.get(record_id)
            base_fingerprint = (
                existing_manifest["base_fingerprint"]
                if existing_manifest is not None
                else fingerprint(canonical_record) if canonical_record is not None else None
            )
            action = (
                "create" if canonical_record is None
                else "unchanged" if canonical_record == record
                else "update"
            )
            manifest_by_id[record_id] = {
                "id": record_id,
                "registry_file": filename,
                "action": action,
                "base_fingerprint": base_fingerprint,
                "staged_fingerprint": fingerprint(record),
                "staged_at": timestamp,
            }
        write_jsonl(path, [by_id[record_id] for record_id in order])
    manifest["records"] = sorted(
        manifest_by_id.values(),
        key=lambda item: (REGISTRY_FILES.index(item["registry_file"]), item["id"]),
    )
    manifest["updated_at"] = timestamp
    write_json(target / STAGING_MANIFEST_FILE, manifest)
    project["workflow_status"] = "in_progress"; project["current_phase"] = "deep_mapping"
    project["next_actions"] = ["database-deep-map-status", "resume-database-deep-map"]
    append_history(project, "stage-database-deep-map-records", f"Staged {len(batch)} canonical candidate records for the Step 3 Storage transaction.")
    write_json(target / PROJECT_FILE, project)
    errors = staging_errors(target, project, manifest) + validate_merged_registry(target)
    if not errors:
        audit = audit_database_deep_map(target)
        errors.extend(audit["errors"])
    if errors:
        for filename, original in original_files.items():
            path = directory / filename
            if original is None:
                path.unlink(missing_ok=True)
            else:
                write_jsonl(path, original)
        write_json(target / STAGING_MANIFEST_FILE, original_manifest)
        write_json(target / PROJECT_FILE, original_project)
        raise ValueError("staged records failed validation: " + "; ".join(errors))
    sync_report(target, project, audit)
    return {
        "operation": "stage_database_deep_map_records",
        "project_id": project["id"],
        "staged_record_ids": [item["id"] for item in batch] if len(batch) <= 1000 else [],
        "staged_record_id_sample": (
            [item["id"] for item in batch]
            if len(batch) <= 40
            else [*[item["id"] for item in batch[:20]], *[item["id"] for item in batch[-20:]]]
        ),
        "staged_record_ids_fingerprint": fingerprint(sorted(item["id"] for item in batch)),
        "staging_record_count": len(manifest["records"]),
        "manifest_fingerprint": staging_manifest_fingerprint(manifest),
        "audit": audit,
    }


def record_database_deep_map_execution_batch(
    project_dir: str | Path,
    update_file: str | Path,
) -> dict[str, Any]:
    """Apply a complete Step 2 ledger transaction with one final audit.

    Large sources can contain thousands of canonical candidates and hundreds of
    route checks.  Re-auditing the same staged registry after every individual
    ledger mutation is needlessly quadratic.  This operation preserves the
    existing update schemas and all-or-nothing rollback semantics while
    committing phase, stage, spine, and check updates in one audited write.
    It never stages records and never writes the canonical registry.
    """

    target = resolve_project_dir(project_dir); require_project(target)
    payload = read_json(Path(update_file).expanduser().resolve())
    expected_keys = {"phases", "stages", "spines", "checks"}
    if set(payload) != expected_keys:
        raise ValueError(
            "execution batch must contain exactly: " + ", ".join(sorted(expected_keys))
        )
    if not all(isinstance(payload[key], list) for key in expected_keys):
        raise ValueError("execution batch sections must be arrays")
    for update in payload["phases"]:
        validate_update(update, "database_deep_map_phase_update.schema.json", "batch_phase_update")
    for update in payload["stages"]:
        validate_update(update, "database_deep_map_stage_update.schema.json", "batch_stage_update")
    for update in payload["spines"]:
        validate_update(update, "database_deep_map_spine_update.schema.json", "batch_spine_update")
    for update in payload["checks"]:
        validate_update(update, "database_deep_map_check_update.schema.json", "batch_check_update")

    def unique(values: list[tuple[Any, ...]], label: str) -> None:
        if len(values) != len(set(values)):
            raise ValueError(f"execution batch contains duplicate {label} targets")

    unique([(item["phase"],) for item in payload["phases"]], "phase")
    unique([(item["unit_id"], item["stage"]) for item in payload["stages"]], "stage")
    unique([(item["unit_id"], item["spine"]) for item in payload["spines"]], "spine")
    unique([(item["check_id"],) for item in payload["checks"]], "check")

    project = read_json(target / PROJECT_FILE)
    units = read_jsonl(target / UNIT_FILE)
    checks = read_jsonl(target / CHECK_FILE)
    original_project = json.loads(json.dumps(project))
    original_units = json.loads(json.dumps(units))
    original_checks = json.loads(json.dumps(checks))
    unit_by_id = {item["id"]: item for item in units}
    check_by_id = {item["id"]: item for item in checks}
    requested_ids = {
        record_id
        for update in payload["stages"]
        for record_id in update["registered_ids"]
    }
    requested_ids.update(
        record_id
        for update in payload["spines"]
        for record_id in [*update["node_ids"], *update["edge_ids"]]
    )
    records = registry_index_for_ids(requested_ids, target)
    known_ids = set(records)
    timestamp = now()

    try:
        for update in payload["phases"]:
            if update["state"] in {"mapped_complete", "verified_complete", "not_applicable"} and (
                not update["completion_basis"] or not update["evidence"]
            ):
                raise ValueError("complete or not-applicable phase update requires completion_basis and evidence")
            if update["state"] == "blocked" and not update["blockers"]:
                raise ValueError("blocked phase update requires blockers")
            project["phase_states"][update["phase"]] = {
                **{key: update[key] for key in ("state", "completion_basis", "evidence", "blockers")},
                "updated_at": timestamp,
            }

        for update in payload["stages"]:
            unit = unit_by_id.get(update["unit_id"])
            if unit is None:
                raise ValueError(f"unknown unit_id {update['unit_id']}")
            unknown_ids = sorted(set(update["registered_ids"]) - known_ids)
            if unknown_ids:
                raise ValueError("stage update references unknown canonical IDs: " + ", ".join(unknown_ids))
            unit["stages"][update["stage"]] = {
                **{key: update[key] for key in (
                    "state", "expected_count", "registered_ids", "verified_count",
                    "completion_basis", "evidence", "blockers", "notes",
                )},
                "updated_at": timestamp,
            }
            unit["updated_at"] = timestamp

        for update in payload["spines"]:
            unit = unit_by_id.get(update["unit_id"])
            if unit is None:
                raise ValueError(f"unknown unit_id {update['unit_id']}")
            unknown_ids = sorted(
                set([*update["node_ids"], *update["edge_ids"]]) - known_ids
            )
            if unknown_ids:
                raise ValueError("spine update references unknown canonical IDs: " + ", ".join(unknown_ids))
            spine = {key: update[key] for key in (
                "state", "expected_node_count", "node_ids", "verified_node_count",
                "expected_edge_count", "edge_ids", "verified_edge_count", "root_node_ids",
                "leaf_node_ids", "topology_fingerprint", "completion_basis", "evidence",
                "blockers", "checkpoint",
            )}
            spine["topology_fingerprint_version"] = "topology-v2"
            spine["verified_node_count"] = sum(
                records[item].get("verification", {}).get("status") == "verified"
                for item in spine["node_ids"]
            )
            spine["verified_edge_count"] = sum(
                records[item].get("verification", {}).get("status") == "verified"
                for item in spine["edge_ids"]
            )
            if spine["checkpoint"]["enumeration_rule"] and spine["checkpoint"]["snapshot"]:
                spine["checkpoint"]["cursor_checksum"] = checkpoint_checksum(spine["checkpoint"])
            if spine["state"] in {"mapped_complete", "verified_complete"}:
                spine["topology_fingerprint"] = spine_topology_fingerprint(spine, records)
            spine["updated_at"] = timestamp
            unit["spines"][update["spine"]] = spine
            unit["updated_at"] = timestamp

        for update in payload["checks"]:
            check = check_by_id.get(update["check_id"])
            if check is None:
                raise ValueError(f"unknown check_id {update['check_id']}")
            if update["state"] in CHECK_CLOSED_STATES and (
                not update["completion_basis"] or not update["evidence"]
            ):
                raise ValueError("passed or not-applicable check update requires completion_basis and evidence")
            if update["state"] in {"blocked", "failed", "needs_human_review"} and not update["blockers"]:
                raise ValueError(f"{update['state']} check update requires typed blockers")
            for key in ("state", "completion_basis", "evidence", "blockers", "notes"):
                check[key] = update[key]
            check["updated_at"] = timestamp

        synchronize_blocked_stage_checks(units, checks, timestamp)
        project["workflow_status"] = "in_progress"
        project["current_phase"] = "completion_audit"
        project["next_actions"] = ["audit-database-deep-map-execution"]
        append_history(
            project,
            "record-database-deep-map-execution-batch",
            "Applied one transactional Step 2 ledger batch after schema-validating every phase, stage, spine, and check update.",
        )
        write_json(target / PROJECT_FILE, project)
        write_jsonl(target / UNIT_FILE, units)
        write_jsonl(target / CHECK_FILE, checks)
        audit = audit_database_deep_map(target)
        if audit["errors"]:
            raise ValueError("execution batch failed audit: " + "; ".join(audit["errors"]))
    except Exception:
        write_json(target / PROJECT_FILE, original_project)
        write_jsonl(target / UNIT_FILE, original_units)
        write_jsonl(target / CHECK_FILE, original_checks)
        raise

    sync_report(target, project, audit)
    return {
        "operation": "record_database_deep_map_execution_batch",
        "project_id": project["id"],
        "phase_update_count": len(payload["phases"]),
        "stage_update_count": len(payload["stages"]),
        "spine_update_count": len(payload["spines"]),
        "check_update_count": len(payload["checks"]),
        "execution_ready_for_storage": audit["execution_ready_for_storage"],
        "execution_ready_for_archive": audit["execution_ready_for_archive"],
        "audit": audit,
    }


def action_queue(project: dict[str, Any], units: list[dict[str, Any]], checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = []
    pending_gates = [item for item in project["diagnostic_plan"]["human_gates"] if item["status"] == "pending"]
    protected_observation_access = any(item["required_before"] == "observation_access" for item in pending_gates)
    gate_priorities = {"metadata_access": 1, "local_storage": 1, "semantic_promotion": 3, "observation_access": 3, "publication": 7}
    for gate in pending_gates:
        queue.append({
            "priority": gate_priorities[gate["required_before"]],
            "target_type": "human_gate", "gate": gate["gate"], "state": gate["status"],
            "required_before": gate["required_before"], "reason": gate["reason"],
            "command": "record-database-deep-map-human-gate",
        })
    checks_by_stage: dict[tuple[str | None, str], list[dict[str, Any]]] = {}
    for check in checks:
        checks_by_stage.setdefault((check["unit_id"], check["stage"]), []).append(check)
    for phase in EARLY_PHASES:
        value = project["phase_states"][phase]
        if value["state"] in ACTIVE_STATES:
            queue.append({"priority": 1, "target_type": "project_phase", "phase": phase, "state": value["state"], "blockers": value["blockers"], "command": "record-database-deep-map-phase"})
    for unit in units:
        for stage in unit["required_stages"]:
            value = unit["stages"][stage]
            if value["state"] in ACTIVE_STATES:
                related_checks = checks_by_stage.get((unit["id"], stage), [])
                stage_priority = 4 if stage == "access" and protected_observation_access else 2
                queue.append({"priority": 8 if value["state"] == "blocked" else stage_priority, "sequence": unit["sequence"], "target_type": "work_unit_stage", "unit_id": unit["id"], "upstream_id": unit["upstream_id"], "label": unit["label"], "stage": stage, "state": value["state"], "route_modules": unit["route_modules"], "required_checks": [{"check_id": item["id"], "facet_id": item["facet_id"], "state": item["state"], "requirement": item["requirement"]} for item in related_checks], "checkpoint": value["notes"], "blockers": value["blockers"], "command": "record-database-deep-map-stage"})
        for spine_name in SPINES:
            value = unit["spines"][spine_name]
            prerequisites_ready = all(
                unit["stages"][stage]["state"] in MAPPED_STATES
                for stage in SPINE_PREREQUISITES[spine_name]
            )
            if value["state"] in ACTIVE_STATES and prerequisites_ready:
                check_stage = next(key for key, mapped in SPINE_CHECK_STAGES.items() if mapped == spine_name)
                related_checks = checks_by_stage.get((unit["id"], check_stage), [])
                queue.append({
                    "priority": 8 if value["state"] == "blocked" else 2,
                    "sequence": unit["sequence"], "target_type": "work_unit_spine",
                    "unit_id": unit["id"], "upstream_id": unit["upstream_id"], "label": unit["label"],
                    "stage": check_stage, "spine": spine_name, "state": value["state"],
                    "route_modules": unit["route_modules"],
                    "required_checks": [{"check_id": item["id"], "facet_id": item["facet_id"], "state": item["state"], "requirement": item["requirement"]} for item in related_checks],
                    "checkpoint": value["checkpoint"], "blockers": value["blockers"],
                    "command": "record-database-deep-map-spine",
                })
    for check in checks_by_stage.get((None, "project"), []):
        if check["state"] in CHECK_ACTIVE_STATES:
            queue.append({"priority": 8 if check["state"] in {"blocked", "failed", "needs_human_review"} else 3, "target_type": "route_contract_check", "check_id": check["id"], "facet_id": check["facet_id"], "stage": "project", "state": check["state"], "route_modules": check["route_modules"], "checkpoint": check["notes"], "blockers": check["blockers"], "requirement": check["requirement"], "command": "record-database-deep-map-check"})
    for phase in EARLY_PHASES:
        value = project["phase_states"][phase]
        if value["state"] == "mapped_complete":
            queue.append({"priority": 4, "target_type": "project_phase_verification", "phase": phase, "state": value["state"], "command": "record-database-deep-map-phase"})
    for unit in units:
        for stage in unit["required_stages"]:
            value = unit["stages"][stage]
            if value["state"] == "mapped_complete":
                related_checks = checks_by_stage.get((unit["id"], stage), [])
                queue.append({"priority": 5, "sequence": unit["sequence"], "target_type": "work_unit_verification", "unit_id": unit["id"], "upstream_id": unit["upstream_id"], "label": unit["label"], "stage": stage, "state": value["state"], "route_modules": unit["route_modules"], "required_checks": [{"check_id": item["id"], "facet_id": item["facet_id"], "state": item["state"], "requirement": item["requirement"]} for item in related_checks], "checkpoint": value["notes"], "command": "record-database-deep-map-stage"})
        for spine_name in SPINES:
            value = unit["spines"][spine_name]
            if value["state"] == "mapped_complete":
                check_stage = next(key for key, mapped in SPINE_CHECK_STAGES.items() if mapped == spine_name)
                related_checks = checks_by_stage.get((unit["id"], check_stage), [])
                queue.append({
                    "priority": 5, "sequence": unit["sequence"], "target_type": "work_unit_spine_verification",
                    "unit_id": unit["id"], "upstream_id": unit["upstream_id"], "label": unit["label"],
                    "stage": check_stage, "spine": spine_name, "state": value["state"],
                    "route_modules": unit["route_modules"],
                    "required_checks": [{"check_id": item["id"], "facet_id": item["facet_id"], "state": item["state"], "requirement": item["requirement"]} for item in related_checks],
                    "checkpoint": value["checkpoint"], "command": "record-database-deep-map-spine",
                })
    unit_by_id = {item["id"]: item for item in units}
    for check in checks:
        if check["unit_id"] is None or check["state"] not in CHECK_ACTIVE_STATES:
            continue
        unit = unit_by_id[check["unit_id"]]
        stage_state = unit_gate_state(unit, check["stage"])
        if stage_state not in MAPPED_STATES:
            continue
        queue.append({"priority": 8 if check["state"] in {"blocked", "failed", "needs_human_review"} else 6, "sequence": unit["sequence"], "target_type": "route_contract_check", "check_id": check["id"], "facet_id": check["facet_id"], "unit_id": unit["id"], "upstream_id": unit["upstream_id"], "label": unit["label"], "stage": check["stage"], "state": check["state"], "route_modules": check["route_modules"], "checkpoint": check["notes"], "blockers": check["blockers"], "requirement": check["requirement"], "command": "record-database-deep-map-check"})
    queue_stage_order = {
        **{stage: index for index, stage in enumerate(UNIT_STAGES)},
        "structural_spine": len(UNIT_STAGES),
        "disciplinary_spine": len(UNIT_STAGES) + 1,
        "variable_bridge": len(UNIT_STAGES) + 2,
    }
    return sorted(
        queue,
        key=lambda item: (
            item["priority"],
            item.get("sequence", 0),
            queue_stage_order.get(item.get("stage"), -1),
        ),
    )


def resume_database_deep_map(project_dir: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir); require_project(target)
    project = read_json(target / PROJECT_FILE); units = read_jsonl(target / UNIT_FILE); checks = read_jsonl(target / CHECK_FILE)
    audit = audit_database_deep_map(target)
    if audit["errors"]:
        project["workflow_status"] = "blocked"; project["next_actions"] = ["repair-deep-map-project"]
        summary = f"Blocked by {len(audit['errors'])} audit errors."
        queue = []
    else:
        queue = action_queue(project, units, checks)
        if queue:
            if queue[0]["target_type"] == "human_gate" or queue[0]["state"] == "needs_human_review":
                project["workflow_status"] = "needs_human_review"
            elif queue[0]["state"] in {"blocked", "failed"}:
                project["workflow_status"] = "blocked"
            else:
                project["workflow_status"] = "in_progress"
            project["current_phase"] = queue[0].get("phase", "deep_mapping")
            project["next_actions"] = [queue[0]["command"]]
            target_label = queue[0].get("upstream_id") or queue[0].get("phase") or queue[0].get("facet_id") or queue[0].get("gate")
            target_stage = queue[0].get("stage") or queue[0].get("phase") or queue[0].get("required_before")
            summary = f"Next target: {target_label} / {target_stage}."
        elif audit["execution_ready_for_storage"]:
            project["workflow_status"] = "ready_for_storage"; project["current_phase"] = "storage"
            project["next_actions"] = ["prepare-database-deep-map-storage"]
            summary = "Step 2 execution is closed; seal the fingerprinted handoff package for Step 3 Storage."
        else:
            project["workflow_status"] = "in_progress"; project["current_phase"] = "validation"
            project["next_actions"] = ["record-database-deep-map-phase"]
            summary = "Unit ledger has no active mapping work, but strict project-level completion gates remain open."
    append_history(project, "resume-database-deep-map", summary); write_json(target / PROJECT_FILE, project)
    updated_audit = audit_database_deep_map(target); sync_report(target, project, updated_audit)
    return {"operation": "resume_database_deep_map", "project_id": project["id"], "workflow_status": project["workflow_status"], "current_phase": project["current_phase"], "summary": summary, "next_target": queue[0] if queue else None, "queue_preview": queue[:10], "progress": audit["progress"], "next_actions": project["next_actions"]}


def database_deep_map_status(project_dir: str | Path) -> dict[str, Any]:
    return {**audit_database_deep_map(project_dir), "operation": "database_deep_map_status"}


def prepare_database_deep_map_archive(project_dir: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir); require_project(target)
    project = read_json(target / PROJECT_FILE)
    original_project = json.loads(json.dumps(project))
    manifest = ensure_staging_manifest(target, project)
    original_manifest = json.loads(json.dumps(manifest))
    audit = audit_database_deep_map(target)
    early_open = [name for name in EARLY_PHASES if project["phase_states"][name]["state"] not in CLOSED_STATES]
    if early_open:
        raise ValueError("cannot prepare archive; unclosed project phases: " + ", ".join(early_open))
    if not audit["execution_ready_for_storage"]:
        raise ValueError("cannot prepare archive; strict unit-stage, dual-spine, route-contract, execution-lock, diagnostic-plan, or human-gate requirements are not satisfied")
    errors = validate_merged_registry(target)
    if errors:
        raise ValueError("cannot prepare archive; staged registry package is invalid: " + "; ".join(errors))
    units = read_jsonl(target / UNIT_FILE)
    checks = read_jsonl(target / CHECK_FILE)
    timestamp = now()
    manifest["state"] = "sealed"; manifest["updated_at"] = timestamp
    package = archive_package_payload(project, units, checks, manifest, timestamp)
    write_json(target / STAGING_MANIFEST_FILE, manifest)
    write_json(target / ARCHIVE_PACKAGE_FILE, package)
    project["phase_states"]["deep_mapping"] = phase_state("verified_complete", timestamp, "Step 2 closed every required stage, structural spine, disciplinary spine, variable bridge, and route obligation within the locked boundary.", project["phase_states"]["boundary"]["evidence"])
    project["phase_states"]["validation"] = phase_state("in_progress", timestamp)
    project["workflow_status"] = "ready_for_storage"; project["current_phase"] = "storage"
    project["next_actions"] = ["archive-database-deep-map", "prepare-database-storage"]
    append_history(project, "prepare-database-deep-map-storage", "Sealed the fingerprinted Step 2 handoff package for Step 3 Storage.")
    write_json(target / PROJECT_FILE, project)
    package_audit = audit_database_deep_map_archive(target)
    if package_audit["errors"]:
        write_json(target / STAGING_MANIFEST_FILE, original_manifest)
        write_json(target / PROJECT_FILE, original_project)
        (target / ARCHIVE_PACKAGE_FILE).unlink(missing_ok=True)
        raise ValueError("archive preparation failed audit: " + "; ".join(package_audit["errors"]))
    sync_report(target, project, audit_database_deep_map(target))
    return {
        "operation": "prepare_database_deep_map_archive",
        "project_id": project["id"],
        "workflow_status": "ready_for_storage",
        "archive_package": str(target / ARCHIVE_PACKAGE_FILE),
        "package_fingerprint": package["package_fingerprint"],
        "archive_audit": package_audit,
    }


def audit_database_deep_map_archive(project_dir: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir); require_project(target)
    project = read_json(target / PROJECT_FILE)
    manifest_path = target / STAGING_MANIFEST_FILE
    if manifest_path.is_file():
        manifest = read_json(manifest_path)
    else:
        manifest = empty_staging_manifest(project, project["created_at"])
    package_path = target / ARCHIVE_PACKAGE_FILE
    errors: list[str] = []
    warnings: list[str] = []
    if not package_path.is_file():
        errors.append(f"missing {ARCHIVE_PACKAGE_FILE}; Step 2 must prepare the archive handoff first")
        package = None
    else:
        package = read_json(package_path)
        errors.extend(validate_schema(package, "database_deep_map_archive_package.schema.json", ARCHIVE_PACKAGE_FILE))
    execution_audit = audit_database_deep_map(target)
    errors.extend(execution_audit["errors"])
    if not execution_audit["execution_ready_for_storage"]:
        errors.append("Step 2 execution is not ready for archive")
    if not manifest_path.is_file():
        errors.append(f"missing {STAGING_MANIFEST_FILE}")
    if manifest["state"] not in {"sealed", "archived"}:
        errors.append("staging manifest is not sealed")
    errors.extend(validate_merged_registry(target))
    manifest_ids = {item["id"] for item in manifest["records"]}
    canonical = registry_index_for_ids(manifest_ids)
    staged = {
        record["id"]: record
        for records in staged_collections(target).values()
        for record in records
        if record.get("id") in manifest_ids
    }
    archive_complete = archive_receipt_is_valid(target, project)
    for item in manifest["records"]:
        canonical_record = canonical.get(item["id"])
        staged_record = staged.get(item["id"])
        if staged_record is None:
            errors.append(f"{item['id']}: staged record is missing")
            continue
        if manifest["state"] == "archived":
            if canonical_record != staged_record:
                errors.append(f"{item['id']}: archived record no longer matches canonical content")
            continue
        if item["action"] == "create" and canonical_record is not None:
            errors.append(f"{item['id']}: canonical create conflict; the ID now exists")
        if item["action"] in {"update", "unchanged"}:
            if canonical_record is None:
                errors.append(f"{item['id']}: canonical base record disappeared")
            elif fingerprint(canonical_record) != item["base_fingerprint"]:
                errors.append(f"{item['id']}: canonical base fingerprint changed after staging")
        if item["action"] == "unchanged" and canonical_record != staged_record:
            errors.append(f"{item['id']}: unchanged action no longer matches canonical content")
    if package is not None:
        units = read_jsonl(target / UNIT_FILE); checks = read_jsonl(target / CHECK_FILE)
        prepared_at = package.get("prepared_at")
        if isinstance(prepared_at, str):
            expected = archive_package_payload(project, units, checks, manifest, prepared_at)
            for key in (
                "project_id", "source_id", "plan_fingerprint", "scope_fingerprint",
                "unit_manifest_fingerprint", "execution_ledger_fingerprint",
                "staging_manifest_fingerprint", "record_count", "collection_counts",
                "package_fingerprint",
            ):
                if package.get(key) != expected.get(key):
                    errors.append(f"archive package {key} is stale or mismatched")
    if manifest["state"] == "archived" and not archive_complete:
        errors.append("archive receipt is missing, invalid, or stale")
    if package is not None and not manifest["records"]:
        warnings.append("Archive package contains no new or updated staged records; it seals a project whose referenced records are already canonical.")
    return {
        "operation": "audit_database_deep_map_archive",
        "project_id": project["id"],
        "project_dir": str(target),
        "ready_to_archive": manifest["state"] == "sealed" and not errors,
        "archive_complete": archive_complete,
        "staging_state": manifest["state"],
        "record_count": len(manifest["records"]),
        "actions": {
            action: sum(item["action"] == action for item in manifest["records"])
            for action in ("create", "update", "unchanged")
        },
        "package_fingerprint": package.get("package_fingerprint") if package else None,
        "errors": errors,
        "warnings": warnings,
    }


def database_deep_map_archive_status(project_dir: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir)
    result = audit_database_deep_map_archive(target)
    receipt_path = target / ARCHIVE_RECEIPT_FILE
    result["archive_receipt_present"] = receipt_path.is_file()
    result["archived"] = result["archive_complete"]
    result["archive_receipt"] = str(receipt_path) if receipt_path.is_file() else None
    return {**result, "operation": "database_deep_map_archive_status"}


def archive_database_deep_map(project_dir: str | Path) -> dict[str, Any]:
    target = resolve_project_dir(project_dir); require_project(target)
    existing_project = read_json(target / PROJECT_FILE)
    if archive_receipt_is_valid(target, existing_project):
        existing_receipt = read_json(target / ARCHIVE_RECEIPT_FILE)
        return {
            "operation": "archive_database_deep_map",
            "project_id": existing_project["id"],
            "workflow_status": "ready_for_storage",
            "status": "already_archived",
            "archive_receipt": str(target / ARCHIVE_RECEIPT_FILE),
            "receipt": existing_receipt,
            "audit": audit_database_deep_map(target),
        }
    archive_audit = audit_database_deep_map_archive(target)
    if archive_audit["errors"]:
        raise ValueError("cannot archive database deep map: " + "; ".join(archive_audit["errors"]))
    project = read_json(target / PROJECT_FILE); original_project = json.loads(json.dumps(project))
    manifest = read_json(target / STAGING_MANIFEST_FILE); original_manifest = json.loads(json.dumps(manifest))
    package = read_json(target / ARCHIVE_PACKAGE_FILE)
    affected_files = sorted({item["registry_file"] for item in manifest["records"] if item["action"] != "unchanged"})
    receipt_path = target / ARCHIVE_RECEIPT_FILE
    original_receipt = receipt_path.read_text(encoding="utf-8") if receipt_path.is_file() else None
    staged = staged_collections(target)
    changed_ids_by_file = {
        filename: {
            item["id"]
            for item in manifest["records"]
            if item["registry_file"] == filename and item["action"] != "unchanged"
        }
        for filename in affected_files
    }
    with tempfile.TemporaryDirectory(prefix=".grdr-registry-transaction-", dir=REGISTRY_ROOT) as temporary:
        transaction_root = Path(temporary)
        prepared_root = transaction_root / "prepared"
        backup_root = transaction_root / "backup"
        prepared_root.mkdir()
        backup_root.mkdir()
        for filename in affected_files:
            changed_ids = changed_ids_by_file[filename]
            changed_records = {
                record["id"]: record
                for record in staged.get(filename, [])
                if record.get("id") in changed_ids
            }
            if set(changed_records) != changed_ids:
                missing = sorted(changed_ids - set(changed_records))
                raise ValueError(f"missing staged records for {filename}: {', '.join(missing)}")
            write_streamed_registry_merge(
                REGISTRY_ROOT / filename,
                prepared_root / filename,
                changed_records,
            )
        replaced_files: list[str] = []
        try:
            for filename in affected_files:
                canonical_path = REGISTRY_ROOT / filename
                backup_path = backup_root / filename
                if canonical_path.is_file():
                    try:
                        os.link(canonical_path, backup_path)
                    except OSError:
                        shutil.copy2(canonical_path, backup_path)
                os.replace(prepared_root / filename, canonical_path)
                replaced_files.append(filename)
            validation_errors = validate_merged_registry(target)
            if validation_errors:
                raise ValueError("; ".join(validation_errors))
            for filename in affected_files:
                expected = {
                    record["id"]: record
                    for record in staged.get(filename, [])
                    if record.get("id") in changed_ids_by_file[filename]
                }
                actual = read_jsonl_selected(REGISTRY_ROOT / filename, set(expected))
                if actual != expected:
                    raise ValueError(f"post-write canonical verification failed for {filename}")
            if affected_files:
                validation_message = (
                    "Incremental schema, duplicate-ID, referential-closure, and post-write "
                    f"content validation passed for {len(affected_files)} streamed registry files."
                )
                catalog_message = (
                    "Core remained immutable; the source-specific human catalog is generated "
                    "inside the source repository during Storage."
                )
            else:
                validation_message = "Prospective canonical registry was Schema-valid and byte-identical to the current registry; no post-write validation was required."
                catalog_message = "Core remained immutable; no external registry catalog rebuild was required."
            timestamp = now()
            action_counts = {
                action: sum(item["action"] == action for item in manifest["records"])
                for action in ("create", "update", "unchanged")
            }
            receipt = {
                "schema_version": "1.0.0",
                "project_id": project["id"],
                "source_id": project["source_id"],
                "package_fingerprint": package["package_fingerprint"],
                "registry_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
                "created_count": action_counts["create"],
                "updated_count": action_counts["update"],
                "unchanged_count": action_counts["unchanged"],
                "collection_counts": package["collection_counts"],
                "registry_validation": validation_message,
                "catalog_validation": catalog_message,
                "archived_at": timestamp,
            }
            receipt["receipt_fingerprint"] = fingerprint(receipt)
            validate_update(receipt, "database_deep_map_archive_receipt.schema.json", ARCHIVE_RECEIPT_FILE)
            manifest["state"] = "archived"; manifest["updated_at"] = timestamp
            write_json(target / STAGING_MANIFEST_FILE, manifest)
            write_json(target / ARCHIVE_RECEIPT_FILE, receipt)
            project["phase_states"]["validation"] = phase_state("verified_complete", timestamp, "The Storage transaction validated the prospective canonical registry and stream-promoted staged records.", project["phase_states"]["boundary"]["evidence"])
            project["phase_states"]["completion_audit"] = phase_state("in_progress", timestamp)
            project["workflow_status"] = "ready_for_storage"; project["current_phase"] = "storage"
            project["next_actions"] = ["prepare-database-storage", "database-storage-status"]
            append_history(project, "archive-database-deep-map", "Storage sub-transaction stream-promoted the sealed execution package into the canonical GRDR registry and issued its internal archive receipt.")
            write_json(target / PROJECT_FILE, project)
            final_audit = audit_database_deep_map(target)
            if final_audit["errors"] or not final_audit["canonical_archive_complete"]:
                raise ValueError("canonical Storage sub-transaction failed final audit: " + "; ".join(final_audit["errors"]))
        except Exception:
            for filename in reversed(replaced_files):
                backup_path = backup_root / filename
                if backup_path.is_file():
                    os.replace(backup_path, REGISTRY_ROOT / filename)
                else:
                    (REGISTRY_ROOT / filename).unlink(missing_ok=True)
            write_json(target / STAGING_MANIFEST_FILE, original_manifest)
            write_json(target / PROJECT_FILE, original_project)
            if original_receipt is None:
                receipt_path.unlink(missing_ok=True)
            else:
                atomic_write_text(receipt_path, original_receipt)
            raise
    sync_report(target, project, final_audit)
    return {
        "operation": "archive_database_deep_map",
        "project_id": project["id"],
        "workflow_status": "ready_for_storage",
        "archive_receipt": str(target / ARCHIVE_RECEIPT_FILE),
        "receipt": receipt,
        "audit": final_audit,
    }


def complete_database_deep_map(project_dir: str | Path) -> dict[str, Any]:
    """Compatibility wrapper that closes only the internal canonical promotion sub-transaction."""
    target = resolve_project_dir(project_dir)
    if not (target / ARCHIVE_PACKAGE_FILE).is_file():
        prepare_database_deep_map_archive(target)
    return archive_database_deep_map(target)


def prepare_database_deep_map_storage(project_dir: str | Path) -> dict[str, Any]:
    """Public Step 2 handoff name for the Plan → Execute → Storage pipeline."""
    result = prepare_database_deep_map_archive(project_dir)
    return {**result, "operation": "prepare_database_deep_map_storage"}
