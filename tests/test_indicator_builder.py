from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "grdr.py"


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
    write_jsonl(project_dir / "literature.jsonl", literature)
    write_jsonl(project_dir / "evidence_units.jsonl", evidence)
    write_jsonl(project_dir / "indicators.jsonl", indicators)
    write_jsonl(project_dir / "mappings.jsonl", mappings)
    return project_dir


class IndicatorBuilderTests(unittest.TestCase):
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
                env={key: value for key, value in os.environ.items() if key != "GRDR_ROOT"},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(json.loads(completed.stdout)["mapping_ready"])


if __name__ == "__main__":
    unittest.main()
