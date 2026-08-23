from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class UNdataRuntimeArtifactTests(unittest.TestCase):
    def test_runtime_descriptor_and_full_variable_audit(self) -> None:
        descriptor = json.loads((ROOT / "runtime" / "runtime.json").read_text(encoding="utf-8"))
        audit = json.loads((ROOT / "runtime" / "runtime_audit.json").read_text(encoding="utf-8"))
        self.assertEqual(descriptor["protocol_version"], "grdr-source-runtime/1.0")
        self.assertTrue((ROOT / "runtime" / descriptor["entrypoint"]).is_file())
        self.assertEqual(audit["status"], "ready")
        self.assertEqual(audit["unresolved_variable_count"], 0)
        self.assertEqual(audit["variable_count"], audit["resolvable_variable_count"])
        self.assertEqual(sum(audit["route_counts"].values()), audit["variable_count"])


if __name__ == "__main__":
    unittest.main()
