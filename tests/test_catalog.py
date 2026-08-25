from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_empty_core_catalog_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_catalog.py"), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("**0** 个数据库", (ROOT / "catalog" / "README.md").read_text(encoding="utf-8"))
        source_pages = list((ROOT / "catalog" / "sources").glob("*/README.md"))
        self.assertEqual(source_pages, [])


if __name__ == "__main__":
    unittest.main()
