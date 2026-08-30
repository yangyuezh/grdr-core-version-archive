from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "grdr.py"
sys.path.insert(0, str(ROOT / "scripts"))

from research_project import perform_matching  # noqa: E402


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
        encoding="utf-8",
    )


def make_project(parent: Path, with_evidence: bool = True) -> Path:
    project_dir = parent / "population-project"
    project_dir.mkdir()
    project_id = "grdr:research-project:population-project"
    evidence_ids = ["grdr:evidence-unit:population-definition"] if with_evidence else []
    project = {
        "schema_version": "0.1.0",
        "id": project_id,
        "title": "Population scale research",
        "research_question": "How does population scale relate to the outcome?",
        "evidence_stage": "mapping_ready",
        "analysis_methods": ["theory_deduction", "content_analysis"],
        "corpus_protocol": {
            "search_strategy": "Declared fixture strategy",
            "sources": ["User-provided corpus"],
            "inclusion_criteria": ["Defines the focal construct"],
            "exclusion_criteria": ["No relevant measurement content"],
            "date_boundary": "Through 2026-08-16",
            "languages": ["en"],
            "saturation_rule": "Stop after no new construct dimensions emerge",
        },
        "human_gates": {
            "corpus_boundary": {
                "status": "approved",
                "reviewer": "test-reviewer",
                "reviewed_at": "2026-08-16T12:00:00Z",
                "notes": "Fixture approval",
            },
            "indicator_framework": {
                "status": "approved",
                "reviewer": "test-reviewer",
                "reviewed_at": "2026-08-16T12:05:00Z",
                "notes": "Fixture approval",
            },
            "contested_mappings": {
                "status": "not_required",
                "reviewer": None,
                "reviewed_at": None,
                "notes": "Direct match only",
            },
        },
        "agent_provenance": {
            "executor": "hybrid",
            "model": "test-agent",
            "workflow_version": "0.4.0",
        },
        "created_at": "2026-08-16T11:00:00Z",
        "updated_at": "2026-08-16T12:10:00Z",
    }
    literature = [
        {
            "schema_version": "0.1.0",
            "id": "grdr:literature-document:population-study",
            "project_id": project_id,
            "study_id": "fixture-study-1",
            "title": "Population measurement study",
            "authors": ["Test Author"],
            "year": 2025,
            "doi": None,
            "url": "https://example.org/population-study",
            "citation": "Test Author. (2025). Population measurement study.",
            "access_basis": "user_provided",
            "full_text_status": "available",
            "decision": "included",
            "exclusion_reason": None,
            "sections_present": ["abstract", "methods", "references"],
            "reference_list_processed": True,
            "quality_appraisal": {"status": "low_concern", "notes": None},
        }
    ]
    evidence = []
    if with_evidence:
        evidence.append(
            {
                "schema_version": "0.1.0",
                "id": "grdr:evidence-unit:population-definition",
                "project_id": project_id,
                "document_id": "grdr:literature-document:population-study",
                "evidence_role": "operationalization",
                "section": "methods",
                "locator": "Methods, paragraph 2",
                "excerpt": None,
                "paraphrase": "The study operationalizes population as the total resident count.",
                "review_status": "agent_extracted",
            }
        )
    indicators = [
        {
            "schema_version": "0.1.0",
            "id": "grdr:research-indicator:total-population",
            "project_id": project_id,
            "name": "Total population",
            "parent_indicator_id": None,
            "node_type": "operational_requirement",
            "definition": "Total resident population in the observation unit.",
            "is_leaf": True,
            "provenance_type": "source_reported",
            "evidence_unit_ids": evidence_ids,
            "synonyms": ["population size"],
            "operational_spec": {
                "unit": "people",
                "denominator": None,
                "population": "residents",
                "observation_unit": "country-year",
                "spatial_scope": "global",
                "temporal_scope": "annual",
                "direction": "higher_more",
                "proxy_allowed": False,
            },
            "review_status": "approved_for_mapping",
        }
    ]
    mappings = [
        {
            "schema_version": "0.1.0",
            "id": "grdr:indicator-mapping:total-population-registry-gap",
            "project_id": project_id,
            "indicator_id": "grdr:research-indicator:total-population",
            "mapping_status": "not_found_registry_snapshot",
            "variable_ids": [],
            "transformation": None,
            "fit": {
                "construct": "exact",
                "population": "exact",
                "unit": "exact",
                "time": "exact",
                "space": "exact",
            },
            "human_review_required": False,
            "review_status": "not_required",
            "notes": "The isolated Core registry is intentionally empty.",
        }
    ]
    (project_dir / "project.json").write_text(
        json.dumps(project, ensure_ascii=False), encoding="utf-8"
    )
    workflow = {
        "schema_version": "0.1.0",
        "project_id": project_id,
        "workflow_status": "ready_to_match",
        "current_step": "matching",
        "matching_attempt": 0,
        "gap_expansion_round": 0,
        "last_operation": "test-fixture",
        "next_actions": ["match-indicators"],
        "history": [
            {
                "timestamp": "2026-08-16T12:10:00Z",
                "operation": "test-fixture",
                "summary": "Prepared an approved mapping fixture.",
            }
        ],
        "created_at": "2026-08-16T11:00:00Z",
        "updated_at": "2026-08-16T12:10:00Z",
    }
    write_jsonl(project_dir / "literature.jsonl", literature)
    write_jsonl(project_dir / "evidence_units.jsonl", evidence)
    write_jsonl(project_dir / "indicators.jsonl", indicators)
    write_jsonl(project_dir / "mappings.jsonl", mappings)
    (project_dir / "workflow.json").write_text(
        json.dumps(workflow, ensure_ascii=False), encoding="utf-8"
    )
    write_jsonl(project_dir / "data_gaps.jsonl", [])
    return project_dir


