from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(name: str) -> list[dict]:
    return [
        json.loads(line)
        for line in (ROOT / "registry" / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_adapter_module():
    path = ROOT / "adapters" / "undata_sdmx.py"
    spec = importlib.util.spec_from_file_location("undata_sdmx", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UNdataRegistryTests(unittest.TestCase):
    def test_official_catalog_snapshot_has_36_unique_datamarts(self) -> None:
        records = [item for item in load_jsonl("datasets.jsonl") if "grdr:source:undata" in item["source_ids"]]
        self.assertEqual(len(records), 36)
        catalog_ids = {item["source_native"]["catalog_id"] for item in records}
        self.assertEqual(len(catalog_ids), 36)
        self.assertIn("EDATA", catalog_ids)
        self.assertIn("GHG", catalog_ids)

    def test_profile_declares_the_dated_exhaustive_metadata_boundary(self) -> None:
        profile = next(item for item in load_jsonl("source_profiles.jsonl") if item["source_id"] == "grdr:source:undata")
        self.assertEqual(profile["inventory_claim"], "exhaustive_snapshot")
        self.assertEqual(profile["layer_claims"]["dataset"], "scope_complete")
        self.assertEqual(profile["layer_claims"]["data_structure"], "scope_complete")
        self.assertEqual(profile["access_claim"], "scope_complete")
        self.assertEqual(profile["layer_claims"]["variable"], "scope_complete")
        self.assertEqual(profile["layer_5_details"]["registered_data_element_count"], 194)
        self.assertEqual(profile["layer_5_details"]["registered_variable_count"], 9334)
        self.assertEqual(profile["enumeration"]["upstream_item_count"], 36)
        self.assertIn("six catalog glossaries", profile["scope_statement"])

    def test_deep_profiles_cover_energy_and_ghg_structures(self) -> None:
        structures = load_jsonl("data_structures.jsonl")
        elements = load_jsonl("data_elements.jsonl")
        variables = load_jsonl("variables.jsonl")
        source_structures = [item for item in structures if item["source_id"] == "grdr:source:undata"]
        self.assertEqual(len(source_structures), 38)
        self.assertEqual(len([item for item in source_structures if "2026-08-21" in item["id"]]), 36)
        self.assertEqual(len([item for item in elements if "undata-energy" in item["id"] and "2026-08-21" not in item["id"]]), 10)
        self.assertEqual(len([item for item in elements if "undata-ghg" in item["id"] and "2026-08-21" not in item["id"]]), 6)
        self.assertEqual(len([item for item in variables if "undata-energy" in item["id"] and "2026-08-21" not in item["id"]]), 6)
        self.assertEqual(len([item for item in variables if "undata-ghg" in item["id"] and "2026-08-21" not in item["id"]]), 7)
        self.assertEqual(len([item for item in elements if "2026-08-21" in item["id"]]), 194)
        self.assertEqual(len([item for item in variables if "2026-08-21" in item["id"]]), 9334)

    def test_sdmx_parser_preserves_components_and_codelist_reference(self) -> None:
        adapter = load_adapter_module()
        payload = b'''<?xml version="1.0"?>
        <message:Structure xmlns:message="urn:sdmx:org.sdmx.infomodel.message:2.1"
          xmlns:structure="urn:sdmx:org.sdmx.infomodel.structure:2.1"
          xmlns:common="urn:sdmx:org.sdmx.infomodel.common:2.1">
          <message:Structures><structure:DataStructures>
            <structure:DataStructure agencyID="TEST" id="DSD_TEST" version="1.0">
              <common:Name>Test structure</common:Name>
              <structure:DataStructureComponents>
                <structure:DimensionList>
                  <structure:Dimension id="REF_AREA" position="1">
                    <structure:LocalRepresentation><structure:Enumeration>
                      <common:Ref agencyID="TEST" id="CL_AREA" version="1.0" class="Codelist" />
                    </structure:Enumeration></structure:LocalRepresentation>
                  </structure:Dimension>
                </structure:DimensionList>
                <structure:MeasureList><structure:PrimaryMeasure id="OBS_VALUE" /></structure:MeasureList>
              </structure:DataStructureComponents>
            </structure:DataStructure>
          </structure:DataStructures></message:Structures>
        </message:Structure>'''
        parsed = adapter.parse_datastructure(payload)
        self.assertEqual(parsed["id"], "DSD_TEST")
        self.assertEqual([item["id"] for item in parsed["components"]], ["REF_AREA", "OBS_VALUE"])
        self.assertEqual(parsed["components"][0]["enumeration"]["id"], "CL_AREA")


if __name__ == "__main__":
    unittest.main()
