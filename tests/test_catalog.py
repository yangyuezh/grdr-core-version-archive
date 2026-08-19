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
            "### 第4层：数据库内部结构（DataStructure）",
            "### 第5层：数据元素与研究变量",
            "### 第6层：理论构念（Construct）",
            "## 访问方式与资源（旁路信息，不占内容层级）",
        ]
        for source in sources:
            slug = source["id"].rsplit(":", 1)[-1]
            page = ROOT / "catalog" / "sources" / slug / "README.md"
            self.assertTrue(page.is_file(), source["id"])
            text = page.read_text(encoding="utf-8")
            self.assertTrue(all(heading in text for heading in headings), source["id"])
            self.assertIn("| 当前拆解阶段 |", text, source["id"])
            self.assertIn("| 已声明拆解范围 |", text, source["id"])
            self.assertIn("## 持久化数据库深度映射工程", text, source["id"])

    def test_undata_human_page_exposes_catalog_and_multidimensional_depth(self) -> None:
        page = ROOT / "catalog" / "sources" / "undata" / "README.md"
        text = page.read_text(encoding="utf-8")
        self.assertIn("36 datamarts", text)
        self.assertIn("#### Energy Statistics Database", text)
        self.assertIn("UNdata Energy Statistics SDMX cube", text)
        self.assertIn("#### 5A 数据结构元素", text)
        self.assertIn("Energy transaction (`TRANSACTION`)", text)
        self.assertIn("Total energy supply (`GA`)", text)
        self.assertIn("19.44%", text)
        self.assertIn("0.93%", text)


if __name__ == "__main__":
    unittest.main()