def isolated_cli_environment(parent: Path, *, omit_grdr_root: bool = False) -> dict[str, str]:
    state = parent / "grdr-state"
    registry = state / "registry"
    registry.mkdir(parents=True)
    for filename in ("variables.jsonl", "source_archives.jsonl"):
        (registry / filename).write_text("", encoding="utf-8")
    environment = dict(os.environ)
    environment["GRDR_STATE_ROOT"] = str(state)
    if omit_grdr_root:
        environment.pop("GRDR_ROOT", None)
    return environment


class IndicatorBuilderTests(unittest.TestCase):
    def test_matching_uses_distributed_runtime_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = make_project(Path(temporary))
            indicators = [json.loads(line) for line in (project_dir / "indicators.jsonl").read_text().splitlines()]
            indicators[0]["name"] = "Synthetic resident count"
            indicators[0]["synonyms"] = []
            write_jsonl(project_dir / "indicators.jsonl", indicators)
            write_jsonl(project_dir / "mappings.jsonl", [])
            construct = {
                "id": "grdr:construct:synthetic-resident-count",
                "name": "Synthetic resident count",
                "aliases": [],
                "verification": {"status": "verified"},
            }
            variable = {
                "id": "grdr:variable:synthetic-resident-count",
                "name": "SYN_POP",
                "label": "Synthetic resident count",
                "construct_ids": [construct["id"]],
                "verification": {"status": "verified"},
                "population": "residents",
                "unit": "people",
                "temporal_resolution": "annual",
                "spatial_resolution": "global",
                "_grdr_snapshot": {
                    "source_id": "grdr:source:synthetic-distributed",
                    "snapshot_id": "r1",
                },
            }

            def distributed_records(_cards, entity_type):
                return {"constructs": [construct], "variables": [variable]}.get(entity_type, [])

            with patch("research_project.distributed.distributed_entity_records", side_effect=distributed_records):
                result = perform_matching(project_dir)
            self.assertEqual(result["outcomes"], {"direct_match": 1})
            self.assertEqual(result["mappings"][0]["variable_ids"], [variable["id"]])
            self.assertIn("distributed snapshot", result["mappings"][0]["notes"])

    def test_topic_only_project_stays_exploratory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = Path(temporary) / "topic-scaffold"
            project_dir.mkdir()
            project_id = "grdr:research-project:topic-scaffold"
            project = {
                "schema_version": "0.1.0",
                "id": project_id,
                "title": "Exploratory topic",
                "research_question": "What dimensions might explain the outcome?",
                "evidence_stage": "topic_scaffold",
                "analysis_methods": ["theory_deduction"],
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
                    "corpus_boundary": {
                        "status": "exploratory_only",
                        "reviewer": None,
                        "reviewed_at": None,
                        "notes": "No literature corpus supplied",
                    },
                    "indicator_framework": {
                        "status": "pending",
                        "reviewer": None,
                        "reviewed_at": None,
                        "notes": None,
                    },
                    "contested_mappings": {
                        "status": "not_required",
                        "reviewer": None,
                        "reviewed_at": None,
                        "notes": None,
                    },
                },
                "agent_provenance": {
                    "executor": "ai_agent",
                    "model": "test-agent",
                    "workflow_version": "0.4.0",
                },
                "created_at": "2026-08-16T11:00:00Z",
                "updated_at": "2026-08-16T11:00:00Z",
            }
            indicator = {
                "schema_version": "0.1.0",
                "id": "grdr:research-indicator:candidate-context",
                "project_id": project_id,
                "name": "Candidate context",
                "parent_indicator_id": None,
                "node_type": "construct",
                "definition": "A provisional context dimension.",
                "is_leaf": True,
                "provenance_type": "topic_scaffold",
                "evidence_unit_ids": [],
                "synonyms": [],
                "operational_spec": None,
                "review_status": "agent_candidate",
            }
            (project_dir / "project.json").write_text(
                json.dumps(project), encoding="utf-8"
            )
            write_jsonl(project_dir / "literature.jsonl", [])
            write_jsonl(project_dir / "evidence_units.jsonl", [])
            write_jsonl(project_dir / "indicators.jsonl", [indicator])
            write_jsonl(project_dir / "mappings.jsonl", [])
            completed = subprocess.run(
                [sys.executable, str(CLI), "audit-indicator-project", str(project_dir)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=isolated_cli_environment(Path(temporary)),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertFalse(payload["formal_evidence_ready"])
            self.assertFalse(payload["mapping_ready"])

    def test_valid_formal_project_is_mapping_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = make_project(Path(temporary))
            completed = subprocess.run(
                [sys.executable, str(CLI), "audit-indicator-project", str(project_dir)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=isolated_cli_environment(Path(temporary)),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["errors"], [])
            self.assertTrue(payload["formal_evidence_ready"])
            self.assertTrue(payload["mapping_ready"])
            self.assertEqual(payload["counts"]["leaf_indicators"], 1)

    def test_formal_indicator_without_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = make_project(Path(temporary), with_evidence=False)
            completed = subprocess.run(
                [sys.executable, str(CLI), "audit-indicator-project", str(project_dir)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env=isolated_cli_environment(Path(temporary)),
            )
            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            self.assertFalse(payload["formal_evidence_ready"])
            self.assertTrue(
                any("has no literature evidence" in item for item in payload["errors"])
            )

    def test_skill_wrapper_discovers_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project_dir = make_project(Path(temporary))
            wrapper = (
                ROOT
                / "skill"
                / "grdr-indicator-builder"
                / "scripts"
                / "audit_project.py"
            )
            completed = subprocess.run(
                [sys.executable, str(wrapper), str(project_dir)],
                cwd=ROOT.parent,
                capture_output=True,
                text=True,
                env=isolated_cli_environment(
                    Path(temporary), omit_grdr_root=True
                ),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(json.loads(completed.stdout)["mapping_ready"])


if __name__ == "__main__":
    unittest.main()
