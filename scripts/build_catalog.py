#!/usr/bin/env python3
"""Build and verify the human- and agent-readable GRDR source catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
CATALOG = ROOT / "catalog"
SOURCE_CATALOG = CATALOG / "sources"
ROOT_README = ROOT / "README.md"
START_MARKER = "<!-- GRDR_SOURCE_CATALOG_START -->"
END_MARKER = "<!-- GRDR_SOURCE_CATALOG_END -->"
PAGED_LAYER_THRESHOLD = 250
PAGED_LAYER_SIZE = 100

STATUS_LABELS = {
    "verified": "已验证",
    "partially_verified": "部分验证",
    "unverified": "待验证候选",
    "stale": "验证已过期",
    "conflicted": "证据冲突",
    "deprecated": "已停用",
    "unavailable": "当前不可用",
}


def load_jsonl(name: str) -> list[dict[str, Any]]:
    path = REGISTRY / f"{name}.jsonl"
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def source_slug(source_id: str) -> str:
    return source_id.rsplit(":", 1)[-1]


def value(item: Any) -> str:
    if item is None or item == "" or item == []:
        return "未知 / 尚未登记"
    if isinstance(item, bool):
        return "是" if item else "否"
    if isinstance(item, list):
        return "、".join(value(part) for part in item)
    if isinstance(item, dict):
        return json.dumps(item, ensure_ascii=False, sort_keys=True)
    return str(item).replace("\n", "<br>").replace("|", "\\|")


def link(label: str, url: str | None) -> str:
    return f"[{label}]({url})" if url else label


def status(record: dict[str, Any]) -> str:
    code = record.get("verification", {}).get("status", "unverified")
    return f"{STATUS_LABELS.get(code, code)} (`{code}`)"


def last_verified(record: dict[str, Any]) -> str:
    return value(record.get("verification", {}).get("last_verified_at"))


def table(rows: Iterable[tuple[str, Any]]) -> str:
    body = ["| 字段 | 内容 |", "|---|---|"]
    body.extend(f"| {name} | {value(item)} |" for name, item in rows)
    return "\n".join(body)


def evidence_list(record: dict[str, Any]) -> str:
    evidence = record.get("evidence", [])
    if not evidence:
        return "- 尚未登记证据。"
    lines = []
    for item in evidence:
        publisher = item.get("publisher") or "发布者未知"
        supports = "、".join(item.get("supports", [])) or "支持范围未注明"
        retrieved = item.get("retrieved_at") or "检索时间未知"
        lines.append(
            f"- [{item['title']}]({item['url']}) — {publisher}；"
            f"证据类型：`{item['evidence_type']}`；支持：{supports}；检索于 {retrieved}。"
        )
    return "\n".join(lines)


def compact_evidence(record: dict[str, Any]) -> str:
    evidence = record.get("evidence", [])
    if not evidence:
        return "尚未登记"
    return "<br>".join(
        f"[{value(item.get('title') or item['url'])}]({item['url']})"
        for item in evidence
    )


def missing_layer(entity: str) -> str:
    return (
        f"> 尚未建立{entity}层记录。这表示 GRDR 还没有完成这一层的核验与展开，"
        f"不表示该数据库不存在相关{entity}。"
    )


def build_context() -> dict[str, Any]:
    collections = {
        name: load_jsonl(name)
        for name in (
            "institutions",
            "sources",
            "datasets",
            "data_structures",
            "resources",
            "data_elements",
            "variables",
            "constructs",
            "semantic_nodes",
            "relationships",
            "source_profiles",
        )
    }
    collections["institution_index"] = {
        item["id"]: item for item in collections["institutions"]
    }
    from database_deep_map import audit_database_deep_map

    deep_maps = []
    for project_file in sorted((ROOT / "deep_map_projects").glob("*/project.json")):
        deep_maps.append(audit_database_deep_map(project_file.parent))
    collections["deep_map_projects"] = deep_maps
    return collections


def linked_records(source: dict[str, Any], context: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    datasets = [
        item for item in context["datasets"] if source["id"] in item["source_ids"]
    ]
    dataset_ids = {item["id"] for item in datasets}
    resources = [
        item
        for item in context["resources"]
        if item["source_id"] == source["id"]
        or dataset_ids.intersection(item["dataset_ids"])
    ]
    data_structures = [
        item
        for item in context["data_structures"]
        if item["source_id"] == source["id"]
        or dataset_ids.intersection(item["dataset_ids"])
    ]
    variables = [
        item
        for item in context["variables"]
        if dataset_ids.intersection(item["dataset_ids"])
    ]
    data_elements = [
        item
        for item in context["data_elements"]
        if dataset_ids.intersection(item["dataset_ids"])
    ]
    construct_ids = {
        construct_id
        for item in variables
        for construct_id in item["construct_ids"]
    }
    constructs = [
        item for item in context["constructs"] if item["id"] in construct_ids
    ]
    semantic_index = {item["id"]: item for item in context["semantic_nodes"]}
    relevant_ids = {
        source["id"],
        *dataset_ids,
        *{item["id"] for item in variables},
        *construct_ids,
    }
    semantic_ids = {
        endpoint
        for edge in context["relationships"]
        if edge["subject_id"] in relevant_ids or edge["object_id"] in relevant_ids
        for endpoint in (edge["subject_id"], edge["object_id"])
        if endpoint in semantic_index
    }
    pending = list(semantic_ids)
    while pending:
        current = semantic_index[pending.pop()]
        for parent_id in current.get("parent_ids", []):
            if parent_id not in semantic_ids and parent_id in semantic_index:
                semantic_ids.add(parent_id); pending.append(parent_id)
    semantic_nodes = [semantic_index[item] for item in sorted(semantic_ids)]
    institution_ids = set(source["maintainer_ids"])
    institution_ids.update(
        edge["object_id"]
        for edge in context["relationships"]
        if edge["subject_id"] in {source["id"], *dataset_ids}
        and edge["object_id"] in context["institution_index"]
        and edge["predicate"] in {"produced_by", "published_by", "maintained_by", "governed_by"}
    )
    institutions = [context["institution_index"][item] for item in sorted(institution_ids)]
    source_profiles = [
        item
        for item in context["source_profiles"]
        if item["source_id"] == source["id"]
    ]
    deep_map_projects = [
        item for item in context["deep_map_projects"] if item["source_id"] == source["id"]
    ]
    deep_map_projects.sort(
        key=lambda item: (
            item.get("scope", {}).get("snapshot_at", ""),
            item.get("progress", {}).get("strict_completion_percentage", 0.0),
            item.get("project_id", ""),
        ),
        reverse=True,
    )
    return {
        "institutions": institutions,
        "datasets": datasets,
        "data_structures": data_structures,
        "resources": resources,
        "data_elements": data_elements,
        "variables": variables,
        "constructs": constructs,
        "semantic_nodes": semantic_nodes,
        "source_profiles": source_profiles,
        "deep_map_projects": deep_map_projects,
    }


def profile_stage(linked: dict[str, list[dict[str, Any]]]) -> str:
    if all(linked[name] for name in ("institutions", "datasets", "data_structures", "variables", "constructs")):
        return "six_layer_chain_present"
    if linked["variables"]:
        return "variable_depth_started"
    if linked["data_structures"]:
        return "data_structure_depth_started"
    if linked["datasets"]:
        return "dataset_depth_started"
    return "source_only"


def declared_scope(linked: dict[str, list[dict[str, Any]]]) -> tuple[str, str]:
    if not linked["source_profiles"]:
        return "undeclared", "not_assessed"
    profile = linked["source_profiles"][0]
    return profile["scope_mode"], profile["inventory_claim"]


def deep_map_summary(linked: dict[str, list[dict[str, Any]]]) -> str:
    if not linked["deep_map_projects"]:
        return "尚未建立持久化深度映射工程"
    return "；".join(
        f"{item['title']} [{item['workflow_status']}]: "
        f"{item['progress']['mapping_percentage']}% mapped / "
        f"{item['progress']['strict_completion_percentage']}% strict / "
        f"{item['progress']['dual_spine_percentage']}% dual-spine"
        for item in linked["deep_map_projects"]
    )


def render_deep_map_projects(records: list[dict[str, Any]]) -> str:
    if not records:
        return "> 尚未建立持久化数据库深度映射工程；当前六层记录不能解释为全库完成。"
    sections = []
    for item in records:
        progress = item["progress"]
        slug = Path(item["project_dir"]).name
        sections.append(
            f"#### {item['title']}\n\n"
            + table(
                [
                    ("工程ID", f"`{item['project_id']}`"),
                    ("工程状态", f"`{item['workflow_status']}`"),
                    ("边界", item["scope"]["boundary_statement"]),
                    ("工作单元", f"{progress['work_units']} / {progress['expected_work_units']}"),
                    ("映射进度", f"{progress['mapping_percentage']}%"),
                    ("严格完成度", f"{progress['strict_completion_percentage']}%"),
                    ("双主干与桥梁完成度", f"{progress['dual_spine_percentage']}%"),
                    ("完整闭合工作单元", f"{progress['fully_closed_work_units']} / {progress['work_units']}"),
                    ("阻塞阶段", progress["blocked_unit_stages"]),
                    ("Execute可交Storage", item["execution_ready_for_storage"]),
                    ("中央注册表事务入库", item["canonical_archive_complete"]),
                    ("完整Storage", item["storage_complete"]),
                    ("可声明完成", item["completion_ready"]),
                    ("工程详情", f"[打开工程台账](../../../deep_map_projects/{slug}/README.md)"),
                ]
            )
        )
    return "\n\n".join(sections)


def render_institutions(records: list[dict[str, Any]]) -> str:
    if not records:
        return missing_layer("机构")
    sections = []
    for item in records:
        sections.append(
            f"#### {item['name']}\n\n"
            + table(
                [
                    ("GRDR ID", f"`{item['id']}`"),
                    ("机构主页", link(item["primary_url"], item["primary_url"])),
                    ("机构类型", f"`{item['institution_type']}`"),
                    ("管辖/归属", item.get("jurisdiction")),
                    ("验证状态", status(item)),
                    ("最后验证", last_verified(item)),
                    ("验证说明", item.get("verification", {}).get("notes")),
                ]
            )
            + "\n\n**机构证据**\n\n"
            + evidence_list(item)
        )
    return "\n\n".join(sections)


def render_source(source: dict[str, Any]) -> str:
    scope = source["scope"]
    authority = source["authority"]
    access = source["access"]
    return table(
        [
            ("GRDR ID", f"`{source['id']}`"),
            ("数据库名称", source["name"]),
            ("别名", source.get("aliases", [])),
            ("官方入口", link(source["canonical_url"], source["canonical_url"])),
            ("数据源类型", [f"`{item}`" for item in source["source_classes"]]),
            ("学科领域", scope["disciplines"]),
            ("主题维度", scope["topics"]),
            ("地理范围", f"`{scope['geographic_scope']}`"),
            ("时间范围", scope.get("temporal_coverage_note")),
            ("观察单位", scope["observation_units"]),
            ("数据模态", scope["modalities"]),
            ("权威角色", [f"`{item}`" for item in authority["roles"]]),
            ("来源位置", f"`{authority['provenance_position']}`"),
            ("权威与来源说明", authority.get("notes")),
            ("开放程度", f"`{access['availability']}`"),
            ("访问方式", [f"`{item}`" for item in access["modes"]]),
            ("需要注册", access["registration_required"]),
            ("机器访问", f"`{access['machine_access']}`"),
            ("许可状态", f"`{access['license_status']}`"),
            ("访问说明", access.get("access_notes")),
            ("验证状态", status(source)),
            ("最后验证", last_verified(source)),
            ("验证说明", source["verification"].get("notes")),
        ]
    ) + "\n\n**数据库层证据**\n\n" + evidence_list(source)


def render_datasets(records: list[dict[str, Any]]) -> str:
    if not records:
        return missing_layer("数据集")
    sections = []
    for item in records:
        scope = item["scope"]
        release = item["release"]
        methodology = item["methodology"]
        citation = item.get("citation", {})
        native = item.get("source_native") or {}
        sections.append(
            f"#### {item['name']}\n\n"
            + table(
                [
                    ("GRDR ID", f"`{item['id']}`"),
                    ("上游目录ID", native.get("catalog_id")),
                    ("上游目录入口", link(native.get("catalog_url") or "未知", native.get("catalog_url"))),
                    ("原始提供机构", native.get("provider_name")),
                    ("生命周期", f"`{native.get('lifecycle_status')}`" if native else None),
                    ("上游最近更新", native.get("last_upstream_update")),
                    ("上游计划更新", native.get("next_upstream_update")),
                    ("说明", item["description"]),
                    ("学科领域", scope["disciplines"]),
                    ("主题维度", scope["topics"]),
                    ("目标总体", scope["population"]),
                    ("观察单位", scope["observation_units"]),
                    ("地理覆盖", scope["geographic_coverage"]),
                    ("空间分辨率", scope["spatial_resolution"]),
                    ("时间覆盖", scope["temporal_coverage"]),
                    ("时间分辨率", scope["temporal_resolution"]),
                    ("数据模态", scope["modalities"]),
                    ("当前版本", release["current_version"]),
                    ("发布日期", release["release_date"]),
                    ("更新频率", release["update_frequency"]),
                    ("有修订政策", release["revision_policy_known"]),
                    ("保留历史版本", release["historical_vintages_available"]),
                    ("数据生成过程", methodology["data_generating_processes"]),
                    ("协调方式", f"`{methodology['harmonization']}`"),
                    ("模型估计", f"`{methodology['modeled_estimates']}`"),
                    ("方法文件", link(methodology.get("methodology_url") or "未知", methodology.get("methodology_url"))),
                    ("已知限制", methodology["limitations"]),
                    ("建议引用", citation.get("preferred_citation")),
                    ("DOI", citation.get("doi")),
                    ("引用入口", link(citation.get("citation_url") or "未知", citation.get("citation_url"))),
                    ("验证状态", status(item)),
                    ("最后验证", last_verified(item)),
                ]
            )
            + "\n\n**数据集层证据**\n\n"
            + evidence_list(item)
        )
    return "\n\n".join(sections)


def render_resources(records: list[dict[str, Any]]) -> str:
    if not records:
        return missing_layer("访问资源")
    sections = []
    for item in records:
        access = item["access"]
        sections.append(
            f"#### {item['name']}\n\n"
            + table(
                [
                    ("GRDR ID", f"`{item['id']}`"),
                    ("资源入口", link(item["url"], item["url"])),
                    ("资源类型", f"`{item['resource_type']}`"),
                    ("格式", item["formats"]),
                    ("开放程度", f"`{access['availability']}`"),
                    ("身份验证", f"`{access['authentication']}`"),
                    ("机器访问", f"`{access['machine_access']}`"),
                    ("限流已知", access["rate_limit_known"]),
                    ("许可状态", f"`{access['license_status']}`"),
                    ("访问说明", access.get("notes")),
                    ("验证状态", status(item)),
                    ("最后验证", last_verified(item)),
                ]
            )
            + "\n\n**资源层证据**\n\n"
            + evidence_list(item)
        )
    return "\n\n".join(sections)


def render_data_structures(records: list[dict[str, Any]]) -> str:
    if not records:
        return missing_layer("数据库内部结构")
    sections = []
    for item in records:
        native = item["native_identity"]
        sections.append(
            f"#### {item['label']} (`{item['name']}`)\n\n"
            + table(
                [
                    ("GRDR ID", f"`{item['id']}`"),
                    ("结构类型", f"`{item['structure_type']}`"),
                    ("结构家族", f"`{item['structure_family']}`"),
                    ("上游原生类型", item["native_type"]),
                    ("原生路径", item["native_path"]),
                    ("结构层级", item["structural_level"]),
                    ("结构粒度", item["grain"]),
                    ("稳定排序", item["ordering"]),
                    ("上游系统", native["system"]),
                    ("发布机构标识", native.get("agency_id")),
                    ("上游对象类别", native["object_class"]),
                    ("上游对象 ID", native["object_id"]),
                    ("结构版本", native.get("version")),
                    ("父结构", item["parent_structure_ids"]),
                    ("子结构", item["child_structure_ids"]),
                    ("关键元素", item["key_element_ids"]),
                    ("结构谱系", item["lineage"]),
                    ("附属访问资源", item["resource_ids"]),
                    ("结构说明", item["description"]),
                    ("验证状态", status(item)),
                    ("最后验证", last_verified(item)),
                ]
            )
            + "\n\n**数据结构层证据**\n\n"
            + evidence_list(item)
        )
    return "\n\n".join(sections)


def render_variables(records: list[dict[str, Any]]) -> str:
    if not records:
        return missing_layer("变量")
    sections = []
    for item in records:
        measurement = item["measurement"]
        comparability = item["comparability"]
        native = item.get("source_native") or {}
        sections.append(
            f"#### {item['label']} (`{item['name']}`)\n\n"
            + table(
                [
                    ("GRDR ID", f"`{item['id']}`"),
                    ("上游系统", native.get("system")),
                    ("Dataflow ID", native.get("dataflow_id")),
                    ("数据结构ID", native.get("data_structure_id")),
                    ("维度选择", native.get("dimension_selections", [])),
                    ("研究角色候选", [f"`{role}`" for role in item["role_candidates"]]),
                    ("单位", item["unit"]),
                    ("分母", item["denominator"]),
                    ("目标总体", item["population"]),
                    ("观察单位", item["observation_unit"]),
                    ("空间分辨率", item["spatial_resolution"]),
                    ("时间分辨率", item["temporal_resolution"]),
                    ("测量类型", f"`{measurement['type']}`"),
                    ("客观/主观", f"`{measurement['objective_subjective']}`"),
                    ("直接性", f"`{measurement['directness']}`"),
                    ("定义", measurement["definition"]),
                    ("构造说明", measurement["construction_notes"]),
                    ("可比性", f"`{comparability['status']}`"),
                    ("可比性说明", comparability["notes"]),
                    ("连接键", item["join_keys"]),
                    ("验证状态", status(item)),
                    ("最后验证", last_verified(item)),
                ]
            )
            + "\n\n**变量层证据**\n\n"
            + evidence_list(item)
        )
    return "\n\n".join(sections)


def render_data_elements(records: list[dict[str, Any]]) -> str:
    if not records:
        return missing_layer("数据结构元素")
    sections = []
    for item in records:
        native = item["source_native"]
        codelist = item.get("codelist") or {}
        sections.append(
            f"#### {item['label']} (`{item['name']}`)\n\n"
            + table(
                [
                    ("GRDR ID", f"`{item['id']}`"),
                    ("元素类型", f"`{item['element_type']}`"),
                    ("上游系统", native["system"]),
                    ("Dataflow ID", native.get("dataflow_id")),
                    ("数据结构ID", native.get("data_structure_id")),
                    ("上游元素ID", native["native_id"]),
                    ("位置", native.get("position")),
                    ("附着层级", native.get("attachment_level")),
                    ("定义", item.get("definition")),
                    ("单位", item.get("unit")),
                    ("数据类型", item["representation"].get("data_type")),
                    ("取值说明", item["representation"].get("allowed_values_note")),
                    ("代码表", codelist.get("id")),
                    ("代码数量", codelist.get("code_count")),
                    ("代码表入口", link(codelist.get("url") or "未知", codelist.get("url"))),
                    ("结构角色", [f"`{role}`" for role in item["roles"]]),
                    ("验证状态", status(item)),
                    ("最后验证", last_verified(item)),
                ]
            )
            + "\n\n**数据元素证据**\n\n"
            + evidence_list(item)
        )
    return "\n\n".join(sections)


def render_constructs(records: list[dict[str, Any]]) -> str:
    if not records:
        return missing_layer("理论构念")
    sections = []
    for item in records:
        sections.append(
            f"#### {item['name']}\n\n"
            + table(
                [
                    ("GRDR ID", f"`{item['id']}`"),
                    ("别名", item.get("aliases", [])),
                    ("定义", item["definition"]),
                    ("学科领域", item["domains"]),
                    ("构念类型", f"`{item['construct_type']}`"),
                    ("范围说明", item.get("scope_notes")),
                    ("验证状态", status(item)),
                    ("最后验证", last_verified(item)),
                ]
            )
            + "\n\n**构念层证据**\n\n"
            + evidence_list(item)
        )
    return "\n\n".join(sections)


def render_variable_catalog_page(
    source: dict[str, Any], records: list[dict[str, Any]], version: str, page: int, pages: int
) -> str:
    rows = [
        "| 变量 | GRDR ID | 原生结构与选择 | 定义 / 操作化 | 单位与粒度 | 构念 | 状态 / 证据 |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in records:
        native = item.get("source_native") or {}
        native_details = {
            "system": native.get("system"),
            "dataflow_id": native.get("dataflow_id"),
            "data_structure_id": native.get("data_structure_id"),
            "dimension_selections": native.get("dimension_selections", []),
        }
        measurement = item["measurement"]
        definition = {
            "type": measurement["type"],
            "objective_subjective": measurement["objective_subjective"],
            "directness": measurement["directness"],
            "definition": measurement["definition"],
            "construction_notes": measurement["construction_notes"],
        }
        grain = {
            "unit": item.get("unit"),
            "denominator": item.get("denominator"),
            "population": item.get("population"),
            "observation_unit": item.get("observation_unit"),
            "spatial_resolution": item.get("spatial_resolution"),
            "temporal_resolution": item.get("temporal_resolution"),
            "join_keys": item.get("join_keys", []),
        }
        rows.append(
            "| {} (`{}`) | `{}` | {} | {} | {} | {} | {}<br>{} |".format(
                value(item["label"]),
                value(item["name"]),
                item["id"],
                value(native_details),
                value(definition),
                value(grain),
                value(item["construct_ids"]),
                status(item),
                compact_evidence(item),
            )
        )
    return f"""---
