from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from database_deep_map import (  # noqa: E402
    audit_database_deep_map,
    complete_database_deep_map,
    database_deep_map_status,
    record_database_deep_map_stage,
    resume_database_deep_map,
    start_database_deep_map,
)


class DatabaseDeepMapWorkflowTests(unittest.TestCase):
    def test_undata_has_fixed_36_unit_ledger_and_honest_progress(self) -> None:
        audit = audit_database_deep_map(ROOT / "deep_map_projects" / "undata")
        self.assertEqual(audit["errors"], [])
        self.assertEqual(audit["progress"]["work_units"], 36)
        self.assertEqual(audit["progress"]["expected_work_units"], 36)
        self.assertEqual(audit["progress"]["required_unit_stages"], 216)
        self.assertEqual(audit["progress"]["mapped_unit_stages"], 42)
        self.assertEqual(audit["progress"]["closed_unit_stages"], 2)
        self.assertEqual(audit["progress"]["mapping_percentage"], 19.44)
        self.assertEqual(audit["progress"]["strict_completion_percentage"], 0.93)
        self.assertFalse(audit["completion_ready"])
        self.assertEqual(audit["next_target"]["upstream_id"], "EDATA")
        self.assertEqual(audit["next_target"]["stage"], "variable")
        self.assertIn("sdmx_cube", audit["next_target"]["route_modules"])
        self.assertIn("next_native=010", audit["next_target"]["checkpoint"])

    def test_resume_selects_priority_unit_and_route(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "undata"
            shutil.copytree(ROOT / "deep_map_projects" / "undata", project)
            result = resume_database_deep_map(project)
            target = result["next_target"]
            self.assertEqual(target["upstream_id"], "EDATA")
            self.assertEqual(target["stage"], "variable")
            self.assertIn("sdmx_cube", target["route_modules"])

    def test_start_stage_update_rollback_and_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "world-bank"
            start = start_database_deep_map(
                ROOT / "examples" / "world_bank_deep_map_spec.json",
                target,
            )
            self.assertTrue((target / "README.md").is_file())
            self.assertEqual(start["audit"]["progress"]["mapping_percentage"], 16.67)
            unit_id = "grdr:deep-map-unit:world-bank-example-wdi"
            evidence = [{
                "url": "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures",
                "title": "API Basic Call Structures",
                "evidence_type": "api_documentation",
                "supports": ["structure", "expected_count"],
                "retrieved_at": "2026-08-14T00:00:00Z",
            }]
            invalid = {
                "unit_id": unit_id, "stage": "data_structure", "state": "mapped_complete",
                "expected_count": 2,
                "registered_ids": ["grdr:data-structure:world-bank-indicators-api-v2"],
                "verified_count": 0, "completion_basis": "One registered structure, but the declared count is intentionally wrong.",
                "evidence": evidence, "blockers": [], "notes": "Regression test",
            }
            invalid_path = Path(temporary) / "invalid.json"
            invalid_path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected_count=2"):
                record_database_deep_map_stage(target, invalid_path)
            after_rollback = database_deep_map_status(target)
            self.assertEqual(after_rollback["stage_summary"]["data_structure"]["state_counts"], {"not_started": 1})

            valid = {
                **invalid,
                "state": "verified_complete", "expected_count": 1, "verified_count": 1,
                "completion_basis": "The bounded example has one documented WDI API data structure.",
                "notes": "Count and canonical reference agree.",
            }
            valid_path = Path(temporary) / "valid.json"
            valid_path.write_text(json.dumps(valid), encoding="utf-8")
            updated = record_database_deep_map_stage(target, valid_path)
            self.assertEqual(updated["audit"]["progress"]["strict_completion_percentage"], 16.67)
            with self.assertRaisesRegex(ValueError, "unclosed project phases"):
                complete_database_deep_map(target)

    def test_undata_units_preserve_mixed_source_and_route_classification(self) -> None:
        units = [
            json.loads(line)
            for line in (ROOT / "deep_map_projects" / "undata" / "units.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len({item["upstream_id"] for item in units}), 36)
        self.assertTrue(all(item["origin_type"] == "secondary" for item in units))
        energy = next(item for item in units if item["upstream_id"] == "EDATA")
        self.assertIn("statistical_cube", energy["structural_archetypes"])
        self.assertEqual(energy["sequence"], 1)


if __name__ == "__main__":
    unittest.main()
