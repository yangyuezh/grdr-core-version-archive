from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CoreIsolationTests(unittest.TestCase):
    def test_no_real_database_artifacts_or_names(self) -> None:
        forbidden = [
            "un" + "data",
            "data" + ".un.org",
            "world" + " bank",
            "world" + "-bank",
            "w" + "di",
        ]
        ignored_parts = {".git", ".venv", "__pycache__"}
        offenders: list[str] = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ignored_parts.intersection(path.parts):
                continue
            relative = path.relative_to(ROOT)
            if relative == Path("registry/source_archives.jsonl"):
                continue
            name = relative.as_posix().casefold()
            if any(token in name for token in forbidden):
                offenders.append(str(relative))
                continue
            try:
                content = path.read_text(encoding="utf-8").casefold()
            except UnicodeDecodeError:
                continue
            if any(token in content for token in forbidden):
                offenders.append(str(relative))
        self.assertEqual(offenders, [])

    def test_registry_templates_are_empty(self) -> None:
        registry_files = sorted((ROOT / "registry").glob("*.jsonl"))
        self.assertGreater(len(registry_files), 0)
        canonical_content = [path for path in registry_files if path.name != "source_archives.jsonl"]
        self.assertTrue(all(not path.read_text(encoding="utf-8").strip() for path in canonical_content))

    def test_no_database_project_or_adapter_is_committed(self) -> None:
        self.assertEqual(list((ROOT / "deep_map_projects").glob("*/project.json")), [])
        adapter_files = list((ROOT / "adapters").rglob("*")) if (ROOT / "adapters").exists() else []
        self.assertEqual([path for path in adapter_files if path.is_file()], [])


if __name__ == "__main__":
    unittest.main()