grdr_id: {json.dumps(source['id'], ensure_ascii=False)}
record_type: "source_variable_catalog_page"
registry_version: {json.dumps(version)}
page: {page}
pages: {pages}
records: {len(records)}
---

# {source['name']}：变量目录 {page}/{pages}

<!-- Generated by scripts/build_catalog.py. Edit registry records, not this page. -->

[返回数据库六层总览](../README.md)

本页完整列出这些变量在 GRDR 中登记的原生选择、测量定义、单位/粒度、构念连接、验证状态与证据入口；权威机器记录仍以 `registry/variables.jsonl` 为准。

{chr(10).join(rows)}
"""


def render_construct_catalog_page(
    source: dict[str, Any], records: list[dict[str, Any]], version: str, page: int, pages: int
) -> str:
    rows = [
        "| 构念 | GRDR ID | 学科 / 类型 | 定义 | 适用范围 | 状态 / 证据 |",
        "|---|---|---|---|---|---|",
    ]
    for item in records:
        rows.append(
            "| {} | `{}` | {} | {} | {} | {}<br>{} |".format(
                value(item["name"]),
                item["id"],
                value({"domains": item["domains"], "construct_type": item["construct_type"]}),
                value(item["definition"]),
                value(item.get("scope_notes")),
                status(item),
                compact_evidence(item),
            )
        )
    return f"""---
