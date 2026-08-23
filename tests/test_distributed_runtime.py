from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import distributed_runtime as runtime  # noqa: E402


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
            """
        )
        connection.execute("INSERT INTO metadata VALUES ('source_id', 'grdr:source:synthetic')")
        construct = {"id": "grdr:construct:synthetic-population", "label": "Population", "name": "Population"}
        dataset = {"id": "grdr:dataset:synthetic-main", "name": "Synthetic dataset"}
        variable = {
            "id": "grdr:variable:synthetic-population",
            "name": "POP",
            "label": "Resident population",
            "dataset_ids": [dataset["id"]],
            "construct_ids": [construct["id"]],
            "data_structure_ids": [],
            "role_candidates": ["outcome", "control"],
            "measurement": {"type": "administrative_measure"},
            "verification": {"status": "verified"},
            "join_keys": ["REF_AREA", "TIME_PERIOD"],
            "observation_unit": "country-year",
            "unit": "persons",
            "comparability": {"status": "comparable"},
        }
        for entity_type, item in (("constructs", construct), ("datasets", dataset), ("variables", variable)):
            connection.execute(
                "INSERT INTO records VALUES (?, ?, ?, ?, ?)",
                (item["id"], entity_type, item.get("label", item.get("name")), json.dumps(item), json.dumps(item)),
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


if __name__ == "__main__":
    unittest.main()
