from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import distributed_runtime as runtime  # noqa: E402
import semantic_resolver as resolver  # noqa: E402


class DistributedRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.snapshot = self.root / "sources" / "synthetic" / "snapshots" / "r1"
        agent = self.snapshot / "agent"
        receipts = self.snapshot / "receipts"
        agent.mkdir(parents=True)
        receipts.mkdir(parents=True)
        index = agent / "grdr-agent-index.sqlite"
        connection = sqlite3.connect(index)
        connection.executescript(
            """
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE records (id TEXT PRIMARY KEY, entity_type TEXT, label TEXT, search_text TEXT, payload_json TEXT);
            CREATE TABLE relationships (id TEXT PRIMARY KEY, subject_id TEXT, predicate TEXT, object_id TEXT, payload_json TEXT);
            CREATE VIRTUAL TABLE record_search USING fts5(id UNINDEXED, label, search_text);
            """
        )
        connection.execute("INSERT INTO metadata VALUES ('source_id', 'grdr:source:synthetic')")
        construct = {"id": "grdr:construct:synthetic-population", "label": "Population", "name": "Population"}
        semantic_node = {
            "id": "grdr:semantic-node:synthetic-demography",
            "preferred_label": "Demography",
            "definition": "Scientific study of human populations.",
            "node_type": "discipline",
            "verification": {"status": "verified"},
        }
        dataset = {"id": "grdr:dataset:synthetic-main", "name": "Synthetic dataset"}
        structure = {
            "id": "grdr:data-structure:synthetic-main",
            "name": "Synthetic table",
            "dataset_ids": [dataset["id"]],
        }
        element = {
            "id": "grdr:data-element:synthetic-value",
            "name": "Observation value",
            "data_structure_ids": [structure["id"]],
        }
        variable = {
            "id": "grdr:variable:synthetic-population",
            "name": "POP",
            "label": "Resident population",
            "dataset_ids": [dataset["id"]],
            "construct_ids": [construct["id"]],
            "data_structure_ids": [structure["id"]],
            "role_candidates": ["outcome", "control"],
            "measurement": {"type": "administrative_measure"},
            "verification": {"status": "verified"},
            "join_keys": ["REF_AREA", "TIME_PERIOD"],
            "observation_unit": "country-year",
            "population": "residents",
            "unit": "persons",
            "temporal_resolution": "annual",
            "spatial_resolution": "global",
            "comparability": {"status": "comparable"},
            "source_native": {"measure_element_id": element["id"]},
        }
        for entity_type, item in (
            ("semantic_nodes", semantic_node),
            ("constructs", construct),
            ("datasets", dataset),
            ("data_structures", structure),
            ("data_elements", element),
            ("variables", variable),
        ):
            label = item.get("preferred_label", item.get("label", item.get("name")))
            connection.execute(
                "INSERT INTO records VALUES (?, ?, ?, ?, ?)",
                (item["id"], entity_type, label, json.dumps(item), json.dumps(item)),
            )
            connection.execute(
                "INSERT INTO record_search VALUES (?, ?, ?)",
                (item["id"], label, json.dumps(item)),
            )
        relationships = [
            ("grdr:relationship:synthetic-describes", semantic_node["id"], "describes", construct["id"]),
            ("grdr:relationship:synthetic-measures", variable["id"], "measures", construct["id"]),
            ("grdr:relationship:synthetic-operationalizes", element["id"], "operationalizes", variable["id"]),
            ("grdr:relationship:synthetic-defines", structure["id"], "defines", element["id"]),
            ("grdr:relationship:synthetic-organized", dataset["id"], "organized_as", structure["id"]),
        ]
        for relationship_id, subject_id, predicate, object_id in relationships:
            payload = {"id": relationship_id, "subject_id": subject_id, "predicate": predicate, "object_id": object_id}
            connection.execute(
                "INSERT INTO relationships VALUES (?, ?, ?, ?, ?)",
                (relationship_id, subject_id, predicate, object_id, json.dumps(payload)),
            )
        connection.commit()
        connection.close()
        descriptor = {
            "schema_version": "1.0.0",
            "protocol_version": "grdr-source-runtime/1.0",
            "source_id": "grdr:source:synthetic",
            "entrypoint": "synthetic_runtime.py",
            "agent_index": "grdr-agent-index.sqlite",
            "operations": ["self-test", "search", "resolve-variable", "fetch-variable"],
            "official_domains": ["example.org"],
        }
        (agent / "runtime.json").write_text(json.dumps(descriptor), encoding="utf-8")
        (agent / "runtime_audit.json").write_text(json.dumps({
            "source_id": "grdr:source:synthetic",
            "status": "ready",
            "variable_count": 1,
            "resolvable_variable_count": 1,
            "unresolved_variable_count": 0,
        }), encoding="utf-8")
        (agent / "synthetic_runtime.py").write_text(
            """import json, sys
print(json.dumps({\"operation\": sys.argv[1], \"status\": \"ok\", \"variable_id\": sys.argv[sys.argv.index(\"--variable-id\") + 1]}))
""",
            encoding="utf-8",
        )
        (receipts / "storage_receipt.json").write_text(json.dumps({
            "logical_content_fingerprint": "a" * 64,
        }), encoding="utf-8")
        self.card = {
            "schema_version": "2.0.0",
            "id": "grdr:source-archive:synthetic",
            "source_id": "grdr:source:synthetic",
            "repository": "https://github.com/example/synthetic",
            "latest_snapshot": "r1",
            "release": "https://github.com/example/synthetic/releases/tag/r1",
            "manifest": "https://github.com/example/synthetic/releases/download/r1/manifest.json",
            "archive_fingerprint": "a" * 64,
            "core_version": "3.3.0",
            "status": "complete",
            "updated_at": "2026-08-23T00:00:00Z",
            "runtime": {
                "protocol_version": "grdr-source-runtime/1.0",
                "asset": "synthetic-r1-agent-runtime.tar.gz",
                "entrypoint": "agent/synthetic_runtime.py",
                "agent_index": "agent/grdr-agent-index.sqlite",
                "operations": descriptor["operations"],
            },
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_status_search_resolve_and_invoke(self) -> None:
        status = runtime.local_snapshot_status(self.card, self.root)
        self.assertTrue(status["runtime_ready"])
        matches = runtime.distributed_variable_matches([self.card], self.root, construct="population")
        self.assertEqual([item["id"] for item in matches], ["grdr:variable:synthetic-population"])
        resolved = runtime.resolve_distributed_variable([self.card], matches[0]["id"], self.root)
        self.assertEqual(resolved["datasets"][0]["id"], "grdr:dataset:synthetic-main")
        invoked = runtime.invoke_source_runtime([self.card], matches[0]["id"], "resolve-variable", self.root)
        self.assertEqual(invoked["result"]["status"], "ok")

    def test_semantic_candidate_recall_and_graph_traversal(self) -> None:
        candidates = runtime.distributed_semantic_candidates(
            [self.card], ["resident population"], self.root, limit=5
        )
        self.assertEqual(candidates[0]["target_id"], "grdr:construct:synthetic-population")
        paths = runtime.distributed_semantic_paths(
            [self.card],
            "grdr:semantic-node:synthetic-demography",
            "semantic_node",
            self.root,
        )
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0]["construct_id"], "grdr:construct:synthetic-population")
        self.assertEqual(paths[0]["variable_id"], "grdr:variable:synthetic-population")
        self.assertEqual(paths[0]["data_element_ids"], ["grdr:data-element:synthetic-value"])
        self.assertEqual(paths[0]["dataset_ids"], ["grdr:dataset:synthetic-main"])

    def test_research_indicator_resolves_through_five_runtime_layers(self) -> None:
        project_dir = self.root / "research-project"
        project_dir.mkdir()
        project_id = "grdr:research-project:synthetic-population"
        indicator_id = "grdr:research-indicator:synthetic-population-total"
        (project_dir / "project.json").write_text(json.dumps({
            "schema_version": "0.1.0",
            "id": project_id,
            "title": "Synthetic population",
            "research_question": "What is the resident population?",
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
                "corpus_boundary": {"status": "exploratory_only", "reviewer": None, "reviewed_at": None, "notes": "fixture"},
                "indicator_framework": {"status": "pending", "reviewer": None, "reviewed_at": None, "notes": None},
                "contested_mappings": {"status": "not_required", "reviewer": None, "reviewed_at": None, "notes": None},
            },
            "agent_provenance": {"executor": "ai_agent", "model": "fixture-agent", "workflow_version": "3.4.0"},
            "created_at": "2026-08-23T00:00:00+00:00",
            "updated_at": "2026-08-23T00:00:00+00:00",
        }), encoding="utf-8")
        indicator = {
            "schema_version": "0.1.0",
            "id": indicator_id,
            "project_id": project_id,
            "name": "Resident population",
            "parent_indicator_id": None,
            "node_type": "operational_requirement",
            "definition": "Number of residents in a country and year.",
            "is_leaf": True,
            "provenance_type": "topic_scaffold",
            "evidence_unit_ids": [],
            "synonyms": ["Population"],
            "operational_spec": {
                "unit": "persons",
                "denominator": None,
                "population": "residents",
                "observation_unit": "country-year",
                "spatial_scope": "global",
                "temporal_scope": "annual",
                "direction": "higher_more",
                "proxy_allowed": False,
            },
            "review_status": "agent_candidate",
        }
        for filename in ("literature.jsonl", "evidence_units.jsonl", "mappings.jsonl", "data_gaps.jsonl"):
            (project_dir / filename).write_text("", encoding="utf-8")
        (project_dir / "indicators.jsonl").write_text(json.dumps(indicator) + "\n", encoding="utf-8")
        (project_dir / "workflow.json").write_text(json.dumps({
            "schema_version": "0.1.0",
            "project_id": project_id,
            "workflow_status": "ready_to_match",
            "current_step": "matching",
            "matching_attempt": 0,
            "gap_expansion_round": 0,
            "last_operation": "fixture",
            "next_actions": ["prepare-semantic-candidates"],
            "history": [{"timestamp": "2026-08-23T00:00:00+00:00", "operation": "fixture", "summary": "Created fixture."}],
            "created_at": "2026-08-23T00:00:00+00:00",
            "updated_at": "2026-08-23T00:00:00+00:00",
        }), encoding="utf-8")

        with patch("semantic_resolver.source_cards", return_value=[self.card]):
            recalled = resolver.prepare_semantic_candidates(project_dir, limit=5, elements_root=self.root)
            self.assertGreater(recalled["candidate_count"], 0)
            candidates = resolver.read_jsonl(project_dir / "semantic_candidates.jsonl")
            construct = next(item for item in candidates if item["target_id"] == "grdr:construct:synthetic-population")
            decision_file = project_dir / "decisions.jsonl"
            decision_file.write_text(json.dumps({
                "indicator_id": indicator_id,
                "target_type": "construct",
                "target_id": construct["target_id"],
                "mapping_relation": "exact_match",
                "alignment_role": "primary",
                "confidence": 0.99,
                "rationale": "The indicator and stored construct both denote resident population counts.",
            }) + "\n", encoding="utf-8")
            aligned = resolver.record_semantic_alignments(project_dir, decision_file)
            self.assertEqual(aligned["alignment_count"], 1)
            traversed = resolver.traverse_semantic_paths(project_dir, elements_root=self.root)
            self.assertEqual(traversed["path_count"], 1)
            matched = resolver.perform_semantic_matching(project_dir, elements_root=self.root)
            self.assertEqual(matched["outcomes"], {"direct_match": 1})
            explained = resolver.explain_indicator_match(project_dir, indicator_id)
            self.assertEqual(explained["mapping"]["semantic_path_ids"], [resolver.read_jsonl(project_dir / "semantic_paths.jsonl")[0]["id"]])
            fetched = resolver.fetch_indicator_data(
                project_dir,
                indicator_id,
                elements_root=self.root,
                extra_args=["--dry-run"],
            )
            self.assertEqual(fetched["source_call"]["result"]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