grdr_id: {json.dumps(source['id'], ensure_ascii=False)}
record_type: "source_construct_catalog_page"
registry_version: {json.dumps(version)}
page: {page}
pages: {pages}
records: {len(records)}
---

# {source['name']}：理论构念目录 {page}/{pages}

<!-- Generated by scripts/build_catalog.py. Edit registry records, not this page. -->

[返回数据库六层总览](../README.md)

本页完整列出这些构念的学科归属、类型、定义、适用范围、验证状态与证据入口；权威机器记录仍以 `registry/constructs.jsonl` 为准。

{chr(10).join(rows)}
"""


def paginated_layer(
    *,
    source: dict[str, Any],
    records: list[dict[str, Any]],
    version: str,
    directory: str,
    entity_label: str,
    renderer: Any,
) -> tuple[str, dict[Path, str]]:
    pages = (len(records) + PAGED_LAYER_SIZE - 1) // PAGED_LAYER_SIZE
    outputs: dict[Path, str] = {}
    links = [
        f"> 本层共 **{len(records):,}** 个{entity_label}，因数量较大按每页最多 "
        f"**{PAGED_LAYER_SIZE}** 条生成可审计目录；没有抽样或省略。"
    ]
    source_dir = SOURCE_CATALOG / source_slug(source["id"])
    for index in range(pages):
        start = index * PAGED_LAYER_SIZE
        chunk = records[start : start + PAGED_LAYER_SIZE]
        page_number = index + 1
        relative = Path(directory) / f"page-{page_number:03d}.md"
        outputs[source_dir / relative] = renderer(source, chunk, version, page_number, pages)
        first = value(chunk[0].get("label") or chunk[0].get("name"))
        last = value(chunk[-1].get("label") or chunk[-1].get("name"))
        links.append(
            f"- [第 {page_number}/{pages} 页（{start + 1:,}–{start + len(chunk):,}："
            f"{first} → {last}）]({relative.as_posix()})"
        )
    return "\n".join(links), outputs


def render_semantic_nodes(records: list[dict[str, Any]]) -> str:
    if not records:
        return missing_layer("学科语义图")
    sections = []
    for item in records:
        sections.append(
            f"#### {item['preferred_label']}\n\n"
            + table(
                [
                    ("GRDR ID", f"`{item['id']}`"),
                    ("语义节点类型", f"`{item['node_type']}`"),
                    ("别名", item["aliases"]),
                    ("定义", item["definition"]),
                    ("多父节点", item["parent_ids"]),
                    ("权威分类映射", item["classification_mappings"]),
                    ("数据库原生术语", item["source_native_terms"]),
                    ("验证状态", status(item)),
                    ("最后验证", last_verified(item)),
                ]
            )
            + "\n\n**学科语义证据**\n\n"
            + evidence_list(item)
        )
    return "\n\n".join(sections)


def render_source_page(
    source: dict[str, Any],
    context: dict[str, Any],
    version: str,
    *,
    linked: dict[str, list[dict[str, Any]]] | None = None,
    variable_content: str | None = None,
    construct_content: str | None = None,
) -> str:
    linked = linked or linked_records(source, context)
    scope_mode, inventory_claim = declared_scope(linked)
    verification_code = source["verification"]["status"]
    if verification_code == "unverified":
        warning = (
            "> **待验证候选。** 当前页面只反映注册表中的候选信息；机构、范围、访问与许可"
            "尚未完成权威证据核验，不应直接作为论文数据来源结论。"
        )
    elif verification_code == "partially_verified":
        warning = (
            "> **部分验证。** 数据库身份和部分官方信息已经核对，但数据集、变量、方法、"
            "许可或覆盖范围仍可能不完整，使用前必须检查对应层级证据。"
        )
    else:
        warning = f"> **验证状态：{status(source)}。** 使用时仍应检查具体数据集和变量层证据。"

    dimensions = table(
        [
            ("学科", source["scope"]["disciplines"]),
            ("主题", source["scope"]["topics"]),
            ("地理", source["scope"]["geographic_scope"]),
            ("时间", source["scope"].get("temporal_coverage_note")),
            ("观察单位", source["scope"]["observation_units"]),
            ("模态", source["scope"]["modalities"]),
            ("已登记数据集", len(linked["datasets"])),
            ("已登记数据库内部结构", len(linked["data_structures"])),
            ("已登记访问资源", len(linked["resources"])),
            ("已登记数据元素", len(linked["data_elements"])),
            ("已登记变量", len(linked["variables"])),
            ("已关联构念", len(linked["constructs"])),
            ("已登记学科语义节点", len(linked["semantic_nodes"])),
            ("当前拆解阶段", f"`{profile_stage(linked)}`"),
            ("持久化深度映射", deep_map_summary(linked)),
            ("已声明拆解范围", f"`{scope_mode}`"),
            ("上游目录完整度", f"`{inventory_claim}`；存在六层链不等于完整枚举"),
        ]
    )
    if linked["source_profiles"]:
        profile = linked["source_profiles"][0]
        enumeration = profile["enumeration"]
        layer_5 = profile.get("layer_5_details")
        blockers = [f"{item['layer']} / {item['type']}: {item['notes']}" for item in profile["blockers"]]
        profile_details = table(
            [
                ("范围说明", profile["scope_statement"]),
                ("清单声明", f"`{profile['inventory_claim']}`"),
                ("各层声明", profile["layer_claims"]),
                ("第5层 5A/5B 边界", layer_5),
                ("枚举方法", enumeration["method"]),
                ("上游项目数", enumeration["upstream_item_count"]),
                ("快照边界", enumeration["snapshot_boundary"]),
                ("枚举说明", enumeration["notes"]),
                ("已知阻塞", blockers),
                ("最后复核", profile["last_reviewed_at"]),
            ]
        )
    else:
        profile_details = missing_layer("拆解范围声明")
    return f"""---
