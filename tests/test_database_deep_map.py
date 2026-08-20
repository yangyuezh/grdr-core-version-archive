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
    record_database_deep_map_check,
    record_database_deep_map_human_gate,
    record_database_deep_map_spine,
    record_database_deep_map_stage,
    resume_database_deep_map,
    start_database_deep_map,
)
from database_deep_map_planner import (  # noqa: E402
    build_database_deep_map_plan,
    build_database_deep_map_plan_from_intake,
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
        self.assertEqual(audit["progress"]["blocked_contract_checks"], 6)
        self.assertEqual(audit["progress"]["required_spines"], 108)
        self.assertEqual(audit["progress"]["closed_spines"], 0)
        self.assertEqual(audit["progress"]["required_contract_checks"], 727)
        self.assertTrue(all(
            value is True
            for key, value in audit["execution_contract"].items()
            if key != "contract_version"
        ))
        self.assertRegex(audit["execution_locks"]["plan_fingerprint"], r"^[a-f0-9]{64}$")
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

    def test_resume_is_deterministic_across_repeated_session_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "undata"
            shutil.copytree(ROOT / "deep_map_projects" / "undata", project)
            first = resume_database_deep_map(project)["next_target"]
            second = resume_database_deep_map(project)["next_target"]
            identity = lambda item: (item["target_type"], item.get("unit_id"), item.get("stage"), item.get("facet_id"))
            self.assertEqual(identity(first), identity(second))
            self.assertEqual((first["upstream_id"], first["stage"]), ("EDATA", "variable"))

    def test_execution_locks_reject_silent_scope_and_manifest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "undata"
            shutil.copytree(ROOT / "deep_map_projects" / "undata", project)
            project_record = json.loads((project / "project.json").read_text(encoding="utf-8"))
            project_record["scope"]["boundary_statement"] += " silently changed"
            (project / "project.json").write_text(json.dumps(project_record), encoding="utf-8")
            audit = audit_database_deep_map(project)
            self.assertTrue(any("scope_fingerprint" in item for item in audit["errors"]))

            shutil.rmtree(project)
            shutil.copytree(ROOT / "deep_map_projects" / "undata", project)
            units = [json.loads(line) for line in (project / "units.jsonl").read_text(encoding="utf-8").splitlines()]
            units[0]["sequence"], units[1]["sequence"] = units[1]["sequence"], units[0]["sequence"]
            (project / "units.jsonl").write_text("".join(json.dumps(item) + "\n" for item in units), encoding="utf-8")
            audit = audit_database_deep_map(project)
            self.assertTrue(any("unit_manifest_fingerprint" in item for item in audit["errors"]))

    def test_start_stage_update_rollback_and_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "world-bank"
            start = start_database_deep_map(
                ROOT / "examples" / "world_bank_deep_map_spec.json",
                target,
            )
            self.assertTrue((target / "README.md").is_file())
            self.assertTrue((target / "checks.jsonl").is_file())
            self.assertEqual(start["audit"]["diagnostic_plan"]["plan_status"], "ready")
            self.assertGreater(start["audit"]["progress"]["required_contract_checks"], 0)
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

    def test_dual_spines_are_mandatory_and_cannot_close_early(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "world-bank"
            start = start_database_deep_map(ROOT / "examples" / "world_bank_deep_map_spec.json", target)
            self.assertEqual(start["audit"]["progress"]["required_spines"], 3)
            self.assertEqual(start["audit"]["progress"]["dual_spine_percentage"], 0.0)
            resumed = resume_database_deep_map(target)
            self.assertEqual(resumed["next_target"]["stage"], "data_structure")
            self.assertTrue(all(item["target_type"] != "work_unit_spine" for item in resumed["queue_preview"]))
            unit_id = "grdr:deep-map-unit:world-bank-example-wdi"
            evidence = [{
                "url": "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures",
                "title": "API Basic Call Structures", "evidence_type": "api_documentation",
                "supports": ["structure"], "retrieved_at": "2026-08-14T00:00:00Z",
            }]
            update = {
                "unit_id": unit_id, "spine": "structural", "state": "verified_complete",
                "expected_node_count": 3,
                "node_ids": [
                    "grdr:dataset:world-development-indicators",
                    "grdr:data-structure:world-bank-indicators-api-v2",
                    "grdr:variable:wdi-sp-pop-totl",
                ],
                "verified_node_count": 0,
                "expected_edge_count": 2,
                "edge_ids": [
                    "grdr:relationship:world-development-indicators-organized-as-world-bank-indicators-api-v2",
                    "grdr:relationship:wdi-contains-population-variable",
                ],
                "verified_edge_count": 0,
                "root_node_ids": ["grdr:dataset:world-development-indicators"],
                "leaf_node_ids": ["grdr:variable:wdi-sp-pop-totl"],
                "topology_fingerprint": None,
                "completion_basis": "Intentional premature closure used to prove the hard gate.",
                "evidence": evidence, "blockers": [],
                "checkpoint": {
                    "enumeration_rule": "Three-node test fixture", "completed_native_count": 3,
                    "last_native_id": "SP.POP.TOTL", "next_native_id": None,
                    "snapshot": "2026-08-14T00:00:00Z", "cursor_checksum": None,
                },
            }
            update_path = Path(temporary) / "spine.json"
            update_path.write_text(json.dumps(update), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cannot close before mapped prerequisite stages"):
                record_database_deep_map_spine(target, update_path)
            audit = audit_database_deep_map(target)
            self.assertEqual(audit["spine_summary"]["structural"]["mapped_units"], 0)

    def test_route_check_cannot_pass_before_its_stage_is_mapped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "world-bank"
            start_database_deep_map(ROOT / "examples" / "world_bank_deep_map_spec.json", target)
            checks = [json.loads(line) for line in (target / "checks.jsonl").read_text(encoding="utf-8").splitlines()]
            check = next(item for item in checks if item["facet_id"] == "core.native_structure")
            update = {
                "check_id": check["id"], "state": "passed",
                "completion_basis": "Intentional invalid early closure for rollback testing.",
                "evidence": [{
                    "url": "https://example.org/schema", "title": "Test schema",
                    "evidence_type": "synthetic_test_fixture", "supports": ["rollback_test"],
                    "retrieved_at": "2026-08-19T00:00:00Z",
                }],
                "blockers": [], "notes": "The data_structure stage is still not_started.",
            }
            update_path = Path(temporary) / "check.json"
            update_path.write_text(json.dumps(update), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cannot close before"):
                record_database_deep_map_check(target, update_path)
            states = {
                item["id"]: item["state"]
                for item in [json.loads(line) for line in (target / "checks.jsonl").read_text(encoding="utf-8").splitlines()]
            }
            self.assertEqual(states[check["id"]], "not_started")

    def test_database_human_gates_require_named_human_and_resolve_plan(self) -> None:
        intake = json.loads((ROOT / "examples" / "intakes" / "clinical_federated.json").read_text(encoding="utf-8"))
        intake["work_unit_strategy"]["expected_count"] = 1
        plan = build_database_deep_map_plan_from_intake(intake)
        spec = json.loads((ROOT / "examples" / "world_bank_deep_map_spec.json").read_text(encoding="utf-8"))
        spec.pop("diagnostic_intake")
        spec["diagnostic_plan"] = plan
        spec["scope"].update({
            "mode": "bounded_partition", "boundary_type": "federated_query",
            "boundary_statement": plan["scope"]["boundary_statement"],
            "expected_work_unit_count": 1,
        })
        spec["units"][0]["route_modules"] = [
            "table_schema", "clinical_interoperability", "restricted_access",
            "federated_identity", "derived_provenance",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            spec_path = Path(temporary) / "clinical.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            target = Path(temporary) / "clinical"
            result = start_database_deep_map(spec_path, target)
            self.assertEqual(result["audit"]["diagnostic_plan"]["plan_status"], "ready_with_gates")
            with self.assertRaisesRegex(ValueError, "requires reviewer and notes"):
                record_database_deep_map_human_gate(target, "access_authorization", "approved", "", "")
            record_database_deep_map_human_gate(target, "access_authorization", "approved", "Human Reviewer", "Approved for the documented secure aggregate workflow.")
            approved = record_database_deep_map_human_gate(target, "privacy_ethics_and_sovereignty", "approved", "Human Reviewer", "Approved within the documented privacy and ethics boundary.")
            self.assertEqual(approved["audit"]["diagnostic_plan"]["plan_status"], "ready")

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

    def test_needs_evidence_plan_cannot_start_execution(self) -> None:
        plan = build_database_deep_map_plan(ROOT / "examples" / "intakes" / "unknown_legacy.json")
        self.assertEqual(plan["plan_status"], "needs_evidence")
        spec = json.loads((ROOT / "examples" / "world_bank_deep_map_spec.json").read_text(encoding="utf-8"))
        spec.pop("diagnostic_intake")
        spec["diagnostic_plan"] = plan
        spec["scope"].update({
            "mode": "representative_chain", "boundary_type": "other",
            "expected_work_unit_count": None,
        })
        with tempfile.TemporaryDirectory() as temporary:
            spec_path = Path(temporary) / "needs-evidence.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not executable"):
                start_database_deep_map(spec_path, Path(temporary) / "project")


if __name__ == "__main__":
    unittest.main()
