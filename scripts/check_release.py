#!/usr/bin/env python3
"""Check that the local GRDR release metadata is internally consistent."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    errors: list[str] = []

    if not SEMVER.fullmatch(version):
        errors.append(f"VERSION is not valid Semantic Versioning: {version!r}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        errors.append(f"CHANGELOG.md has no entry for {version}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if f"Version `{version}`" not in readme:
        errors.append(f"README.md does not identify Version `{version}`")

    skill = ROOT / "skill" / "grdr" / "SKILL.md"
    if not skill.is_file():
        errors.append("version-controlled Skill bundle is missing")
    elif not skill.read_text(encoding="utf-8").startswith("---\nname: grdr\n"):
        errors.append("version-controlled Skill identity is not 'grdr'")

    legacy_skill = ROOT / "skill" / "global-research-data-warehouse"
    if legacy_skill.exists():
        errors.append("legacy global-research-data-warehouse Skill bundle still exists")

    for deep_map_skill in (
        "grdr-plan-database-deep-map",
        "grdr-execute-database-deep-map",
        "grdr-archive-database-deep-map",
    ):
        skill_path = ROOT / "skill" / deep_map_skill / "SKILL.md"
        if not skill_path.is_file():
            errors.append(f"version-controlled {deep_map_skill} Skill is missing")
        elif not skill_path.read_text(encoding="utf-8").startswith(
            f"---\nname: {deep_map_skill}\n"
        ):
            errors.append(f"version-controlled Skill identity is not {deep_map_skill!r}")

    if (ROOT / "skill" / "grdr-deep-map-database").exists():
        errors.append("superseded monolithic grdr-deep-map-database Skill bundle still exists")

    if (ROOT / "skill" / "grdr-source-profiler").exists():
        errors.append("superseded grdr-source-profiler Skill bundle still exists")

    indicator_skill = ROOT / "skill" / "grdr-indicator-builder" / "SKILL.md"
    if not indicator_skill.is_file():
        errors.append("version-controlled grdr-indicator-builder Skill is missing")
    elif not indicator_skill.read_text(encoding="utf-8").startswith(
        "---\nname: grdr-indicator-builder\n"
    ):
        errors.append("version-controlled indicator Skill identity is not 'grdr-indicator-builder'")

    for required_path in [
        ROOT / "schemas" / "research_workflow.schema.json",
        ROOT / "schemas" / "data_gap.schema.json",
        ROOT / "schemas" / "data_structure.schema.json",
        ROOT / "schemas" / "semantic_node.schema.json",
        ROOT / "schemas" / "database_deep_map_project.schema.json",
        ROOT / "schemas" / "database_deep_map_unit.schema.json",
        ROOT / "schemas" / "database_deep_map_phase_update.schema.json",
        ROOT / "schemas" / "database_deep_map_stage_update.schema.json",
        ROOT / "schemas" / "database_deep_map_spine_update.schema.json",
        ROOT / "schemas" / "database_deep_map_intake.schema.json",
        ROOT / "schemas" / "database_deep_map_plan.schema.json",
        ROOT / "schemas" / "database_deep_map_check.schema.json",
        ROOT / "schemas" / "database_deep_map_check_update.schema.json",
        ROOT / "schemas" / "database_deep_map_staging_manifest.schema.json",
        ROOT / "schemas" / "database_deep_map_archive_package.schema.json",
        ROOT / "schemas" / "database_deep_map_archive_receipt.schema.json",
        ROOT / "schemas" / "database_route_contracts.schema.json",
        ROOT / "config" / "database_route_contracts.json",
        ROOT / "requirements-validation.txt",
        ROOT / "registry" / "data_structures.jsonl",
        ROOT / "registry" / "semantic_nodes.jsonl",
        ROOT / "scripts" / "research_project.py",
        ROOT / "scripts" / "database_deep_map.py",
        ROOT / "scripts" / "database_deep_map_planner.py",
        ROOT / "deep_map_projects" / "undata" / "project.json",
        ROOT / "deep_map_projects" / "undata" / "units.jsonl",
        ROOT / "deep_map_projects" / "undata" / "checks.jsonl",
        ROOT / "deep_map_projects" / "undata" / "staging_manifest.json",
        ROOT / "docs" / "DATABASE_DEEP_MAP_WORKFLOW.md",
        ROOT / "skill" / "grdr-plan-database-deep-map" / "references" / "diagnostic-matrix.md",
        ROOT / "skill" / "grdr-plan-database-deep-map" / "references" / "database-archetypes.md",
        ROOT / "skill" / "grdr-plan-database-deep-map" / "references" / "route-contracts.md",
        ROOT / "skill" / "grdr-plan-database-deep-map" / "references" / "lifecycle-boundaries.md",
        ROOT / "skill" / "grdr-execute-database-deep-map" / "references" / "engineering-contract.md",
        ROOT / "skill" / "grdr-execute-database-deep-map" / "references" / "within-stage-enumeration.md",
        ROOT / "skill" / "grdr-execute-database-deep-map" / "references" / "exception-recovery.md",
        ROOT / "skill" / "grdr-execute-database-deep-map" / "references" / "phase-update.example.json",
        ROOT / "skill" / "grdr-execute-database-deep-map" / "references" / "stage-update.example.json",
        ROOT / "skill" / "grdr-execute-database-deep-map" / "references" / "spine-update.example.json",
        ROOT / "skill" / "grdr-execute-database-deep-map" / "references" / "check-update.example.json",
        ROOT / "skill" / "grdr-execute-database-deep-map" / "scripts" / "inspect_sdmx.py",
        ROOT / "skill" / "grdr-execute-database-deep-map" / "scripts" / "audit_execution.py",
        ROOT / "skill" / "grdr-archive-database-deep-map" / "references" / "archive-contract.md",
        ROOT / "skill" / "grdr-archive-database-deep-map" / "references" / "completion-contract.md",
    ]:
        if not required_path.is_file():
            errors.append(f"required research workflow file is missing: {required_path.relative_to(ROOT)}")

    cli = (ROOT / "scripts" / "grdr.py").read_text(encoding="utf-8")
    for command in [
        "list-database-route-modules",
        "plan-database-deep-map",
        "audit-database-deep-map-plan",
        "start-database-deep-map",
        "upgrade-database-deep-map",
        "database-deep-map-status",
        "resume-database-deep-map",
        "record-database-deep-map-phase",
        "record-database-deep-map-stage",
        "record-database-deep-map-spine",
        "record-database-deep-map-check",
        "record-database-deep-map-execution-batch",
        "record-database-deep-map-human-gate",
        "stage-database-deep-map-records",
        "audit-database-deep-map",
        "audit-database-deep-map-execution",
        "prepare-database-deep-map-archive",
        "audit-database-deep-map-archive",
        "database-deep-map-archive-status",
        "archive-database-deep-map",
        "complete-database-deep-map",
        "start-research-project",
        "research-project-status",
        "approve-human-gate",
        "resume-research-project",
        "match-indicators",
        "expand-from-data-gaps",
        "rerun-matching",
    ]:
        if f'"{command}"' not in cli:
            errors.append(f"GRDR CLI is missing required command: {command}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"GRDR release metadata is consistent for v{version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