grdr_id: {json.dumps(source['id'], ensure_ascii=False)}
record_type: "source_catalog"
registry_version: {json.dumps(version)}
verification_status: {json.dumps(verification_code)}
canonical_url: {json.dumps(source['canonical_url'])}
---

# {source['name']}

<!-- Generated by scripts/build_catalog.py. Edit registry records, not this page. -->

{warning}

## 数据维度总览

{dimensions}

## 拆解范围与清单边界

{profile_details}

## 持久化数据库深度映射工程

{render_deep_map_projects(linked['deep_map_projects'])}

## 六层目录

### 第1层：发布/维护机构（Institution）

{render_institutions(linked['institutions'])}

### 第2层：数据库/数据源（Source）

{render_source(source)}

### 第3层：数据集（Dataset）

{render_datasets(linked['datasets'])}

### 第4层：数据库内部结构（DataStructure）

{render_data_structures(linked['data_structures'])}

### 第5层：数据元素与研究变量

#### 5A 数据结构元素（维度、测度、标识符、属性）

{render_data_elements(linked['data_elements'])}

#### 5B 可研究匹配变量

{variable_content if variable_content is not None else render_variables(linked['variables'])}

### 第6层：理论构念（Construct）

{construct_content if construct_content is not None else render_constructs(linked['constructs'])}

