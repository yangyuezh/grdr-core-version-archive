from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "grdr",
    "grdr-plan-database-deep-map",
    "grdr-execute-database-deep-map",
    "grdr-store-database-deep-map",
    "grdr-indicator-builder",
    "grdr-resolve-research-semantics",
)


class SkillPortabilityTests(unittest.TestCase):
    def test_configure_core_writes_a_relocatable_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pointer = Path(temporary) / "nested" / "grdr-core-root"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "configure_core.py"),
                    "--pointer",
                    str(pointer),
                ],
                cwd=Path(temporary),
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(pointer.read_text(encoding="utf-8"), str(ROOT) + "\n")

    def test_configure_core_persists_optional_snapshot_cache_and_github_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pointer = root / "codex-home" / "grdr-core-root"
            state = root / "state"
            cache = root / "snapshot-cache"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "configure_core.py"),
                    "--pointer",
                    str(pointer),
                    "--snapshot-cache-root",
                    str(cache),
                    "--github-observation-max-gib",
                    "5",
                ],
                cwd=root,
                env={**os.environ, "GRDR_STATE_ROOT": str(state)},
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            config = json.loads((state / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["schema_version"], "1.2.0")
            self.assertEqual(config["snapshot_cache_root"], str(cache.resolve()))
            self.assertEqual(
                config["storage_capacity_policy"]["github_release_observation_max_bytes"],
                5 * 1024 ** 3,
            )
            self.assertNotIn(
                "elements_full_mirror_max_bytes",
                config["storage_capacity_policy"],
            )
            self.assertLess(
                config["storage_capacity_policy"]["github_release_asset_max_bytes"],
                2 * 1024 ** 3,
            )

    def test_all_installed_skill_launchers_work_from_an_arbitrary_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            codex_home = root / "codex-home"
            installed = codex_home / "skills"
            installed.mkdir(parents=True)
            (codex_home / "grdr-core-root").write_text(str(ROOT) + "\n", encoding="utf-8")
            state = root / "state"
            caller = root / "unrelated-caller"
            caller.mkdir()
            environment = {
                **os.environ,
                "CODEX_HOME": str(codex_home),
                "GRDR_STATE_ROOT": str(state),
            }
            environment.pop("GRDR_ROOT", None)
            for name in SKILLS:
                destination = installed / name
                shutil.copytree(ROOT / "skill" / name, destination)
                result = subprocess.run(
                    [sys.executable, str(destination / "scripts" / "grdr.py"), "stats"],
                    cwd=caller,
                    env=environment,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["registry_version"], (ROOT / "VERSION").read_text().strip())
                self.assertEqual(payload["counts"]["source_archives"], 0)

    def test_state_root_inside_core_is_rejected(self) -> None:
        environment = {**os.environ, "GRDR_STATE_ROOT": str(ROOT / ".forbidden-state")}
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "grdr.py"), "stats"],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the immutable GRDR Core repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
