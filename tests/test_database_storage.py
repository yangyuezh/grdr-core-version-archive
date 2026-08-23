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

from database_deep_map import (  # noqa: E402
    REGISTRY_FILES,
    archive_database_deep_map,
    audit_database_deep_map,
    fingerprint,
    prepare_database_deep_map_storage,
    start_database_deep_map,
)
from database_storage import (  # noqa: E402
    audit_database_storage,
    build_agent_index,
    checked_files,
    HUMAN_READABLE_MARKER,
    prepare_database_storage,
    publication_asset_records,
    record_database_storage_publication,
    write_source_readme,
)


class DatabaseStorageTests(unittest.TestCase):
    @staticmethod
    def _close_execution(target: Path) -> None:
        evidence = [{
            "url": "https://example.org/synthetic-database-contract",
            "title": "Synthetic Core test contract",
            "evidence_type": "synthetic_test_fixture",
            "supports": ["storage_contract"],
            "retrieved_at": "2026-08-22T00:00:00Z",
        }]
        project = json.loads((target / "project.json").read_text(encoding="utf-8"))
        for state in project["phase_states"].values():
            state.update({
                "state": "verified_complete",
                "completion_basis": "Synthetic Core fixture.",
                "evidence": evidence,
                "blockers": [],
            })
        (target / "project.json").write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")

        units = [json.loads(line) for line in (target / "units.jsonl").read_text(encoding="utf-8").splitlines()]
        for unit in units:
            for stage in unit["stages"].values():
                stage.update({
                    "state": "not_applicable",
                    "expected_count": 0,
                    "registered_ids": [],
                    "verified_count": 0,
                    "completion_basis": "Synthetic zero denominator.",
                    "evidence": evidence,
                    "blockers": [],
                    "notes": "Core fixture",
                })
            for spine in unit["spines"].values():
                spine.update({
                    "state": "not_applicable",
                    "expected_node_count": 0,
                    "node_ids": [],
                    "verified_node_count": 0,
                    "expected_edge_count": 0,
                    "edge_ids": [],
                    "verified_edge_count": 0,
                    "root_node_ids": [],
                    "leaf_node_ids": [],
                    "topology_fingerprint": None,
                    "completion_basis": "Synthetic zero denominator.",
                    "evidence": evidence,
                    "blockers": [],
                })
        (target / "units.jsonl").write_text(
            "".join(json.dumps(item) + "\n" for item in units), encoding="utf-8"
        )

        checks = [json.loads(line) for line in (target / "checks.jsonl").read_text(encoding="utf-8").splitlines()]
        for check in checks:
            check.update({
                "state": "not_applicable",
                "completion_basis": "Synthetic Core fixture.",
                "evidence": evidence,
                "blockers": [],
                "notes": "Core fixture",
            })
        (target / "checks.jsonl").write_text(
            "".join(json.dumps(item) + "\n" for item in checks), encoding="utf-8"
        )

    def test_storage_builds_release_elements_parity_and_rejects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = {
                "schema_version": "0.1.0",
                "id": "grdr:source:synthetic-example",
                "name": "Synthetic Example Database",
                "aliases": [],
                "canonical_url": "https://example.org/synthetic-database",
                "maintainer_ids": ["grdr:institution:synthetic-fixture"],
                "source_classes": ["other"],
                "scope": {
                    "disciplines": ["multidisciplinary"],
                    "topics": ["software testing"],
                    "geographic_scope": "non_geographic",
                    "observation_units": ["synthetic-unit"],
                    "modalities": ["tabular"],
                    "temporal_coverage_note": "Synthetic test fixture only.",
                },
                "authority": {
                    "roles": ["unknown"],
                    "provenance_position": "unknown",
                    "notes": "Synthetic test fixture only.",
                },
                "access": {
                    "availability": "open",
                    "modes": ["other"],
                    "registration_required": False,
                    "machine_access": "documented",
                    "license_status": "documented_open",
                    "access_notes": "Synthetic test fixture only.",
                },
                "refresh_policy": {"review_interval_days": 365, "last_change_detected_at": None},
                "verification": {
                    "status": "verified",
                    "last_verified_at": "2026-08-22T00:00:00Z",
                    "notes": "Validated only as a synthetic Core fixture.",
                },
                "evidence": [{
                    "url": "https://example.org/synthetic-database-contract",
                    "title": "Synthetic Core test contract",
                    "publisher": "GRDR Core tests",
                    "evidence_type": "other",
                    "supports": ["identity", "scope", "structure"],
                    "retrieved_at": "2026-08-22T00:00:00Z",
                    "archived_url": None,
                }],
            }
            canonical = {filename: [] for filename in REGISTRY_FILES}
            canonical["institutions.jsonl"] = [{
                "schema_version": "0.1.0",
                "id": "grdr:institution:synthetic-fixture",
                "name": "Synthetic Fixture Maintainer",
                "aliases": [],
                "institution_type": "other",
                "jurisdiction": None,
                "primary_url": "https://example.org/synthetic-fixture",
                "verification": {
                    "status": "verified",
                    "last_verified_at": "2026-08-22T00:00:00Z",
                    "notes": "Validated only as a synthetic Core fixture.",
                },
                "evidence": [{
                    "url": "https://example.org/synthetic-database-contract",
                    "title": "Synthetic Core test contract",
                    "publisher": "GRDR Core tests",
                    "evidence_type": "other",
                    "supports": ["identity"],
                    "retrieved_at": "2026-08-22T00:00:00Z",
                    "archived_url": None,
                }],
            }]
            canonical["sources.jsonl"] = [source]
            canonical_patcher = patch("database_deep_map.canonical_collections", return_value=canonical)
            canonical_patcher.start()
            self.addCleanup(canonical_patcher.stop)
            project_dir = root / "project"
            start_database_deep_map(ROOT / "tests" / "fixtures" / "synthetic_deep_map_spec.json", project_dir)
            self._close_execution(project_dir)
            self.assertTrue(audit_database_deep_map(project_dir)["execution_ready_for_storage"])
            prepare_database_deep_map_storage(project_dir)
            archive_database_deep_map(project_dir)

            observation = root / "observations.csv"
            observation.write_text("unit,time,value\nexample,2026,1\n", encoding="utf-8")
            runtime_script = root / "synthetic_runtime.py"
            runtime_script.write_text(
                """#!/usr/bin/env python3
import json
print(json.dumps({
    \"source_id\": \"grdr:source:synthetic-example\",
    \"status\": \"ready\",
    \"variable_count\": 0,
    \"resolvable_variable_count\": 0,
    \"unresolved_variable_count\": 0,
}))
""",
                encoding="utf-8",
            )
            runtime_descriptor = root / "runtime.json"
            runtime_descriptor.write_text(json.dumps({
                "schema_version": "1.0.0",
                "protocol_version": "grdr-source-runtime/1.0",
                "source_id": "grdr:source:synthetic-example",
                "entrypoint": runtime_script.name,
                "agent_index": "grdr-agent-index.sqlite",
                "operations": ["self-test", "search", "resolve-variable", "fetch-variable"],
                "official_domains": ["example.org"],
                "notes": "Synthetic test runtime.",
            }), encoding="utf-8")
            spec = {
                "schema_version": "2.0.0",
                "source_id": "grdr:source:synthetic-example",
                "source_slug": "synthetic-example-test",
                "snapshot_id": "2026-08-22-r1",
                "core": {
                    "version": (ROOT / "VERSION").read_text().strip(),
                    "repository": "https://github.com/yangyuezh/grdr-core",
                },
                "source_repository": {
                    "github": "yangyuezh/grdr-source-synthetic-example-test",
                    "local_path": str(root / "source-repo"),
                    "visibility": "private",
                },
                "release": {
                    "tag": "synthetic-example-test-2026-08-22-r1",
                    "title": "Synthetic Core test snapshot",
                },
                "elements_root": str(root / "Elements"),
                "observation_inputs": [{"name": "main", "path": str(observation)}],
                "adapter_inputs": [],
                "runtime": {
                    "descriptor": str(runtime_descriptor),
                    "files": [str(runtime_script)],
                },
            }
            spec_path = root / "storage-spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            prepared = prepare_database_storage(project_dir, spec_path)
            self.assertEqual(prepared["status"], "ready_for_publish")
            audit = audit_database_storage(project_dir)
            self.assertEqual(audit["errors"], [])
            self.assertTrue(audit["ready_for_publish"])
            self.assertFalse(audit["storage_complete"])
            self.assertEqual(audit["observation_file_count"], 1)
            self.assertGreaterEqual(audit["release_asset_count"], 4)

            package = json.loads((project_dir / "storage_package.json").read_text(encoding="utf-8"))
            publication = {
                "schema_version": "1.0.0",
                "project_id": package["project_id"],
                "source_id": package["source_id"],
                "snapshot_id": package["snapshot_id"],
                "repository_url": "https://github.com/yangyuezh/grdr-source-synthetic-example-test",
                "release_url": "https://github.com/yangyuezh/grdr-source-synthetic-example-test/releases/tag/synthetic-example-test-2026-08-22-r1",
                "release_tag": package["release_tag"],
                "source_repository_commit": "a" * 40,
                "assets": publication_asset_records(package),
                "verified_at": "2026-08-22T00:00:00Z",
            }
            publication["publication_fingerprint"] = fingerprint(publication)
            publication_path = root / "publication.json"
            publication_path.write_text(json.dumps(publication), encoding="utf-8")
            temporary_cards = root / "core" / "registry" / "source_archives.jsonl"
            temporary_cards.parent.mkdir(parents=True)
            temporary_cards.write_text("", encoding="utf-8")
            with patch("database_storage.SOURCE_ARCHIVE_FILE", temporary_cards):
                completed = record_database_storage_publication(project_dir, publication_path)
                self.assertTrue(completed["audit"]["storage_complete"])
                self.assertTrue(audit_database_deep_map(project_dir)["completion_ready"])

            elements = Path(audit["elements_snapshot_path"])
            stored_observation = elements / "observations" / "main" / observation.name
            stored_observation.write_text("tampered\n", encoding="utf-8")
            tampered = audit_database_storage(project_dir)
            self.assertTrue(any("Elements logical file inventory" in item for item in tampered["errors"]))

    def test_storage_spec_requires_actual_observation_input(self) -> None:
        schema = json.loads((ROOT / "schemas" / "database_storage_spec.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["observation_inputs"]["minItems"], 1)

    def test_macos_filesystem_sidecars_are_not_storage_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "actual.csv").write_text("unit,value\nexample,1\n", encoding="utf-8")
            (root / "._actual.csv").write_bytes(b"appledouble")
            (root / ".DS_Store").write_bytes(b"finder")
            (root / "._observations").write_bytes(b"directory-sidecar")

            self.assertEqual([path.name for path in checked_files(root)], ["actual.csv"])

    def test_agent_index_skips_macos_staging_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            staging = project / "staging"
            staging.mkdir(parents=True)
            (project / "project.json").write_text(json.dumps({
                "id": "grdr:deep-map-project:synthetic-sidecar",
                "source_id": "grdr:source:synthetic-sidecar",
            }), encoding="utf-8")
            (staging / "._variables.jsonl").write_bytes(b"\x00\xb0appledouble")
            destination = Path(temp) / "agent.sqlite"
            build_agent_index(project, destination)
            connection = sqlite3.connect(destination)
            try:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM records").fetchone()[0], 0)
            finally:
                connection.close()

    def test_source_readme_preserves_human_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "README.md"
            path.write_text(
                "<!-- Generated by GRDR Storage -->\nold\n\n"
                + HUMAN_READABLE_MARKER
                + "\n\n## Curated details\nKeep this.\n",
                encoding="utf-8",
            )
            write_source_readme(path, "<!-- Generated by GRDR Storage -->\nnew\n")
            value = path.read_text(encoding="utf-8")
            self.assertIn("new", value)
            self.assertNotIn("old", value)
            self.assertIn("## Curated details\nKeep this.", value)


if __name__ == "__main__":
    unittest.main()
