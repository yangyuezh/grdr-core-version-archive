from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "grdr.py"


def run_cli(*args: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class CoreCliTests(unittest.TestCase):
    def test_version_and_empty_registry(self) -> None:
        stats = run_cli("stats")
        self.assertEqual(stats["registry_version"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual(stats["counts"]["sources"], 0)
        self.assertEqual(stats["counts"]["datasets"], 0)
        self.assertEqual(stats["counts"]["variables"], 0)

    def test_route_contracts_and_source_archive_index(self) -> None:
        routes = run_cli("list-database-route-modules")
        self.assertEqual(len(routes["route_modules"]), 29)
        archives = run_cli("list-source-archives")
        expected = [
            json.loads(line)
            for line in (ROOT / "registry" / "source_archives.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(archives["result_count"], len(expected))
        self.assertEqual(archives["results"], expected)

    def test_release_metadata(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_release.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


if __name__ == "__main__":
    unittest.main()
