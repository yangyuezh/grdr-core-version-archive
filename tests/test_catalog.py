from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HumanCatalogTests(unittest.TestCase):
    def test_generated_catalog_is_current(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_catalog.py"), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_every_source_has_a_six_layer_page(self) -> None:
        sources = [
            json.loads(line)
            for line in (ROOT / "registry" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        headings = [
            "### 第1层：发布/维护机构（Institution）",
            "### 第2层：数据库/数据源（Source）",
            "### 第3层：数据集（Dataset）",
            "### 第4层：访问资源（Resource）",
            "### 第5层：变量（Variable）",
            "### 第6层：理论构念（Construct）",
        ]
        for source in sources:
            slug = source["id"].rsplit(":", 1)[-1]
            page = ROOT / "catalog" / "sources" / slug / "README.md"
            self.assertTrue(page.is_file(), source["id"])
            text = page.read_text(encoding="utf-8")
            self.assertTrue(all(heading in text for heading in headings), source["id"])


if __name__ == "__main__":
    unittest.main()
