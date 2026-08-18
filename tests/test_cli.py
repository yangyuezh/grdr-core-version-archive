from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "grdr.py"


def run_cli(*arguments: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(CLI), *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


class GrdrCliTests(unittest.TestCase):
    def test_cli_reports_canonical_version(self) -> None:
        payload = run_cli("stats")
        expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(payload["registry_version"], expected)

    def test_release_metadata_check_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_release.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_stats_include_all_entity_levels(self) -> None:
        payload = run_cli("stats")
        self.assertGreaterEqual(payload["counts"]["sources"], 1)
        self.assertGreaterEqual(payload["counts"]["datasets"], 1)
        self.assertGreaterEqual(payload["counts"]["data_structures"], 1)
        self.assertGreaterEqual(payload["counts"]["data_elements"], 1)
        self.assertGreaterEqual(payload["counts"]["variables"], 1)
        self.assertEqual(payload["counts"]["source_profiles"], 2)

    def test_variable_search_uses_construct(self) -> None:
        payload = run_cli("search-variables", "--construct", "population")
        ids = {item["id"] for item in payload["results"]}
        self.assertIn("grdr:variable:wdi-sp-pop-totl", ids)

    def test_provenance_reaches_institution_construct_and_resource(self) -> None:
        payload = run_cli(
            "trace-provenance",
            "grdr:variable:wdi-sp-pop-totl",
            "--depth",
            "5",
        )
        ids = {item["id"] for item in payload["nodes"]}
        self.assertIn("grdr:institution:world-bank", ids)
        self.assertIn("grdr:construct:population-size", ids)
        self.assertIn("grdr:resource:world-bank-indicators-api", ids)

    def test_coverage_diagnosis_distinguishes_match_from_registry_gap(self) -> None:
        request = ROOT / "examples" / "population_emissions_request.json"
        payload = run_cli("diagnose-coverage", str(request))
        by_name = {
            item["requirement"]["name"]: item["status"]
            for item in payload["findings"]
        }
        self.assertEqual(
            by_name["population size"],
            "partially_verified_available",
        )
        self.assertEqual(
            by_name["territorial carbon dioxide emissions"],
            "conceptually_required_not_found",
        )

    def test_optional_access_layers_are_queryable(self) -> None:
        adapters = run_cli("list-adapters", "--status", "operational")
        storage = run_cli("list-storage", "--mode", "federated_access")
        monitors = run_cli("list-monitors", "--status", "passing")
        self.assertIn(
            "grdr:adapter:world-bank-indicators-api-v2",
            {item["id"] for item in adapters["results"]},
        )
        self.assertIn(
            "grdr:storage:wdi-federated-api",
            {item["id"] for item in storage["results"]},
        )
        self.assertIn(
            "grdr:monitor:world-bank-indicators-api-health",
            {item["id"] for item in monitors["results"]},
        )

    def test_source_depth_audit_distinguishes_source_only_and_six_layer_chain(self) -> None:
        undata = run_cli("audit-source-depth", "grdr:source:undata")["profile"]
        world_bank = run_cli(
            "audit-source-depth", "grdr:source:world-bank-open-data"
        )["profile"]
        self.assertEqual(undata["profile_stage"], "six_layer_chain_present")
        self.assertTrue(undata["variable_matching_ready"])
        self.assertFalse(undata["deep_map_scope_complete"])
        self.assertEqual(undata["data_element_count"], 16)
        self.assertEqual(undata["variable_count"], 13)
        self.assertEqual(undata["data_structure_count"], 2)
        self.assertEqual(undata["access_sidecar"]["resource_count"], 9)
        self.assertEqual(world_bank["profile_stage"], "six_layer_chain_present")
        self.assertTrue(world_bank["variable_matching_ready"])
        self.assertEqual(world_bank["catalog_completeness"], "representative_only")
        self.assertEqual(world_bank["declared_profile"]["scope_mode"], "representative_chain")
        self.assertEqual(undata["declared_profile"]["scope_mode"], "catalog_level")
        self.assertEqual(undata["catalog_completeness"], "catalog_scope_complete")
        self.assertIn("data_structure", {item["entity"] for item in undata["coverage_gaps"]})
        self.assertNotIn("dataset", {item["entity"] for item in undata["coverage_gaps"]})

    def test_all_source_depth_audit_covers_every_registered_source(self) -> None:
        payload = run_cli("audit-all-source-depth")
        source_count = len(
            [
                line
                for line in (ROOT / "registry" / "sources.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
        )
        self.assertEqual(payload["source_count"], source_count)
        self.assertEqual(payload["variable_matching_ready_sources"], 2)

    def test_deep_map_skill_wrapper_calls_canonical_audit(self) -> None:
        wrapper = ROOT / "skill" / "grdr-deep-map-database" / "scripts" / "audit_database_map.py"
        completed = subprocess.run(
            [sys.executable, str(wrapper), "grdr:source:undata"],
            cwd=ROOT.parent,
            check=True,
            capture_output=True,
            text=True,
            env={key: value for key, value in os.environ.items() if key != "GRDR_ROOT"},
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["operation"], "audit_source_depth")
        self.assertEqual(payload["profile"]["profile_stage"], "six_layer_chain_present")

    def test_data_element_is_queryable_with_linked_dataset_and_resource(self) -> None:
        payload = run_cli("get-data-element", "grdr:data-element:undata-energy-transaction")
        self.assertEqual(payload["data_element"]["source_native"]["native_id"], "TRANSACTION")
        self.assertEqual(payload["data_element"]["codelist"]["code_count"], 216)
        self.assertEqual(payload["datasets"][0]["id"], "grdr:dataset:undata-energy-statistics")
        self.assertEqual(payload["data_structures"][0]["id"], "grdr:data-structure:undata-energy-sdmx")

    def test_database_internal_structure_is_queryable(self) -> None:
        payload = run_cli("get-data-structure", "grdr:data-structure:undata-energy-sdmx")
        self.assertEqual(payload["data_structure"]["native_identity"]["object_id"], "DF_UNDATA_ENERGY / DSD_ENERGY")
        self.assertEqual(len(payload["data_elements"]), 10)
        self.assertEqual(len(payload["variables"]), 6)

    def test_undata_variables_preserve_dimension_selections(self) -> None:
        payload = run_cli("get-variable", "grdr:variable:undata-energy-ga")
        native = payload["variable"]["source_native"]
        self.assertEqual(native["measure_element_id"], "grdr:data-element:undata-energy-obs-value")
        self.assertEqual(native["dimension_selections"][0]["code"], "GA")


if __name__ == "__main__":
    unittest.main()
