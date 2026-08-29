from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import distributed_runtime as distributed  # noqa: E402
import global_runtime_index as global_index  # noqa: E402


class GlobalRuntimeIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.registry = self.root / "registry"
        self.registry.mkdir()
        self.snapshot = self.root / "sources" / "synthetic" / "snapshots" / "r1"
        agent = self.snapshot / "agent"
        receipts = self.snapshot / "receipts"
        agent.mkdir(parents=True)
        receipts.mkdir(parents=True)

        construct = {
            "id": "grdr:construct:synthetic-population",
            "name": "Resident population",
            "definition": "Number of residents.",
            "verification": {"status": "verified"},
        }
        dataset = {
            "id": "grdr:dataset:synthetic-main",
            "name": "Synthetic population dataset",
            "source_ids": ["grdr:source:synthetic"],
            "verification": {"status": "verified"},
        }
        variable = {
            "id": "grdr:variable:synthetic-population",
            "name": "POP",
            "label": "Resident population",
            "dataset_ids": [dataset["id"]],
            "construct_ids": [construct["id"]],
            "data_structure_ids": [],
            "role_candidates": ["outcome", "control"],
            "observation_unit": "country-year",
            "population": "residents",
            "unit": "persons",
            "temporal_resolution": "annual",
            "spatial_resolution": "global",
            "measurement": {"type": "administrative_measure"},
            "comparability": {"status": "comparable"},
            "join_keys": ["REF_AREA", "TIME_PERIOD"],
            "verification": {"status": "verified"},
        }
        index = agent / "grdr-agent-index.sqlite"
        connection = sqlite3.connect(index)
        connection.executescript(
            """
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE records (
              id TEXT PRIMARY KEY, entity_type TEXT, label TEXT,
              search_text TEXT, payload_json TEXT
            );
            CREATE TABLE relationships (
              id TEXT PRIMARY KEY, subject_id TEXT, predicate TEXT,
              object_id TEXT, payload_json TEXT
            );
            CREATE VIRTUAL TABLE record_search USING fts5(
              id UNINDEXED, label, search_text
            );
            """
        )
        connection.execute(
            "INSERT INTO metadata VALUES ('source_id', 'grdr:source:synthetic')"
        )
        for entity_type, record in (
            ("datasets", dataset),
            ("constructs", construct),
            ("variables", variable),
        ):
            label = record.get("label") or record.get("name")
            payload = json.dumps(record)
            connection.execute(
                "INSERT INTO records VALUES (?, ?, ?, ?, ?)",
                (record["id"], entity_type, label, payload, payload),
            )
            connection.execute(
                "INSERT INTO record_search VALUES (?, ?, ?)",
                (record["id"], label, payload),
            )
        connection.commit()
        connection.close()

        descriptor = {
            "schema_version": "2.0.0",
            "protocol_version": "grdr-source-runtime/2.0",
            "route_environment_protocol": "grdr-route-context/1.0",
            "source_id": "grdr:source:synthetic",
            "entrypoint": "synthetic_runtime.py",
            "agent_index": "grdr-agent-index.sqlite",
            "online_access_manifest": "online_access.json",
            "operations": [
                "self-test", "self-test-online", "search",
                "resolve-variable", "fetch-variable",
            ],
            "official_domains": ["example.org"],
        }
        (agent / "runtime.json").write_text(json.dumps(descriptor), encoding="utf-8")
        (agent / "runtime_audit.json").write_text(
            json.dumps(
                {
                    "source_id": "grdr:source:synthetic",
                    "status": "ready",
                    "variable_count": 1,
                    "resolvable_variable_count": 1,
                    "unresolved_variable_count": 0,
                }
            ),
            encoding="utf-8",
        )
        access = {
            "schema_version": "1.0.0",
            "source_id": "grdr:source:synthetic",
            "snapshot_id": "r1",
            "status": "callable_complete",
            "routes": [
                {
                    "route_id": "official-api",
                    "access_method": "official_api",
                    "authority": "official",
                    "uri": "https://example.org/api",
                    "freshness": "version_pinned",
                    "verification": "live_runtime_test",
                }
            ],
            "route_policies": {
                "latest": ["official_online"],
                "reproducible": ["official_online"],
                "offline": [],
            },
        }
        (agent / "online_access.json").write_text(json.dumps(access), encoding="utf-8")
        (agent / "online_runtime_audit.json").write_text(
            json.dumps(
                {
                    "source_id": "grdr:source:synthetic",
                    "snapshot_id": "r1",
                    "status": "ready",
                    "variable_count": 1,
                    "online_callable_variable_count": 1,
                    "unresolved_online_variable_count": 0,
                    "route_results": [
                        {
                            "route_id": "official-api",
                            "status": "ready",
                            "access_method": "official_api",
                            "authority": "official",
                        }
                    ],
                    "variable_routes": [
                        {
                            "variable_id": variable["id"],
                            "route_ids": ["official-api"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (agent / "synthetic_runtime.py").write_text(
            "import json\nprint(json.dumps({'status': 'ok'}))\n",
            encoding="utf-8",
        )

        logical_files = [
            {**item, "locations": ["elements"]}
            for item in distributed.snapshot_inventory(self.snapshot)
        ]
        logical_fingerprint = distributed.fingerprint(logical_files)
        manifest = {
            "schema_version": "4.0.0",
            "source_id": "grdr:source:synthetic",
            "snapshot_id": "r1",
            "logical_files": logical_files,
            "logical_content_fingerprint": logical_fingerprint,
            "snapshot_profile": {
                "observation_replication": {"mode": "no_mirror"},
                "observation_placement": {"locations": []},
                "online_access": {"status": "callable_complete"},
            },
            "external_observation_locations": [],
        }
        (receipts / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        receipt = {"logical_content_fingerprint": logical_fingerprint}
        receipt["receipt_fingerprint"] = distributed.fingerprint(receipt)
        (receipts / "storage_receipt.json").write_text(
            json.dumps(receipt), encoding="utf-8"
        )
        self.card = {
            "schema_version": "4.0.0",
            "id": "grdr:source-archive:synthetic",
            "source_id": "grdr:source:synthetic",
            "repository": "https://github.com/example/synthetic",
            "latest_snapshot": "r1",
            "release": "https://github.com/example/synthetic/releases/tag/r1",
            "manifest": "https://github.com/example/synthetic/releases/download/r1/manifest.json",
            "archive_fingerprint": logical_fingerprint,
            "core_version": "4.5.0",
            "status": "complete",
            "updated_at": "2026-08-25T00:00:00Z",
            "runtime": {
                "protocol_version": "grdr-source-runtime/2.0",
                "asset": "synthetic-agent.tar.gz",
                "entrypoint": "agent/synthetic_runtime.py",
                "agent_index": "agent/grdr-agent-index.sqlite",
                "operations": descriptor["operations"],
            },
        }
        records = {
            "datasets.jsonl": [dataset],
            "constructs.jsonl": [construct],
            "variables.jsonl": [variable],
            "source_archives.jsonl": [self.card],
        }
        for filename in global_index.CENTRAL_COLLECTIONS.values():
            values = records.get(filename, [])
            (self.registry / filename).write_text(
                "".join(json.dumps(item) + "\n" for item in values),
                encoding="utf-8",
            )
        (self.registry / "source_archives.jsonl").write_text(
            json.dumps(self.card) + "\n", encoding="utf-8"
        )
        self.index_path = self.root / "indexes" / "global.sqlite"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def update(self, **kwargs):
        return global_index.update_global_index(
            [self.card],
            self.root,
            registry_dir=self.registry,
            index_path=self.index_path,
            **kwargs,
        )

    def test_build_search_route_and_incremental_noop(self) -> None:
        built = self.update(rebuild=True)
        self.assertEqual(built["status"], "ready")
        self.assertEqual(built["source_status_counts"], {"ready": 1})
        self.assertEqual(built["variable_route_count"], 1)
        self.assertTrue(self.index_path.is_file())
        self.assertFalse(ROOT in self.index_path.parents)
        manifest = json.loads(
            self.index_path.with_name("grdr-global-index-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        schema = json.loads(
            (ROOT / "schemas" / "global_runtime_index_manifest.schema.json").read_text(
                encoding="utf-8"
            )
        )
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(manifest)

        matches = global_index.search_records(
            [self.card],
            ("variables",),
            self.root,
            construct="population",
            registry_dir=self.registry,
            index_path=self.index_path,
        )
        self.assertEqual(
            [item["id"] for item in matches],
            ["grdr:variable:synthetic-population"],
        )
        route = global_index.route_variable(
            [self.card],
            "grdr:variable:synthetic-population",
            self.root,
            registry_dir=self.registry,
            index_path=self.index_path,
        )
        self.assertEqual(route["status"], "routable")
        self.assertEqual(
            route["candidates"][0]["declared_variable_route_ids"],
            ["official-api"],
        )

        unchanged = self.update()
        self.assertFalse(unchanged["last_update_actions"]["central_rebuilt"])
        self.assertEqual(
            unchanged["last_update_actions"]["sources_unchanged"],
            ["grdr:source:synthetic"],
        )

    def test_audit_and_rebuild_are_deterministic(self) -> None:
        self.update(rebuild=True)
        first = global_index.audit_global_index(
            [self.card],
            self.root,
            registry_dir=self.registry,
            index_path=self.index_path,
        )
        self.assertEqual(first["status"], "passed", first)
        rebuilt = self.update(rebuild=True)
        self.assertEqual(rebuilt["entity_counts"]["variables"], 1)
        second = global_index.audit_global_index(
            [self.card],
            self.root,
            registry_dir=self.registry,
            index_path=self.index_path,
        )
        self.assertEqual(second["status"], "passed", second)

    def test_missing_snapshot_auto_materializes_agent_scope(self) -> None:
        backup = self.root / "snapshot-backup"
        shutil.copytree(self.snapshot, backup)
        shutil.rmtree(self.snapshot)
        with patch.object(
            distributed,
            "materialize_source_snapshot",
            side_effect=distributed.DistributedRuntimeError("offline"),
        ):
            unavailable = self.update(rebuild=True)
        self.assertEqual(unavailable["status"], "degraded", unavailable)

        def restore_agent_cache(card, root, *, scope):
            self.assertEqual(scope, "agent")
            shutil.copytree(backup, distributed.snapshot_path(card, root))
            return {"status": "materialized"}

        with patch.object(
            distributed,
            "materialize_source_snapshot",
            side_effect=restore_agent_cache,
        ) as materialize:
            recovered = self.update()

        self.assertEqual(recovered["status"], "ready", recovered)
        self.assertEqual(
            recovered["last_update_actions"]["sources_updated"],
            [{"source_id": self.card["source_id"], "status": "ready"}],
        )
        materialize.assert_called_once_with(self.card, self.root, scope="agent")


if __name__ == "__main__":
    unittest.main()
