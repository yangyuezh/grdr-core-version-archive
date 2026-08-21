from __future__ import annotations

import gzip
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "deep_map_projects" / "undata-2026-08-21"


def jsonl(name: str) -> list[dict]:
    return [
        json.loads(line)
        for line in (ROOT / "registry" / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class UNdataDeepMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with gzip.open(PROJECT / "evidence" / "undata-metadata-snapshot.json.gz", "rt", encoding="utf-8") as handle:
            cls.snapshot = json.load(handle)

    def test_snapshot_has_complete_locked_denominators(self) -> None:
        snapshot = self.snapshot
        self.assertEqual(len(snapshot["catalog"]), 36)
        self.assertEqual(len(snapshot["glossaries"]), 6)
        self.assertEqual(len(snapshot["explorer"]), 32)
        self.assertEqual(sum(item["node_count"] for item in snapshot["explorer"].values()), 8719)
        self.assertEqual(sum(item["leaf_count"] for item in snapshot["explorer"].values()), 8259)
        self.assertEqual({key: len(value["variables"]) for key, value in snapshot["alternatives"].items()}, {
            "KI": 33,
            "MDG": 126,
            "SDGs": 860,
            "WorldStat": 56,
        })
        for item in snapshot["explorer"].values():
            filters = [variable["filter"] for variable in item["variables"]]
            self.assertEqual(len(filters), len(set(filters)))
            self.assertTrue(all(variable["paths"] for variable in item["variables"]))

    def test_canonical_registry_matches_archive_receipt(self) -> None:
        dated = "-2026-08-21-"
        self.assertEqual(sum(dated in item["id"] for item in jsonl("variables.jsonl")), 9334)
        self.assertEqual(sum(dated in item["id"] for item in jsonl("constructs.jsonl")), 9334)
        self.assertEqual(sum("-2026-08-21-" in item["id"] for item in jsonl("data_elements.jsonl")), 194)
        self.assertEqual(sum(item["id"].endswith("-2026-08-21-root") for item in jsonl("data_structures.jsonl")), 36)
        self.assertEqual(sum(item["id"].startswith("grdr:relationship:undata-") and item.get("qualifiers", {}).get("snapshot_boundary") == "2026-08-21" for item in jsonl("relationships.jsonl")), 43000)

        profile = next(item for item in jsonl("source_profiles.jsonl") if item["source_id"] == "grdr:source:undata")
        self.assertEqual(profile["scope_mode"], "exhaustive_snapshot")
        self.assertEqual(profile["inventory_claim"], "exhaustive_snapshot")
        self.assertEqual(profile["layer_5_details"]["registered_variable_count"], 9334)
        self.assertTrue(all(value == "scope_complete" for value in profile["layer_claims"].values()))

        receipt = json.loads((PROJECT / "archive_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["created_count"], 61975)
        self.assertEqual(receipt["updated_count"], 38)
        self.assertEqual(receipt["collection_counts"]["variables.jsonl"], 9334)
        self.assertRegex(receipt["receipt_fingerprint"], r"^[a-f0-9]{64}$")

    def test_human_result_states_boundary_and_full_closure(self) -> None:
        report = (PROJECT / "UNdata-DEEP-MAP-RESULT.md").read_text(encoding="utf-8")
        self.assertIn("Official datamarts: **36 / 36**", report)
        self.assertIn("Registered dated variables: **9,334**", report)
        self.assertIn("Required stages closed: **216 / 216**", report)
        self.assertIn("Required spines closed: **108 / 108**", report)
        self.assertIn("Required route checks closed: **638 / 638**", report)
        self.assertIn("Observation rows mirrored: **0**", report)
        self.assertIn("source-exposed metadata", report)


if __name__ == "__main__":
    unittest.main()
