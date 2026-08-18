from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "grdr.py"
SPEC = ROOT / "examples" / "population_energy_income_industry_co2_project.json"


def run_cli(*arguments: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(CLI), *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


class ResearchWorkflowTests(unittest.TestCase):
    def test_real_question_runs_complete_exploratory_closed_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            started = run_cli("start-research-project", str(SPEC), "--project-dir", str(project))
            self.assertEqual(started["leaf_indicators"], 5)

            initial = run_cli("research-project-status", str(project))
            self.assertEqual(initial["workflow_status"], "initialized")
            self.assertEqual(initial["human_gates"]["indicator_framework"]["status"], "pending")

            resumed = run_cli("resume-research-project", str(project))
            self.assertEqual(resumed["workflow_status"], "ready_to_match")

            matched = run_cli("match-indicators", str(project))
            self.assertEqual(matched["outcomes"], {"direct_match": 3, "not_found_registry_snapshot": 2})
            self.assertTrue(matched["exploratory"])
            self.assertFalse(matched["formal_evidence_ready"])

            expanded = run_cli("expand-from-data-gaps", str(project))
            self.assertEqual(expanded["gap_count"], 2)
            candidate_ids = {item for gap in expanded["gaps"] for item in gap["candidate_dataset_ids"]}
            self.assertIn("grdr:dataset:undata-national-accounts-estimates-of-main-aggregates", candidate_ids)

            resumed_again = run_cli("resume-research-project", str(project))
            self.assertEqual(resumed_again["current_step"], "rematching")
            rerun = run_cli("rerun-matching", str(project))
            self.assertEqual(rerun["matching_attempt"], 2)
            self.assertEqual(rerun["outcomes"]["not_found_registry_snapshot"], 2)

            final = run_cli("research-project-status", str(project))
            self.assertEqual(final["leaf_match_coverage"], {"matched": 3, "ratio": 0.6, "total": 5})
            self.assertTrue(final["exploratory_matching_complete"])
            self.assertFalse(final["formal_evidence_ready"])

    def test_human_gate_requires_and_records_explicit_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            run_cli("start-research-project", str(SPEC), "--project-dir", str(project))
            approved = run_cli(
                "approve-human-gate",
                str(project),
                "indicator_framework",
                "--reviewer",
                "fixture-human-reviewer",
                "--notes",
                "Fixture explicitly approves only this test scaffold.",
            )
            self.assertEqual(approved["status"], "approved")
            status = run_cli("research-project-status", str(project))
            gate = status["human_gates"]["indicator_framework"]
            self.assertEqual(gate["reviewer"], "fixture-human-reviewer")
            self.assertIsNotNone(gate["reviewed_at"])
            self.assertFalse(status["formal_evidence_ready"])


if __name__ == "__main__":
    unittest.main()
