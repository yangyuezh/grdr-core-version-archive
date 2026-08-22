from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from database_deep_map import (  # noqa: E402
    archive_database_deep_map,
    audit_database_deep_map,
    fingerprint,
    prepare_database_deep_map_storage,
    stage_database_deep_map_records,
    start_database_deep_map,
)
from database_storage import (  # noqa: E402
    audit_database_storage,
    prepare_database_storage,
    publication_asset_records,
    record_database_storage_publication,
)


class DatabaseStorageTests(unittest.TestCase):
    @staticmethod
    def _close_execution(target: Path) -> None:
        evidence = [{
            "url": "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures",
            "title": "Synthetic Storage contract fixture",
            "evidence_type": "synthetic_test_fixture",
            "supports": ["storage_contract"],
            "retrieved_at": "2026-08-22T00:00:00Z",
        }]
        project = json.loads((target / "project.json").read_text(encoding="utf-8"))
        for state in project["phase_states"].values():
            state.update({
                "state": "verified_complete", "completion_basis": "Synthetic Storage fixture.",
                "evidence": evidence, "blockers": [],
            })
        (target / "project.json").write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")
        units = [json.loads(line) for line in (target / "units.jsonl").read_text(encoding="utf-8").splitlines()]
        for unit in units:
            for stage in unit["stages"].values():
                stage.update({
                    "state": "not_applicable", "expected_count": 0, "registered_ids": [],
                    "verified_count": 0, "completion_basis": "Synthetic zero denominator.",
                    "evidence": evidence, "blockers": [], "notes": "Storage fixture",
                })
            for spine in unit["spines"].values():
                spine.update({
                    "state": "not_applicable", "expected_node_count": 0, "node_ids": [],
                    "verified_node_count": 0, "expected_edge_count": 0, "edge_ids": [],
                    "verified_edge_count": 0, "root_node_ids": [], "leaf_node_ids": [],
                    "topology_fingerprint": None, "completion_basis": "Synthetic zero denominator.",
                    "evidence": evidence, "blockers": [],
                })
        (target / "units.jsonl").write_text("".join(json.dumps(item) + "\n" for item in units), encoding="utf-8")
        checks = [json.loads(line) for line in (target / "checks.jsonl").read_text(encoding="utf-8").splitlines()]
        for check in checks:
            check.update({
                "state": "not_applicable", "completion_basis": "Synthetic Storage fixture.",
                "evidence": evidence, "blockers": [], "notes": "Storage fixture",
            })
        (target / "checks.jsonl").write_text("".join(json.dumps(item) + "\n" for item in checks), encoding="utf-8")

    def test_storage_builds_release_elements_parity_and_rejects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project_dir = root / "project"
            start_database_deep_map(ROOT / "examples" / "world_bank_deep_map_spec.json", project_dir)
            source = next(
                json.loads(line) for line in (ROOT / "registry" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if json.loads(line)["id"] == "grdr:source:world-bank-open-data"
            )
            candidate = root / "candidate.json"
            candidate.write_text(json.dumps(source), encoding="utf-8")
            stage_database_deep_map_records(project_dir, candidate)
            self._close_execution(project_dir)
            self.assertTrue(audit_database_deep_map(project_dir)["execution_ready_for_storage"])
            prepare_database_deep_map_storage(project_dir)
            archive_database_deep_map(project_dir)

            observation = root / "observations.csv"
            observation.write_text("country,year,value\nAAA,2025,1\n", encoding="utf-8")
            spec = {
                "schema_version": "1.0.0",
                "source_id": "grdr:source:world-bank-open-data",
                "source_slug": "world-bank-open-data-test",
                "snapshot_id": "2026-08-22-r1",
                "core": {"version": (ROOT / "VERSION").read_text().strip(), "repository": "https://github.com/yangyuezh/grdr"},
                "source_repository": {"github": "yangyuezh/grdr-source-world-bank-open-data-test", "local_path": str(root / "source-repo"), "visibility": "private"},
                "release": {"tag": "world-bank-open-data-test-2026-08-22-r1", "title": "World Bank test snapshot"},
                "elements_root": str(root / "Elements"),
                "observation_inputs": [{"name": "main", "path": str(observation)}],
                "adapter_inputs": [str(ROOT / "adapters" / "world_bank_indicators.py")],
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
                "repository_url": "https://github.com/yangyuezh/grdr-source-world-bank-open-data-test",
                "release_url": "https://github.com/yangyuezh/grdr-source-world-bank-open-data-test/releases/tag/world-bank-open-data-test-2026-08-22-r1",
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


if __name__ == "__main__":
    unittest.main()
