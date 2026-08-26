from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
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
    record_database_deep_map_stage,
    stage_database_deep_map_records,
    start_database_deep_map,
)
from database_storage import (  # noqa: E402
    assess_storage_capacity,
    audit_database_storage,
    build_storage_receipt,
    build_agent_index,
    checked_files,
    HUMAN_READABLE_MARKER,
    prepare_database_storage,
    publication_asset_records,
    record_database_storage_publication,
    run_source_runtime_invocation_acceptance,
    run_source_runtime_online_test,
    sha256_file,
    write_source_readme,
)


class DatabaseStorageTests(unittest.TestCase):
    @staticmethod
    def _close_execution(target: Path, dataset_id: str | None = None) -> None:
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
            for stage_name, stage in unit["stages"].items():
                stage.update({
                    "state": "verified_complete" if dataset_id and stage_name == "dataset" else "not_applicable",
                    "expected_count": 1 if dataset_id and stage_name == "dataset" else 0,
                    "registered_ids": [dataset_id] if dataset_id and stage_name == "dataset" else [],
                    "verified_count": 1 if dataset_id and stage_name == "dataset" else 0,
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

    def test_storage_builds_canonical_release_with_optional_local_cache(self) -> None:
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
            external_registry = root / "state" / "registry"
            external_registry.mkdir(parents=True)
            for filename in [*REGISTRY_FILES, "source_archives.jsonl"]:
                records = canonical.get(filename, [])
                (external_registry / filename).write_text(
                    "".join(json.dumps(item) + "\n" for item in records),
                    encoding="utf-8",
                )
            registry_patcher = patch("database_deep_map.REGISTRY_ROOT", external_registry)
            archive_card_patcher = patch(
                "database_storage.SOURCE_ARCHIVE_FILE",
                external_registry / "source_archives.jsonl",
            )
            registry_patcher.start()
            archive_card_patcher.start()
            self.addCleanup(registry_patcher.stop)
            self.addCleanup(archive_card_patcher.stop)
            immutable_registry_before = {
                path.name: path.read_bytes() for path in sorted((ROOT / "registry").glob("*.jsonl"))
            }
            project_dir = root / "project"
            start_database_deep_map(ROOT / "tests" / "fixtures" / "synthetic_deep_map_spec.json", project_dir)
            dataset_id = "grdr:dataset:synthetic-example-table"
            dataset = {
                "schema_version": "0.1.0",
                "id": dataset_id,
                "name": "Synthetic example table",
                "aliases": [],
                "source_native": None,
                "source_ids": [source["id"]],
                "description": "One synthetic dataset used to test external Storage state.",
                "scope": {
                    "disciplines": ["multidisciplinary"],
                    "topics": ["software testing"],
                    "population": None,
                    "observation_units": ["synthetic-unit"],
                    "geographic_coverage": None,
                    "spatial_resolution": None,
                    "temporal_coverage": "2026",
                    "temporal_resolution": "annual",
                    "modalities": ["tabular"],
                },
                "release": {
                    "current_version": "1",
                    "release_date": "2026-08-22",
                    "update_frequency": None,
                    "revision_policy_known": False,
                    "historical_vintages_available": False,
                },
                "methodology": {
                    "data_generating_processes": ["synthetic fixture"],
                    "harmonization": "none",
                    "modeled_estimates": "none",
                    "methodology_url": "https://example.org/synthetic-database-contract",
                    "limitations": ["Synthetic test data only."],
                },
                "resource_ids": [],
                "citation": {
                    "preferred_citation": None,
                    "doi": None,
                    "citation_url": "https://example.org/synthetic-database-contract",
                },
                "verification": {
                    "status": "verified",
                    "last_verified_at": "2026-08-22T00:00:00Z",
                    "notes": "Synthetic Core fixture.",
                },
                "evidence": source["evidence"],
            }
            candidate_file = root / "candidate-records.jsonl"
            candidate_file.write_text(json.dumps(dataset) + "\n", encoding="utf-8")
            stage_database_deep_map_records(project_dir, candidate_file)
            locks_before = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))["locks"]
            dataset_stage_update = root / "dataset-stage-update.json"
            dataset_stage_update.write_text(json.dumps({
                "unit_id": "grdr:deep-map-unit:synthetic-example-synthetic-table-1",
                "stage": "dataset",
                "state": "verified_complete",
                "expected_count": 1,
                "registered_ids": [dataset_id],
                "verified_count": 1,
                "completion_basis": "The staged Dataset resolves the bounded work unit without mutating the Plan lock.",
                "evidence": [{
                    "url": "https://example.org/synthetic-database-contract",
                    "title": "Synthetic Core test contract",
                    "evidence_type": "synthetic_test_fixture",
                    "supports": ["dataset_identity", "plan_lock"],
                    "retrieved_at": "2026-08-22T00:00:00Z",
                }],
                "blockers": [],
                "notes": "Regression test for a newly staged Dataset whose Plan-time dataset_id was null.",
            }) + "\n", encoding="utf-8")
            record_database_deep_map_stage(project_dir, dataset_stage_update)
            locks_after = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))["locks"]
            unit_after = json.loads((project_dir / "units.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(locks_before, locks_after)
            self.assertIsNone(unit_after["dataset_id"])
            self.assertEqual(unit_after["stages"]["dataset"]["registered_ids"], [dataset_id])
            self._close_execution(project_dir, dataset_id)
            execution_audit = audit_database_deep_map(project_dir)
            self.assertTrue(execution_audit["execution_ready_for_storage"], execution_audit)
            prepare_database_deep_map_storage(project_dir)
            archive_database_deep_map(project_dir)

            observation = project_dir / "raw_observations" / "observations.csv"
            observation.parent.mkdir()
            observation.write_text("unit,time,value\nexample,2026,1\n", encoding="utf-8")
            runtime_script = root / "synthetic_runtime.py"
            runtime_script.write_text(
                """#!/usr/bin/env python3
import json, sys
if sys.argv[1] == \"self-test-online\":
    access = json.load(open(sys.argv[sys.argv.index(\"--access-manifest\") + 1]))
    print(json.dumps({
        \"schema_version\": \"1.0.0\",
        \"source_id\": \"grdr:source:synthetic-example\",
        \"snapshot_id\": access[\"snapshot_id\"],
        \"status\": \"ready\",
        \"variable_count\": 0,
        \"online_callable_variable_count\": 0,
        \"unresolved_online_variable_count\": 0,
        \"route_results\": [{
            \"route_id\": route[\"route_id\"],
            \"status\": \"ready\",
            \"access_method\": route[\"access_method\"],
            \"authority\": route[\"authority\"],
            \"tested_at\": \"2026-08-22T00:00:00Z\",
            \"evidence_basis\": \"Synthetic online route fixture.\",
        } for route in access[\"routes\"]],
        \"variable_routes\": [],
        \"tested_at\": \"2026-08-22T00:00:00Z\",
    }))
else:
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
                "schema_version": "2.0.0",
                "protocol_version": "grdr-source-runtime/2.0",
                "route_environment_protocol": "grdr-route-context/1.0",
                "source_id": "grdr:source:synthetic-example",
                "entrypoint": runtime_script.name,
                "agent_index": "grdr-agent-index.sqlite",
                "online_access_manifest": "online_access.json",
                "operations": ["self-test", "self-test-online", "search", "resolve-variable", "fetch-variable"],
                "supported_access_methods": ["official_api", "grdr_release_snapshot"],
                "official_domains": ["example.org"],
                "notes": "Synthetic test runtime.",
            }), encoding="utf-8")
            sealed_template = root / "sealed-template"
            shutil.copytree(project_dir, sealed_template)
            spec = {
                "schema_version": "4.1.0",
                "source_id": "grdr:source:synthetic-example",
                "source_slug": "synthetic-example-test",
                "snapshot_id": "2026-08-22-r1",
                "core": {
                    "version": (ROOT / "VERSION").read_text().strip(),
                    "repository": "https://github.com/example/grdr-core",
                },
                "source_repository": {
                    "github": "example/grdr-source-synthetic-example-test",
                    "local_path": str(root / "source-repo"),
                    "visibility": "private",
                },
                "release": {
                    "tag": "synthetic-example-test-2026-08-22-r1",
                    "title": "Synthetic Core test snapshot",
                },
                "observation_policy": {
                    "replication": {
                        "mode": "full_mirror",
                        "placements": ["github_release"],
                        "completeness": {
                            "claim": "complete_within_knowledge_scope",
                            "basis": "The one declared synthetic observation file exhausts the locked fixture scope.",
                            "expected_file_count": 1,
                            "expected_partition_count": None,
                        },
                        "partition_manifest": None,
                        "external_locations": [],
                    },
                    "online_access": {
                        "completion_requirement": "all_registered_variables_online_callable",
                        "official_access": {
                            "status": "callable",
                            "basis": "The synthetic official API is represented by a live-test fixture.",
                        },
                        "routes": [{
                            "route_id": "official-api",
                            "access_method": "official_api",
                            "authority": "official",
                            "uri": "https://example.org/synthetic-database/api",
                            "freshness": "current_upstream",
                            "coverage_claim": "all_registered_variables",
                            "verification": "live_runtime_test",
                        }, {
                            "route_id": "grdr-release",
                            "access_method": "grdr_release_snapshot",
                            "authority": "grdr",
                            "uri": "https://github.com/example/grdr-source-synthetic-example-test/releases/tag/synthetic-example-test-2026-08-22-r1",
                            "freshness": "frozen_snapshot",
                            "coverage_claim": "all_registered_variables",
                            "verification": "staged_release_snapshot_test",
                        }],
                    },
                    "cache": {
                        "mode": "disabled",
                        "research_project_snapshots": False,
                        "root": None,
                    },
                },
                "observation_inputs": [{"name": "main", "path": str(observation)}],
                "raw_observation_exclusions": [],
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
            self.assertEqual(package["schema_version"], "4.1.0")
            self.assertEqual(package["snapshot_profile"]["observation_replication"]["mode"], "full_mirror")
            self.assertEqual(package["snapshot_profile"]["online_access"]["status"], "callable_complete")
            self.assertEqual(
                package["snapshot_profile"]["online_access"]["route_policies"],
                {
                    "latest": ["official_online", "github_release_snapshot", "local_snapshot_cache"],
                    "reproducible": ["github_release_snapshot", "local_snapshot_cache"],
                    "offline": ["local_snapshot_cache"],
                },
            )
            self.assertEqual(package["snapshot_profile"]["knowledge_scope"]["scope_fingerprint"], locks_after["scope_fingerprint"])
            self.assertEqual(package["duplicate_content_hash_count"], 0)
            self.assertFalse(any(
                item["path"].endswith("raw_observations/observations.csv")
                for item in package["logical_files"]
                if item["component"] == "knowledge"
            ))
            publication = {
                "schema_version": "2.0.0",
                "project_id": package["project_id"],
                "source_id": package["source_id"],
                "snapshot_id": package["snapshot_id"],
                "repository_url": "https://github.com/example/grdr-source-synthetic-example-test",
                "release_url": "https://github.com/example/grdr-source-synthetic-example-test/releases/tag/synthetic-example-test-2026-08-22-r1",
                "release_tag": package["release_tag"],
                "source_repository_commit": "a" * 40,
                "assets": publication_asset_records(package),
                "verified_at": "2026-08-22T00:00:00Z",
            }
            publication["publication_fingerprint"] = fingerprint(publication)
            publication_path = root / "publication.json"
            publication_path.write_text(json.dumps(publication), encoding="utf-8")
            project_value = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            receipt = build_storage_receipt(
                project_value, package, publication, "2026-08-22T00:01:00Z"
            )
            receipt_path = root / "receipt.json"
            receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            with patch(
                "database_storage.verify_github_publication",
                side_effect=ValueError("remote receipt verification failed"),
            ):
                with self.assertRaisesRegex(ValueError, "remote receipt verification failed"):
                    record_database_storage_publication(project_dir, publication_path, receipt_path)
            self.assertFalse((project_dir / "storage_receipt.json").exists())
            self.assertFalse((project_dir / "storage_publication.json").exists())
            self.assertEqual((external_registry / "source_archives.jsonl").read_text(), "")

            def verified_publication(package_value, publication_value, candidate_receipt_path):
                verification = {
                    "schema_version": "1.0.0",
                    "project_id": package_value["project_id"],
                    "source_id": package_value["source_id"],
                    "snapshot_id": package_value["snapshot_id"],
                    "repository_url": publication_value["repository_url"],
                    "release_url": publication_value["release_url"],
                    "release_tag": publication_value["release_tag"],
                    "source_repository_commit": publication_value["source_repository_commit"],
                    "assets": publication_value["assets"],
                    "receipt_asset": {
                        "name": "storage_receipt.json",
                        "sha256": sha256_file(candidate_receipt_path),
                        "size_bytes": candidate_receipt_path.stat().st_size,
                    },
                    "verified_at": "2026-08-22T00:02:00Z",
                }
                verification["verification_fingerprint"] = fingerprint(verification)
                return verification

            with patch(
                "database_storage.verify_github_publication",
                side_effect=verified_publication,
            ):
                completed = record_database_storage_publication(
                    project_dir, publication_path, receipt_path
                )
            self.assertTrue(completed["audit"]["storage_complete"])
            self.assertTrue(audit_database_deep_map(project_dir)["completion_ready"])
            self.assertEqual(
                immutable_registry_before,
                {path.name: path.read_bytes() for path in sorted((ROOT / "registry").glob("*.jsonl"))},
            )

            partition_project = root / "project-partitioned"
            shutil.copytree(sealed_template, partition_project)
            partition_observation = partition_project / "raw_observations" / "observations.csv"
            partition_manifest = root / "partition-manifest.json"
            partition_manifest.write_text(
                json.dumps({
                    "schema_version": "1.0.0",
                    "source_id": "grdr:source:synthetic-example",
                    "snapshot_id": "2026-08-22-r2",
                    "partition_count": 1,
                    "file_count": 1,
                    "partitions": [{
                        "name": "main",
                        "boundary": {
                            "description": "The complete synthetic fixture partition.",
                            "selectors": {"unit": ["example"], "year": [2026]},
                        },
                        "files": [{
                            "relative_path": "observations.csv",
                            "sha256": sha256_file(partition_observation),
                            "size_bytes": partition_observation.stat().st_size,
                        }],
                    }],
                }),
                encoding="utf-8",
            )
            partition_spec = json.loads(json.dumps(spec))
            partition_spec.update({
                "schema_version": "4.0.0",
                "snapshot_id": "2026-08-22-r2",
                "source_slug": "synthetic-example-partitioned",
                "elements_root": str(root / "Elements"),
            })
            partition_spec["source_repository"].update({
                "github": "example/grdr-source-synthetic-example-partitioned",
                "local_path": str(root / "source-repo-partitioned"),
            })
            partition_spec["release"].update({
                "tag": "synthetic-example-test-2026-08-22-r2",
                "title": "Synthetic partitioned snapshot",
            })
            partition_spec["observation_policy"] = {
                "replication": {
                    "mode": "partitioned_mirror",
                    "placements": ["elements"],
                    "completeness": {
                        "claim": "complete_declared_partition_set",
                        "basis": "The partition manifest declares the one locally mirrored test partition.",
                        "expected_file_count": 1,
                        "expected_partition_count": 1,
                    },
                    "partition_manifest": str(partition_manifest),
                    "external_locations": [],
                },
                "online_access": {
                    "completion_requirement": "all_registered_variables_online_callable",
                    "official_access": {
                        "status": "callable",
                        "basis": "The synthetic official API is represented by a live-test fixture.",
                    },
                    "routes": [spec["observation_policy"]["online_access"]["routes"][0]],
                },
                "cache": {
                    "mode": "on_demand",
                    "research_project_snapshots": True,
                    "root": "research_project",
                },
            }
            partition_spec["observation_inputs"] = [{
                "name": "main",
                "path": str(partition_observation),
            }]
            partition_spec_path = root / "partition-storage-spec.json"
            partition_spec_path.write_text(json.dumps(partition_spec), encoding="utf-8")
            partitioned = prepare_database_storage(partition_project, partition_spec_path)
            self.assertEqual(partitioned["audit"]["errors"], [])
            partition_package = partitioned["package"]
            self.assertEqual(partition_package["observation_file_count"], 1)
            self.assertEqual(
                [item["component"] for item in partition_package["release_assets"]],
                ["knowledge", "agent"],
            )
            self.assertTrue(
                Path(partition_package["elements_snapshot_path"], "observations").is_dir()
            )
            self.assertEqual(
                partition_package["snapshot_profile"]["online_access"]["route_policies"],
                {
                    "latest": ["official_online", "elements_mirror"],
                    "reproducible": ["elements_mirror"],
                    "offline": ["elements_mirror"],
                },
            )

            no_mirror_project = root / "project-no-mirror"
            shutil.copytree(sealed_template, no_mirror_project)
            shutil.rmtree(no_mirror_project / "raw_observations")
            no_mirror_spec = json.loads(json.dumps(spec))
            no_mirror_spec.update({
                "schema_version": "4.1.0",
                "snapshot_id": "2026-08-22-r3",
                "source_slug": "synthetic-example-no-mirror",
            })
            no_mirror_spec.pop("elements_root", None)
            no_mirror_spec["source_repository"].update({
                "github": "example/grdr-source-synthetic-example-no-mirror",
                "local_path": str(root / "source-repo-no-mirror"),
            })
            no_mirror_spec["release"].update({
                "tag": "synthetic-example-test-2026-08-22-r3",
                "title": "Synthetic no-mirror snapshot",
            })
            no_mirror_spec["observation_policy"] = {
                "replication": {
                    "mode": "no_mirror",
                    "placements": [],
                    "completeness": {
                        "claim": "observations_not_replicated",
                        "basis": "Observations remain online while the complete knowledge and call paths are stored.",
                        "expected_file_count": None,
                        "expected_partition_count": None,
                    },
                    "partition_manifest": None,
                    "external_locations": [],
                },
                "online_access": {
                    "completion_requirement": "all_registered_variables_online_callable",
                    "official_access": {
                        "status": "callable",
                        "basis": "The synthetic official API is represented by a live-test fixture.",
                    },
                    "routes": [{
                        **spec["observation_policy"]["online_access"]["routes"][0],
                        "freshness": "version_pinned",
                    }],
                },
                "cache": {
                    "mode": "on_demand",
                    "research_project_snapshots": True,
                    "root": "research_project",
                },
            }
            no_mirror_spec["observation_inputs"] = []
            no_mirror_spec_path = root / "no-mirror-storage-spec.json"
            no_mirror_spec_path.write_text(json.dumps(no_mirror_spec), encoding="utf-8")
            no_mirror = prepare_database_storage(no_mirror_project, no_mirror_spec_path)
            self.assertEqual(no_mirror["audit"]["errors"], [])
            no_mirror_package = no_mirror["package"]
            self.assertEqual(no_mirror_package["observation_file_count"], 0)
            self.assertEqual(
                no_mirror_package["snapshot_profile"]["observation_replication"]["mode"],
                "no_mirror",
            )
            self.assertFalse(
                Path(no_mirror_package["local_snapshot_cache_path"], "observations").exists()
            )
            self.assertEqual(
                no_mirror_package["snapshot_profile"]["online_access"]["route_policies"],
                {
                    "latest": ["official_online"],
                    "reproducible": ["official_online"],
                    "offline": [],
                },
            )
            local_cache = Path(no_mirror_package["local_snapshot_cache_path"])
            shutil.rmtree(local_cache)
            cacheless_audit = audit_database_storage(no_mirror_project)
            self.assertEqual(cacheless_audit["errors"], [])
            self.assertTrue(any("Optional local snapshot cache" in item for item in cacheless_audit["warnings"]))

            local_cache = Path(audit["local_snapshot_cache_path"])
            stored_observation = local_cache / "observations" / "main" / observation.name
            stored_observation.write_text("tampered\n", encoding="utf-8")
            tampered = audit_database_storage(project_dir)
            self.assertTrue(any("local snapshot cache inventory" in item for item in tampered["errors"]))

    def test_storage_spec_exposes_three_observation_modes(self) -> None:
        schema = json.loads((ROOT / "schemas" / "database_storage_spec.schema.json").read_text(encoding="utf-8"))
        modes = schema["properties"]["observation_policy"]["properties"]["replication"]["properties"]["mode"]["enum"]
        self.assertEqual(modes, ["full_mirror", "partitioned_mirror", "no_mirror"])
        self.assertNotIn("minItems", schema["properties"]["observation_inputs"])
        self.assertNotIn("elements_root", schema["required"])

    def test_online_completion_rejects_an_uncovered_registered_variable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            agent = root / "agent"
            agent.mkdir()
            index = agent / "grdr-agent-index.sqlite"
            connection = sqlite3.connect(index)
            connection.execute(
                "CREATE TABLE records (id TEXT PRIMARY KEY, entity_type TEXT)"
            )
            connection.execute(
                "INSERT INTO records VALUES (?, ?)",
                ("grdr:variable:synthetic-uncovered", "variables"),
            )
            connection.commit()
            connection.close()
            access = {
                "schema_version": "1.0.0",
                "source_id": "grdr:source:synthetic-example",
                "snapshot_id": "r1",
                "status": "callable_complete",
                "completion_requirement": "all_registered_variables_online_callable",
                "official_access": {"status": "callable", "basis": "Synthetic route."},
                "routes": [{
                    "route_id": "official-api",
                    "access_method": "official_api",
                    "authority": "official",
                    "uri": "https://example.org/api",
                    "freshness": "current_upstream",
                    "coverage_claim": "all_registered_variables",
                    "verification": "live_runtime_test",
                }],
                "coverage": {"claim": "all_registered_variables", "expected_variable_count": 1},
                "route_policies": {
                    "latest": ["official_online"],
                    "reproducible": ["official_online"],
                    "offline": [],
                },
            }
            (agent / "online_access.json").write_text(json.dumps(access), encoding="utf-8")
            runtime_script = agent / "runtime.py"
            runtime_script.write_text(
                """import json
print(json.dumps({
  "schema_version": "1.0.0",
  "source_id": "grdr:source:synthetic-example",
  "snapshot_id": "r1",
  "status": "ready",
  "variable_count": 1,
  "online_callable_variable_count": 0,
  "unresolved_online_variable_count": 0,
  "route_results": [{
    "route_id": "official-api", "status": "ready", "access_method": "official_api",
    "authority": "official", "tested_at": "2026-08-22T00:00:00Z", "evidence_basis": "Synthetic."
  }],
  "variable_routes": [],
  "tested_at": "2026-08-22T00:00:00Z"
}))
""",
                encoding="utf-8",
            )
            descriptor = {
                "source_id": "grdr:source:synthetic-example",
                "entrypoint": "runtime.py",
                "agent_index": "grdr-agent-index.sqlite",
                "online_access_manifest": "online_access.json",
            }
            with self.assertRaisesRegex(ValueError, "did not cover every registered variable"):
                run_source_runtime_online_test(agent, descriptor, root)

    def test_capacity_thresholds_are_external_and_mode_independent(self) -> None:
        base_policy = {
            "replication": {
                "mode": "full_mirror",
                "placements": [],
            },
        }
        with patch.dict(os.environ, {
            "GRDR_GITHUB_OBSERVATION_MAX_BYTES": "5",
        }):
            larger_than_github = assess_storage_capacity(
                {"observation_policy": base_policy},
                [{"size_bytes": 6}],
            )
            self.assertEqual(larger_than_github["size_class"], "large")
            self.assertNotIn("elements_full_mirror_max_bytes", larger_than_github)
            github_policy = json.loads(json.dumps(base_policy))
            github_policy["replication"]["placements"] = ["github_release"]
            with self.assertRaisesRegex(ValueError, "GitHub Release observation limit"):
                assess_storage_capacity(
                    {"observation_policy": github_policy},
                    [{"size_bytes": 6}],
                )
            large = assess_storage_capacity(
                {"observation_policy": {
                    "replication": {
                        "mode": "no_mirror",
                        "placements": [],
                        "capacity_estimate": {
                            "estimated_total_bytes": 11,
                            "basis": "Synthetic upstream estimate.",
                        },
                    },
                }},
                [],
            )
            self.assertEqual(large["size_class"], "large")
            self.assertEqual(large["captured_bytes"], 0)
        with patch.dict(os.environ, {
            "GRDR_GITHUB_OBSERVATION_MAX_BYTES": "10",
        }):
            github_only = assess_storage_capacity(
                {"observation_policy": {
                    "replication": {
                        "mode": "full_mirror",
                        "placements": ["github_release"],
                    },
                }},
                [{"size_bytes": 6}],
            )
            self.assertEqual(github_only["size_class"], "small")
            self.assertIn("GitHub Release", github_only["recommendation"])

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

    def test_parameterized_runtime_acceptance_catches_core_cli_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            snapshot = Path(temp) / "snapshot"
            agent = snapshot / "agent"
            observations = snapshot / "observations"
            agent.mkdir(parents=True)
            observations.mkdir()
            variable_id = "grdr:variable:synthetic-population"
            index = agent / "grdr-agent-index.sqlite"
            connection = sqlite3.connect(index)
            connection.execute(
                "CREATE TABLE records (id TEXT PRIMARY KEY, entity_type TEXT, label TEXT, search_text TEXT, payload_json TEXT)"
            )
            connection.execute(
                "INSERT INTO records VALUES (?, 'variables', 'Population', 'Population', ?)",
                (variable_id, json.dumps({"id": variable_id, "name": "Population"})),
            )
            connection.commit()
            connection.close()
            access = {
                "schema_version": "1.0.0",
                "source_id": "grdr:source:synthetic",
                "snapshot_id": "r1",
                "status": "callable_complete",
                "completion_requirement": "all_registered_variables_online_callable",
                "official_access": {"status": "callable", "basis": "Synthetic route."},
                "routes": [{
                    "route_id": "official-api",
                    "access_method": "official_api",
                    "authority": "official",
                    "uri": "https://example.org/api",
                    "freshness": "current_upstream",
                    "coverage_claim": "all_registered_variables",
                    "verification": "live_runtime_test",
                }],
                "coverage": {"claim": "all_registered_variables", "expected_variable_count": 1},
                "route_policies": {
                    "latest": ["official_online", "local_snapshot_cache"],
                    "reproducible": ["local_snapshot_cache"],
                    "offline": ["local_snapshot_cache"],
                },
            }
            (agent / "online_access.json").write_text(json.dumps(access), encoding="utf-8")
            (agent / "online_runtime_audit.json").write_text(json.dumps({
                "variable_routes": [{"variable_id": variable_id, "route_ids": ["official-api"]}],
            }), encoding="utf-8")
            runtime_script = agent / "runtime.py"
            runtime_script.write_text(
                """import argparse, json, os
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument("operation")
parser.add_argument("--index", required=True)
parser.add_argument("--variable-id", required=True)
parser.add_argument("--country", required=True)
parser.add_argument("--start-period")
parser.add_argument("--end-period")
parser.add_argument("--timeout")
parser.add_argument("--output-dir", required=True)
args = parser.parse_args()
output = Path(args.output_dir)
raw = output / "observations.json"
raw.write_text(json.dumps([{"country": args.country, "period": args.start_period, "value": 1}]))
(output / "provenance.json").write_text(json.dumps({"route": os.environ["GRDR_OBSERVATION_ROUTE"]}))
print(json.dumps({
    "source_id": "grdr:source:synthetic",
    "variable_id": args.variable_id,
    "status": "fetched",
    "row_count": 1,
    "raw_path": str(raw),
}))
""",
                encoding="utf-8",
            )
            descriptor = {
                "protocol_version": "grdr-source-runtime/2.0",
                "source_id": "grdr:source:synthetic",
                "entrypoint": "runtime.py",
                "agent_index": "grdr-agent-index.sqlite",
                "online_access_manifest": "online_access.json",
            }
            probes = [{
                "probe_id": "population-online",
                "variable_id": variable_id,
                "route_policy": "latest",
                "parameters": {"country": "USA", "start_period": "2023", "end_period": "2024"},
                "expected": {"minimum_row_count": 1, "selected_routes": ["official_upstream"]},
            }, {
                "probe_id": "population-offline",
                "variable_id": variable_id,
                "route_policy": "offline",
                "parameters": {"country": "USA", "start_period": "2023", "end_period": "2024"},
                "expected": {"minimum_row_count": 1, "selected_routes": ["local_snapshot_cache"]},
            }]
            spec = {
                "source_id": "grdr:source:synthetic",
                "snapshot_id": "r1",
                "runtime": {"acceptance_probes": probes},
            }
            report = run_source_runtime_invocation_acceptance(
                spec,
                descriptor,
                {"variable_count": 1},
                snapshot,
            )
            self.assertEqual(report["status"], "ready")
            self.assertEqual(report["probe_count"], 2)
            self.assertEqual(
                [item["selected_route"] for item in report["probes"]],
                ["official_upstream", "local_snapshot_cache"],
            )

            runtime_script.write_text(
                runtime_script.read_text(encoding="utf-8").replace(
                    'parser.add_argument("--start-period")',
                    'parser.add_argument("--start-year")',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "population-online failed"):
                run_source_runtime_invocation_acceptance(
                    spec,
                    descriptor,
                    {"variable_count": 1},
                    snapshot,
                )


if __name__ == "__main__":
    unittest.main()
