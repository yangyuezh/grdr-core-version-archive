from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import distributed_runtime as runtime  # noqa: E402
import research_project as research  # noqa: E402
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
        logical_files = []
        for item in runtime.snapshot_inventory(self.snapshot):
            logical_files.append({**item, "locations": ["elements"]})
        logical_fingerprint = runtime.fingerprint(logical_files)
        manifest = {
            "schema_version": "3.0.0",
            "source_id": "grdr:source:synthetic",
            "snapshot_id": "r1",
            "logical_files": logical_files,
            "logical_content_fingerprint": logical_fingerprint,
            "snapshot_profile": {
                "observation_replication": {"mode": "federated_on_demand"},
                "observation_placement": {
                    "locations": ["official_upstream"],
                    "cache": {
                        "mode": "on_demand",
                        "research_project_snapshots": True,
                        "root": "research_project",
                    },
                },
            },
            "external_observation_locations": [{
                "type": "official_upstream",
                "uri": "https://example.org/api",
                "local_path": None,
                "verification": "official_runtime_verified",
                "logical_paths": [],
                "content_fingerprint": "b" * 64,
            }],
        }
        (receipts / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        receipt = {"logical_content_fingerprint": logical_fingerprint}
        receipt["receipt_fingerprint"] = runtime.fingerprint(receipt)
        (receipts / "storage_receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        self.card = {
            "schema_version": "2.0.0",
            "id": "grdr:source-archive:synthetic",
            "source_id": "grdr:source:synthetic",
            "repository": "https://github.com/example/synthetic",
            "latest_snapshot": "r1",
            "release": "https://github.com/example/synthetic/releases/tag/r1",
            "manifest": "https://github.com/example/synthetic/releases/download/r1/manifest.json",
            "archive_fingerprint": logical_fingerprint,
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

    def write_history_registry(self) -> Path:
        registry = self.root / "registry"
        registry.mkdir(exist_ok=True)
        records = {
            "datasets.jsonl": [
                {
                    "id": "grdr:dataset:synthetic-main",
                    "name": "Synthetic dataset",
                    "source_ids": ["grdr:source:synthetic"],
                }
            ],
            "constructs.jsonl": [
                {
                    "id": "grdr:construct:synthetic-population-r0",
                    "label": "Resident population",
                    "definition": "Historical resident population definition.",
                },
                {
                    "id": "grdr:construct:synthetic-population",
                    "label": "Resident population",
                    "definition": "Current resident population definition.",
                },
            ],
            "variables.jsonl": [
                {
                    "id": "grdr:variable:synthetic-population-r0",
                    "name": "POP",
                    "label": "Resident population",
                    "dataset_ids": ["grdr:dataset:synthetic-main"],
                    "construct_ids": ["grdr:construct:synthetic-population-r0"],
                    "role_candidates": ["outcome", "control"],
                    "observation_unit": "country-year",
                    "unit": "persons",
                    "measurement": {"type": "administrative_measure"},
                    "comparability": {"status": "historical"},
                    "join_keys": ["REF_AREA", "TIME_PERIOD"],
                    "verification": {"status": "verified"},
                },
                {
                    "id": "grdr:variable:synthetic-population",
                    "name": "POP",
                    "label": "Resident population",
                    "dataset_ids": ["grdr:dataset:synthetic-main"],
                    "construct_ids": ["grdr:construct:synthetic-population"],
                    "role_candidates": ["outcome", "control"],
                    "observation_unit": "country-year",
                    "unit": "persons",
                    "measurement": {"type": "administrative_measure"},
                    "comparability": {"status": "comparable"},
                    "join_keys": ["REF_AREA", "TIME_PERIOD"],
                    "verification": {"status": "verified"},
                },
            ],
            "semantic_nodes.jsonl": [],
            "relationships.jsonl": [],
            "source_archives.jsonl": [self.card],
        }
        for filename, values in records.items():
            (registry / filename).write_text(
                "".join(json.dumps(value) + "\n" for value in values),
                encoding="utf-8",
            )
        return registry

    def test_status_search_resolve_and_invoke(self) -> None:
        status = runtime.local_snapshot_status(self.card, self.root)
        self.assertTrue(status["runtime_ready"])
        matches = runtime.distributed_variable_matches([self.card], self.root, construct="population")
        self.assertEqual([item["id"] for item in matches], ["grdr:variable:synthetic-population"])
        resolved = runtime.resolve_distributed_variable([self.card], matches[0]["id"], self.root)
        self.assertEqual(resolved["datasets"][0]["id"], "grdr:dataset:synthetic-main")
        invoked = runtime.invoke_source_runtime([self.card], matches[0]["id"], "resolve-variable", self.root)
        self.assertEqual(invoked["result"]["status"], "ok")
        self.assertEqual(invoked["observation_route"]["selected_route"], "official_upstream")

    def test_verified_runtime_cache_invalidates_after_file_mutation(self) -> None:
        first = runtime.local_snapshot_status(self.card, self.root, verify=True)
        self.assertTrue(first["runtime_ready"])
        second = runtime.local_snapshot_status(self.card, self.root, verify=True)
        self.assertTrue(second["verification_cache_hit"])
        entrypoint = self.snapshot / "agent" / "synthetic_runtime.py"
        entrypoint.write_text(entrypoint.read_text(encoding="utf-8") + "# tampered\n", encoding="utf-8")
        invalid = runtime.local_snapshot_status(self.card, self.root, verify=True)
        self.assertFalse(invalid["runtime_ready"])
        self.assertTrue(any("inventory differs" in item for item in invalid["errors"]))

    def test_persisted_elements_root_and_environment_override(self) -> None:
        state = self.root / "state"
        state.mkdir()
        configured = self.root
        (state / "config.json").write_text(
            json.dumps({"schema_version": "1.0.0", "elements_root": str(configured)}),
            encoding="utf-8",
        )
        with patch.dict(
            os.environ,
            {"GRDR_STATE_ROOT": str(state), "GRDR_ELEMENTS_ROOT": ""},
            clear=False,
        ):
            self.assertEqual(runtime.elements_root(), configured.resolve())
            override = self.root / "override"
            os.environ["GRDR_ELEMENTS_ROOT"] = str(override)
            self.assertEqual(runtime.elements_root(), override.resolve())

    def test_variable_cli_prefers_latest_callable_snapshot(self) -> None:
        self.write_history_registry()
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "grdr.py"),
                "search-variables",
                "--construct",
                "population",
                "--limit",
                "10",
            ],
            cwd=ROOT,
            env={
                **os.environ,
                "GRDR_STATE_ROOT": str(self.root),
                "GRDR_ELEMENTS_ROOT": str(self.root),
            },
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["snapshot_policy"], "latest_callable")
        self.assertEqual(payload["callable_source_count"], 1)
        self.assertEqual(
            [item["id"] for item in payload["results"]],
            ["grdr:variable:synthetic-population"],
        )
        self.assertEqual(payload["results"][0]["snapshot"]["snapshot_id"], "r1")

    def test_variable_cli_history_is_explicit_and_complete(self) -> None:
        self.write_history_registry()
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "grdr.py"),
                "search-variables",
                "--construct",
                "population",
                "--snapshot-policy",
                "history",
                "--limit",
                "10",
            ],
            cwd=ROOT,
            env={
                **os.environ,
                "GRDR_STATE_ROOT": str(self.root),
                "GRDR_ELEMENTS_ROOT": str(self.root),
            },
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["snapshot_policy"], "history")
        self.assertEqual(
            [item["id"] for item in payload["results"]],
            [
                "grdr:variable:synthetic-population",
                "grdr:variable:synthetic-population-r0",
            ],
        )

    def test_on_demand_fetch_seals_research_project_snapshot(self) -> None:
        project = self.root / "research-project"
        project.mkdir()
        (project / "workflow.json").write_text("{}", encoding="utf-8")
        result = runtime.research_project_data_snapshot(
            [self.card],
            "grdr:variable:synthetic-population",
            project,
            self.root,
            ["--country", "840"],
        )
        snapshot = result["research_data_snapshot"]
        capture = Path(snapshot["path"])
        self.assertTrue((capture / "manifest.json").is_file())
        self.assertTrue((capture / "data" / "runtime_result.json").is_file())
        self.assertTrue((project / "data_snapshot_index.jsonl").is_file())
        manifest = json.loads((capture / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_id"], "grdr:source:synthetic")
        self.assertEqual(manifest["source_snapshot_id"], "r1")
        self.assertEqual(manifest["variable_id"], "grdr:variable:synthetic-population")

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

    def test_latest_callable_policy_excludes_historical_canonical_source_records(self) -> None:
        registry = self.write_history_registry()

        with patch.object(resolver, "REGISTRY_ROOT", registry):
            history = resolver.central_semantic_candidates(["Resident population"], 10)
            self.assertEqual(
                {item["target_id"] for item in history},
                {
                    "grdr:construct:synthetic-population-r0",
                    "grdr:construct:synthetic-population",
                },
            )
            current_only = resolver.central_semantic_candidates(
                ["Resident population"],
                10,
                exclude_source_ids={"grdr:source:synthetic"},
            )
            self.assertEqual(current_only, [])

        callable_candidates = runtime.distributed_semantic_candidates(
            [self.card], ["Resident population"], self.root, limit=10
        )
        self.assertEqual(
            [item["target_id"] for item in callable_candidates],
            ["grdr:construct:synthetic-population"],
        )
        self.assertEqual(callable_candidates[0]["snapshot"]["snapshot_id"], "r1")

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

        registry = self.write_history_registry()
        with (
            patch("semantic_resolver.source_cards", return_value=[self.card]),
            patch.object(resolver, "REGISTRY_ROOT", registry),
            patch.object(research, "REGISTRY_ROOT", registry),
        ):
            recalled = resolver.prepare_semantic_candidates(project_dir, limit=5, elements_root=self.root)
            self.assertGreater(recalled["candidate_count"], 0)
            self.assertEqual(recalled["snapshot_policy"], "latest_callable")
            self.assertEqual(recalled["callable_source_count"], 1)
            candidates = resolver.read_jsonl(project_dir / "semantic_candidates.jsonl")
            self.assertNotIn("grdr:construct:synthetic-population-r0", {item["target_id"] for item in candidates})
            construct = next(item for item in candidates if item["target_id"] == "grdr:construct:synthetic-population")
            self.assertEqual(construct["snapshot"]["snapshot_id"], "r1")
            historical = resolver.prepare_semantic_candidates(
                project_dir,
                limit=5,
                elements_root=self.root,
                snapshot_policy="history",
                replace=True,
            )
            self.assertEqual(historical["snapshot_policy"], "history")
            history_candidates = resolver.read_jsonl(project_dir / "semantic_candidates.jsonl")
            self.assertIn(
                "grdr:construct:synthetic-population-r0",
                {item["target_id"] for item in history_candidates},
            )
            current = [
                item
                for item in history_candidates
                if item["target_id"] == "grdr:construct:synthetic-population"
            ]
            self.assertEqual(len(current), 1)
            self.assertEqual(current[0]["snapshot"]["snapshot_id"], "r1")
            resolver.prepare_semantic_candidates(
                project_dir,
                limit=5,
                elements_root=self.root,
                snapshot_policy="latest_callable",
                replace=True,
            )
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

            superseded = {**self.card, "latest_snapshot": "r2"}
            (registry / "source_archives.jsonl").write_text(
                json.dumps(superseded) + "\n",
                encoding="utf-8",
            )
            status = research.research_project_status(project_dir)
            self.assertEqual(status["workflow_status"], "needs_rerun")
            self.assertEqual(status["mapping_snapshot_health"]["status"], "stale")
            self.assertFalse(status["exploratory_matching_complete"])
            self.assertEqual(status["leaf_match_coverage"]["matched"], 0)
            with self.assertRaisesRegex(ValueError, "indicator mapping is stale"):
                resolver.fetch_indicator_data(
                    project_dir,
                    indicator_id,
                    elements_root=self.root,
                    extra_args=["--dry-run"],
                )
            resumed = research.resume_research_project(project_dir)
            self.assertEqual(resumed["workflow_status"], "ready_to_match", resumed)
            self.assertEqual(
                resumed["next_actions"],
                ["prepare-semantic-candidates --replace"],
            )


if __name__ == "__main__":
    unittest.main()