## 学科语义主干（多父节点知识图谱）

{render_semantic_nodes(linked['semantic_nodes'])}

## 访问方式与资源（旁路信息，不占内容层级）

{render_resources(linked['resources'])}

## 机器读取与维护

- 权威结构化记录：`registry/sources.jsonl` 中的 `{source['id']}`。
- 关联记录以页面中的 GRDR ID 为准，可通过 `scripts/grdr.py` 查询。
- 拆解范围记录：{value([item['id'] for item in linked['source_profiles']])}。
- 本页由 `scripts/build_catalog.py` 自动生成；不得把“尚未登记”解释成“上游不存在”。
"""


def render_root_block(context: dict[str, Any]) -> str:
    rows = [
        "当前注册表共收录 **{}** 个数据库/数据平台。每个数据库均有独立六层详情页；"
        "“待验证候选”仅表示已经登记，不表示其覆盖与使用条件已经核验。".format(len(context["sources"])),
        "",
        "| 数据库 | 发布/维护机构 | 主要领域 | 拆解范围 | 拆解阶段 | 严格完成度 | 验证状态 | 六层详情 |",
        "|---|---|---|---|---|---:|---|---|",
    ]
    for source in context["sources"]:
        linked = linked_records(source, context)
        publishers = "<br>".join(item["name"] for item in linked["institutions"])
        disciplines = "、".join(source["scope"]["disciplines"])
        slug = source_slug(source["id"])
        scope_mode, _inventory_claim = declared_scope(linked)
        rows.append(
            f"| [{source['name']}]({source['canonical_url']}) | {publishers or '未知 / 尚未登记'} | "
            f"{disciplines} | `{scope_mode}` | `{profile_stage(linked)}` | "
            f"{linked['deep_map_projects'][0]['progress']['strict_completion_percentage'] if linked['deep_map_projects'] else 0.0}% | {status(source)} | "
            f"[查看六层目录](catalog/sources/{slug}/README.md) |"
        )
    rows.extend(
        [
            "",
            "完整的人机双读索引见 [GRDR数据库目录](catalog/README.md)。",
        ]
    )
    return "\n".join(rows)


def render_catalog_index(context: dict[str, Any], version: str) -> str:
    counts: dict[str, int] = {}
    rows = [
        "| 数据库 | 发布/维护机构 | 数据集 | 数据结构 | 数据元素 | 变量 | 构念 | 访问资源 | 映射进度 | 严格完成度 | 拆解范围 | 拆解阶段 | 状态 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for source in context["sources"]:
        linked = linked_records(source, context)
        code = source["verification"]["status"]
        counts[code] = counts.get(code, 0) + 1
        publishers = "<br>".join(item["name"] for item in linked["institutions"])
        slug = source_slug(source["id"])
        scope_mode, _inventory_claim = declared_scope(linked)
        rows.append(
            f"| [{source['name']}](sources/{slug}/README.md) | {publishers or '未知 / 尚未登记'} | "
            f"{len(linked['datasets'])} | {len(linked['data_structures'])} | {len(linked['data_elements'])} | {len(linked['variables'])} | "
            f"{len(linked['constructs'])} | {len(linked['resources'])} | "
            f"{linked['deep_map_projects'][0]['progress']['mapping_percentage'] if linked['deep_map_projects'] else 0.0}% | "
            f"{linked['deep_map_projects'][0]['progress']['strict_completion_percentage'] if linked['deep_map_projects'] else 0.0}% | "
            f"`{scope_mode}` | `{profile_stage(linked)}` | {status(source)} |"
        )
    summary = "、".join(
        f"{STATUS_LABELS.get(code, code)} {count} 个" for code, count in sorted(counts.items())
    )
    return f"""# GRDR 数据库目录

