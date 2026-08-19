from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from database_deep_map_planner import (  # noqa: E402
    audit_database_deep_map_plan,
    build_database_deep_map_plan,
    list_database_route_modules,
    load_contracts,
)


class DatabaseDeepMapPlannerTests(unittest.TestCase):
    def plan(self, name: str) -> dict:
        return build_database_deep_map_plan(ROOT / "examples" / "intakes" / name)

    def test_route_registry_is_extensible_and_unique(self) -> None:
        contracts = load_contracts()
        route_ids = [item["id"] for item in contracts["route_modules"]]
        facet_ids = [facet["id"] for item in contracts["route_modules"] for facet in item["facets"]]
        self.assertEqual(len(route_ids), 29)
        self.assertEqual(len(facet_ids), 70)
        self.assertEqual(len(route_ids), len(set(route_ids)))
        self.assertEqual(len(facet_ids), len(set(facet_ids)))
        self.assertEqual(len(list_database_route_modules()["route_modules"]), len(route_ids))

    def test_restricted_federated_clinical_plan_has_human_gates(self) -> None:
        plan = self.plan("clinical_federated.json")
        self.assertEqual(plan["plan_status"], "ready_with_gates")
        self.assertTrue({
            "core_metadata", "clinical_interoperability", "restricted_access",
            "federated_identity", "table_schema",
        }.issubset(plan["selected_route_modules"]))
        self.assertNotIn("sensor_stream", plan["selected_route_modules"])
        self.assertEqual(
            {item["gate"] for item in plan["human_gates"]},
            {"privacy_ethics_and_sovereignty", "access_authorization"},
        )
        self.assertEqual(audit_database_deep_map_plan(plan)["errors"], [])

    def test_rolling_sensor_plan_composes_specialized_routes(self) -> None:
        plan = self.plan("sensor_stream.json")
        self.assertEqual(plan["plan_status"], "ready")
        self.assertTrue({
            "sensor_stream", "geospatial", "scientific_array",
            "instrument_measurement", "api_schema",
        }.issubset(plan["selected_route_modules"]))
        self.assertNotIn("experimental_measurement", plan["selected_route_modules"])
        self.assertNotIn("sdmx_cube", plan["selected_route_modules"])
        self.assertIn("dynamic_or_nonstationary_source", plan["risk_flags"])
        self.assertEqual(plan["unresolved_critical"], [])

    def test_multimodal_research_graph_composes_semantic_routes(self) -> None:
        plan = self.plan("multimodal_research_graph.json")
        self.assertTrue({
            "knowledge_graph", "corpus_multimodal", "scholarly_communication",
            "machine_learning_asset", "software_workflow", "derived_provenance",
        }.issubset(plan["selected_route_modules"]))
        self.assertIn("multilingual_or_encoding_variation", plan["risk_flags"])

    def test_unknown_legacy_source_stays_in_preflight(self) -> None:
        plan = self.plan("unknown_legacy.json")
        self.assertEqual(plan["plan_status"], "needs_evidence")
        self.assertIn("legacy_or_proprietary", plan["selected_route_modules"])
        self.assertIn("open_world_custom", plan["selected_route_modules"])
        self.assertGreaterEqual(len(plan["unresolved_critical"]), 5)

    def test_plan_audit_rejects_removed_route_obligation(self) -> None:
        plan = self.plan("sensor_stream.json")
        broken = copy.deepcopy(plan)
        broken["required_facets"] = [
            item for item in broken["required_facets"]
            if item["id"] != "stream.window_completion"
        ]
        audit = audit_database_deep_map_plan(broken)
        self.assertFalse(audit["valid"])
        self.assertTrue(any("missing required facet" in item for item in audit["errors"]))


if __name__ == "__main__":
    unittest.main()