<!-- Generated by scripts/build_catalog.py. Edit registry records, not this page. -->

目录版本：`{version}`。当前共收录 **{len(context['sources'])}** 个数据库；{summary}。

本目录同时面向研究人员和 AI Agent。每个数据库都按统一六层展开：

1. 发布/维护机构（Institution）
2. 数据库/数据源（Source）
3. 数据集（Dataset）
4. 数据库内部结构（DataStructure）
5. 数据元素与研究变量（5A DataElement / 5B Variable）
6. 理论构念（Construct）

API、CSV、批量下载、查询器、认证与许可作为访问旁路挂接到内容实体，不占六层主链。

“尚未登记”表示 GRDR 还没有完成该层的核验和录入，不表示上游数据库不存在相关内容。

## 数据库及六层完整度

{chr(10).join(rows)}

## 维护规则

- 新增任何 `registry/sources.jsonl` 记录后，必须运行 `python3 scripts/build_catalog.py`。
- 根 `README.md`、本索引和每个数据库的独立目录必须同时更新。
- 运行 `python3 scripts/build_catalog.py --check` 检查目录是否与结构化注册表一致。
- 生成页面只展示注册表中已有信息；未知字段必须保持“未知 / 尚未登记”。
"""


def replace_root_catalog(readme: str, block: str) -> str:
    if START_MARKER not in readme or END_MARKER not in readme:
        raise ValueError("README.md is missing GRDR catalog markers")
    prefix, remainder = readme.split(START_MARKER, 1)
    _old, suffix = remainder.split(END_MARKER, 1)
    return f"{prefix}{START_MARKER}\n{block.rstrip()}\n{END_MARKER}{suffix}"


def expected_outputs(context: dict[str, Any]) -> tuple[dict[Path, str], str]:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    outputs = {CATALOG / "README.md": render_catalog_index(context, version)}
    for source in context["sources"]:
        linked = linked_records(source, context)
        variable_content = render_variables(linked["variables"])
        construct_content = render_constructs(linked["constructs"])
        if len(linked["variables"]) > PAGED_LAYER_THRESHOLD:
            variable_content, pages = paginated_layer(
                source=source,
                records=linked["variables"],
                version=version,
                directory="variables",
                entity_label="变量",
                renderer=render_variable_catalog_page,
            )
            outputs.update(pages)
        if len(linked["constructs"]) > PAGED_LAYER_THRESHOLD:
            construct_content, pages = paginated_layer(
                source=source,
                records=linked["constructs"],
                version=version,
                directory="constructs",
                entity_label="理论构念",
                renderer=render_construct_catalog_page,
            )
            outputs.update(pages)
        outputs[SOURCE_CATALOG / source_slug(source["id"]) / "README.md"] = (
            render_source_page(
                source,
                context,
                version,
                linked=linked,
                variable_content=variable_content,
                construct_content=construct_content,
            )
        )
    root_readme = replace_root_catalog(
        ROOT_README.read_text(encoding="utf-8"), render_root_block(context)
    )
    return outputs, root_readme


def check(outputs: dict[Path, str], root_readme: str) -> int:
    errors = []
    for path, expected in outputs.items():
        if not path.is_file():
            errors.append(f"missing generated catalog file: {path.relative_to(ROOT)}")
        elif path.read_text(encoding="utf-8") != expected:
            errors.append(f"stale generated catalog file: {path.relative_to(ROOT)}")
    expected_pages = {path for path in outputs if path != CATALOG / "README.md"}
    actual_pages = set(SOURCE_CATALOG.glob("**/*.md")) if SOURCE_CATALOG.exists() else set()
    for path in sorted(actual_pages - expected_pages):
        errors.append(f"unexpected source catalog page: {path.relative_to(ROOT)}")
    if ROOT_README.read_text(encoding="utf-8") != root_readme:
        errors.append("README.md source catalog is stale")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"GRDR human catalog is current ({len(expected_pages)} source pages)")
    return 0


def write(outputs: dict[Path, str], root_readme: str) -> None:
    expected_pages = {path for path in outputs if path != CATALOG / "README.md"}
    actual_pages = set(SOURCE_CATALOG.glob("**/*.md")) if SOURCE_CATALOG.exists() else set()
    for stale in sorted(actual_pages - expected_pages):
        stale.unlink()
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    ROOT_README.write_text(root_readme, encoding="utf-8")
    print(f"Built GRDR human catalog ({len(outputs) - 1} source pages)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when generated catalog files are missing or stale")
    args = parser.parse_args()
    context = build_context()
    outputs, root_readme = expected_outputs(context)
    if args.check:
        return check(outputs, root_readme)
    write(outputs, root_readme)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
